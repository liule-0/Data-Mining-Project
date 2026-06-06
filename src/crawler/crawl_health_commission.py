"""
============================================================
重庆市卫生健康委员会数据爬虫
============================================================
数据来源:
  - 重庆市卫健委年度资料: http://wsjkw.cq.gov.cn/zwgk_242/fdzdgknr/tjxx/sjzl/ndzl/

爬取内容:
  1. 年度统计年鉴和主要统计数据中的关键医疗指标
  2. 全市医疗机构、床位、医护人员配置
  3. 住院人次、老年住院占比等

输出:
  - data/raw/healthcare/yearly_data_links.json   (年度数据下载链接)
  - data/raw/healthcare/healthcare_crawled.xlsx   (解析后的结构化数据)
============================================================
"""

import os
import re
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from typing import Optional, List, Dict
from urllib.parse import urljoin, urlparse

# ===================== 配置 =====================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

BASE_URL = "http://wsjkw.cq.gov.cn"
NDZL_URL = f"{BASE_URL}/zwgk_242/fdzdgknr/tjxx/sjzl/ndzl/"

# 常见慢病关键词
CHRONIC_DISEASE_KEYWORDS = [
    "脑血管病", "心力衰竭", "心绞痛", "高血压", "糖尿病",
    "慢性阻塞性肺疾病", "脑卒中", "冠心病", "恶性肿瘤",
]


# ===================== 1. 爬取年度数据页面列表 =====================


def fetch_ndzl_pages() -> List[Dict[str, str]]:
    """
    爬取卫健委「年度资料」页面，获取各年份统计年鉴/统计数据的入口页面

    返回:
        [{"title": "2024年统计年鉴", "url": "https://...", "year": "2024"}, ...]
    """
    resp = requests.get(NDZL_URL, headers=HEADERS, timeout=30)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]

        # 过滤出年鉴/统计数据链接
        if not any(kw in text for kw in ["年鉴", "统计数据", "主要统计"]):
            continue
        if href.startswith("javascript") or href == "#":
            continue

        full_url = urljoin(NDZL_URL, href)
        year_match = re.search(r"(20\d{2})", text)
        year = year_match.group(1) if year_match else ""

        results.append({
            "title": text,
            "year": year,
            "url": full_url,
        })

    return results


# ===================== 2. 提取PDF附件链接 =====================


def extract_pdf_links(page_url: str) -> List[Dict[str, str]]:
    """
    从年度数据详情页中提取PDF/Excel附件的下载链接

    卫健委页面的附件链接通过 onclick="downloadFj(...)" 实现
    """
    try:
        resp = requests.get(page_url, headers=HEADERS, timeout=30)
        resp.encoding = "utf-8"

        # 解析 downloadFj('文件名', '文件路径') 模式
        pattern = r"downloadFj\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)"
        matches = re.findall(pattern, resp.text)

        results = []
        base_path = os.path.dirname(page_url)

        for filename, filepath in matches:
            # 构建完整下载URL
            if filepath.startswith("http"):
                download_url = filepath
            elif filepath.startswith("./"):
                download_url = f"{base_path}/{filepath[2:]}"
            elif filepath.startswith("/"):
                download_url = f"{BASE_URL}{filepath}"
            else:
                download_url = f"{base_path}/{filepath}"

            results.append({
                "filename": filename,
                "url": download_url,
            })

        return results

    except Exception as e:
        print(f"  提取附件失败 {page_url}: {e}")
        return []


# ===================== 3. 下载年度数据PDF =====================


def download_pdf(
    pdf_url: str,
    save_dir: str,
    filename: Optional[str] = None,
    timeout: int = 120,
) -> Optional[str]:
    """
    下载PDF文件
    """
    os.makedirs(save_dir, exist_ok=True)

    if not filename:
        filename = pdf_url.split("/")[-1]
        if "." not in filename:
            filename += ".pdf"

    save_path = os.path.join(save_dir, filename)

    if os.path.exists(save_path):
        size_mb = os.path.getsize(save_path) / (1024 * 1024)
        print(f"  ⏭️ 已存在: {filename} ({size_mb:.1f} MB)")
        return save_path

    try:
        print(f"  ⬇️ 下载: {filename} ...")
        resp = requests.get(pdf_url, headers=HEADERS, timeout=timeout, stream=True)
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0

        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded / total * 100
                    print(f"\r  进度: {pct:.1f}%", end="", flush=True)

        print(f"\r  ✅ 完成: {filename} ({downloaded / 1024 / 1024:.1f} MB)")
        return save_path

    except Exception as e:
        print(f"  ❌ 下载失败: {e}")
        return None


# ===================== 4. 从PDF提取关键指标 =====================


def extract_health_indicators(pdf_path: str, year: int) -> Dict:
    """
    使用 pdfplumber 从PDF中提取关键医疗指标
    （住院人次、慢病数据等）
    """
    try:
        import pdfplumber
    except ImportError:
        return {}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            text_parts = []
            for page in pdf.pages[:10]:  # 读前10页
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            full_text = "\n".join(text_parts)
            data = {"年份": year}

            # 提取医疗机构数
            m = re.search(r"(?:医院|医疗卫生机构)[^\\d]*?([\\d,]+)个", full_text)
            if m:
                data["医疗机构数"] = int(m.group(1).replace(",", ""))

            # 提取床位数
            m = re.search(r"(?:床位)[^\\d]*?([\\d,]+)张", full_text)
            if m:
                data["床位数"] = int(m.group(1).replace(",", ""))

            # 提取医师数
            m = re.search(r"(?:执业[^\\d]*?医师|医生)[^\\d]*?([\\d,]+)人", full_text)
            if m:
                data["执业医师数"] = int(m.group(1).replace(",", ""))

            # 提取总诊疗人次
            m = re.search(r"总诊疗[^\\d]*?([\\d,.]+)万", full_text)
            if m:
                data["总诊疗人次(万)"] = float(m.group(1).replace(",", ""))

            # 提取入院人次
            m = re.search(r"入院[^\\d]*?([\\d,.]+)万", full_text)
            if m:
                data["入院人次(万)"] = float(m.group(1).replace(",", ""))

            # 提取病床使用率
            m = re.search(r"病床使用率[^\\d]*?([\\d.]+)%", full_text)
            if m:
                data["病床使用率(%)"] = float(m.group(1))

            # 提取出院者平均住院日
            m = re.search(r"平均住院[^\\d]*?([\\d.]+)天", full_text)
            if m:
                data["平均住院日"] = float(m.group(1))

            # 慢病相关
            for disease in CHRONIC_DISEASE_KEYWORDS:
                m = re.search(rf"{disease}[^\\d]*?([\\d,]+)", full_text)
                if m:
                    data[f"{disease}住院人次"] = int(m.group(1).replace(",", ""))

            return data

    except Exception as e:
        print(f"  ❌ PDF解析失败: {e}")
        return {}


# ===================== 5. 主控流程 =====================


def run_crawler(
    download_pdfs: bool = False,
    pdf_save_dir: str = "data/raw/healthcare/yearbook_pdf",
    output_dir: str = "data/raw/healthcare",
):
    """
    运行卫健委数据爬虫主流程

    参数:
        download_pdfs: 是否下载PDF附件
        pdf_save_dir: PDF保存目录
        output_dir: 结构化数据输出目录
    """
    from src.utils.config_loader import get_config
    root = get_config()["paths"]["root"]
    pdf_save_dir = os.path.join(root, pdf_save_dir)
    output_dir = os.path.join(root, output_dir)
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("🏥 重庆市卫健委数据爬虫")
    print("=" * 60)

    # ----- 1. 获取年度资料列表 -----
    print("\n[1/3] 获取卫健委年度资料列表...")
    ndzl_pages = fetch_ndzl_pages()
    print(f"  ✅ 找到 {len(ndzl_pages)} 个年度资料页面:")

    for p in ndzl_pages:
        print(f"     {p['year']}年: {p['title']}")

    # 保存索引
    pages_path = os.path.join(output_dir, "yearly_data_links.json")
    with open(pages_path, "w", encoding="utf-8") as f:
        json.dump(ndzl_pages, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 页面索引已保存: {pages_path}")

    # ----- 2. 提取PDF附件 -----
    print("\n[2/3] 提取PDF附件链接...")
    all_attachments = []

    for page in ndzl_pages:
        print(f"  解析: {page['title']}")
        pdfs = extract_pdf_links(page["url"])
        for pdf in pdfs:
            pdf["page_title"] = page["title"]
            pdf["year"] = page["year"]
            pdf["page_url"] = page["url"]
            all_attachments.append(pdf)
            print(f"     📎 {pdf['filename']}")

    if all_attachments:
        # 保存附件索引
        attach_path = os.path.join(output_dir, "pdf_attachments.json")
        with open(attach_path, "w", encoding="utf-8") as f:
            json.dump(all_attachments, f, ensure_ascii=False, indent=2)
        print(f"\n  ✅ 共找到 {len(all_attachments)} 个PDF附件")
        print(f"  ✅ 附件索引已保存: {attach_path}")

    # ----- 3. 下载PDF并提取数据（可选） -----
    if download_pdfs and all_attachments:
        print("\n[3/3] 下载PDF并提取关键指标...")
        indicators = []

        for att in all_attachments[:5]:  # 最多下载5个
            save_path = download_pdf(
                att["url"],
                pdf_save_dir,
                filename=att["filename"],
            )
            if save_path and save_path.endswith(".pdf"):
                data = extract_health_indicators(
                    save_path,
                    int(att["year"]) if att["year"] else 0,
                )
                if data and len(data) > 1:
                    data["来源"] = att["filename"]
                    indicators.append(data)

        if indicators:
            df = pd.DataFrame(indicators)
            excel_path = os.path.join(output_dir, "healthcare_crawled.xlsx")
            df.to_excel(excel_path, index=False, engine="openpyxl")
            print(f"\n  ✅ 结构化数据已保存: {excel_path}")
            print(df.to_string(index=False))
    else:
        print("\n[3/3] 跳过PDF下载（使用 --download-pdfs 开启）")

    print("\n" + "=" * 60)
    print("✅ 卫健委爬虫执行完毕！")
    print(f"   共发现 {len(ndzl_pages)} 个年度资料页面")
    print(f"   共发现 {len(all_attachments)} 个PDF附件")
    print("=" * 60)

    return {
        "pages": ndzl_pages,
        "attachments": all_attachments,
    }


# ===================== 命令行入口 =====================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    import argparse
    parser = argparse.ArgumentParser(description="重庆市卫健委数据爬虫")
    parser.add_argument("--download-pdfs", action="store_true",
                        help="下载PDF附件并提取数据")
    args = parser.parse_args()

    run_crawler(download_pdfs=args.download_pdfs)
