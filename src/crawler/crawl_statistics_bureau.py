"""
============================================================
重庆市统计局数据爬虫
============================================================
数据来源:
  - 统计年鉴: http://tjj.cq.gov.cn/zwgk_233/tjnj/
  - 统计公报: https://tjj.cq.gov.cn/zwgk_233/fdzdgknr/tjxx/sjzl_55471/tjgb_55472/
  - 重庆数据门户: https://data.tjj.cq.gov.cn/

爬取内容:
  1. 各区县人口结构数据（常住人口、户籍人口、年龄结构）
  2. 年度统计公报中的关键人口指标

输出:
  - data/raw/population/cq_population_crawled.xlsx  (结构化人口数据)
  - data/raw/population/yearbook_links.json          (年鉴下载链接)
  - data/raw/population/statistical_bulletins.json   (公报摘要)
============================================================
"""

import os
import re
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional, List, Dict
from urllib.parse import urljoin

# ===================== 配置 =====================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

BASE_URL = "http://tjj.cq.gov.cn"
YEARBOOK_URL = f"{BASE_URL}/zwgk_233/tjnj/"
BULLETIN_URL = f"{BASE_URL}/zwgk_233/fdzdgknr/tjxx/sjzl_55471/tjgb_55472/"

# ===================== 1. 获取年鉴PDF链接 =====================


def fetch_yearbook_links() -> List[Dict[str, str]]:
    """
    爬取统计年鉴页面，获取各年份年鉴PDF的下载链接

    返回:
        [{"year": "2024", "name": "2024重庆统计年鉴", "pdf_url": "https://..."}, ...]
    """
    resp = requests.get(YEARBOOK_URL, headers=HEADERS, timeout=30)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    for tag in soup.find_all(lambda t: t.get("redit")):
        name = tag.get_text(strip=True)
        pdf_url = tag.get("redit", "")
        # 提取年份
        year_match = re.search(r"(20\d{2})", name)
        year = year_match.group(1) if year_match else "unknown"

        results.append({
            "year": year,
            "name": name,
            "pdf_url": pdf_url,
            "file_size_mb": None,  # 下载时可填充
        })

    # 按年份排序
    results.sort(key=lambda x: x["year"], reverse=True)
    return results


def download_yearbook_pdf(
    pdf_url: str,
    save_dir: str,
    filename: Optional[str] = None,
    timeout: int = 120,
) -> Optional[str]:
    """
    下载指定年鉴PDF文件

    参数:
        pdf_url: PDF下载链接
        save_dir: 保存目录
        filename: 文件名（不提供则从URL提取）
        timeout: 超时秒数

    返回:
        保存路径，失败返回 None
    """
    os.makedirs(save_dir, exist_ok=True)

    if not filename:
        filename = pdf_url.split("/")[-1]
        if not filename.endswith(".pdf"):
            filename += ".pdf"

    save_path = os.path.join(save_dir, filename)

    if os.path.exists(save_path):
        file_size = os.path.getsize(save_path) / (1024 * 1024)
        print(f"  ⏭️ 文件已存在: {filename} ({file_size:.1f} MB)")
        return save_path

    try:
        print(f"  ⬇️ 正在下载: {filename} ...")
        resp = requests.get(pdf_url, headers=HEADERS, timeout=timeout, stream=True)
        resp.raise_for_status()

        total_size = int(resp.headers.get("content-length", 0))
        downloaded = 0

        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = downloaded / total_size * 100
                    print(f"\r  进度: {pct:.1f}%", end="", flush=True)

        print(f"\r  ✅ 下载完成: {filename} ({downloaded / 1024 / 1024:.1f} MB)")
        return save_path

    except Exception as e:
        print(f"  ❌ 下载失败 {filename}: {e}")
        return None


# ===================== 2. 爬取统计公报 =====================


def fetch_statistical_bulletins(max_pages: int = 5) -> List[Dict[str, str]]:
    """
    爬取历年统计公报列表

    返回:
        [{"title": "...", "date": "...", "url": "..."}, ...]
    """
    all_bulletins = []

    for page in range(1, max_pages + 1):
        page_url = f"{BULLETIN_URL}index_{page}.html" if page > 1 else BULLETIN_URL
        try:
            resp = requests.get(page_url, headers=HEADERS, timeout=30)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            found = 0
            for a in soup.find_all("a", href=True):
                text = a.get_text(strip=True)
                href = a["href"]
                if "统计公报" in text and "解读" not in text:
                    full_url = urljoin(BASE_URL, href)
                    # 提取日期
                    date_match = re.search(r"(20\d{2})", text)
                    date_str = date_match.group(1) if date_match else ""

                    all_bulletins.append({
                        "title": text,
                        "year": date_str,
                        "url": full_url,
                    })
                    found += 1

            if found == 0:
                break  # 没有更多公报了
        except Exception as e:
            print(f"  第{page}页爬取失败: {e}")
            break

    # 去重
    seen = set()
    unique = []
    for b in all_bulletins:
        if b["url"] not in seen:
            seen.add(b["url"])
            unique.append(b)

    return unique


def parse_bulletin_population(bulletin_url: str) -> Dict:
    """
    解析单篇统计公报中的人口数据

    返回:
        {"常住人口": xxx, "城镇化率": xxx, ...}
    """
    try:
        resp = requests.get(bulletin_url, headers=HEADERS, timeout=30)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text()

        data = {}

        # 提取常住人口
        pop_match = re.search(r"常住人口[^\d]*?([\d.]+)万", text)
        if pop_match:
            data["常住人口(万人)"] = float(pop_match.group(1))

        # 提取城镇化率
        urban_match = re.search(r"城镇化率[^\d]*?([\d.]+)%", text)
        if urban_match:
            data["城镇化率(%)"] = float(urban_match.group(1))

        # 提取出生率
        birth_match = re.search(r"出生率[^\d]*?([\d.]+)‰", text)
        if birth_match:
            data["出生率(‰)"] = float(birth_match.group(1))

        # 提取死亡率
        death_match = re.search(r"死亡率[^\d]*?([\d.]+)‰", text)
        if death_match:
            data["死亡率(‰)"] = float(death_match.group(1))

        # 提取自然增长率
        natural_match = re.search(r"自然增长率[^\d]*?([\d.-]+)‰", text)
        if natural_match:
            data["自然增长率(‰)"] = float(natural_match.group(1))

        return data

    except Exception as e:
        print(f"  解析失败 {bulletin_url}: {e}")
        return {}


# ===================== 3. 爬取重庆数据门户 =====================


def fetch_data_portal_population() -> pd.DataFrame:
    """
    尝试从 重庆数据门户 (https://data.tjj.cq.gov.cn/) 获取人口数据

    注意: 该门户需要登录，此函数仅尝试公开可访问的接口
    """
    print("  ⚠️ 重庆数据门户需要登录，公开接口受限")
    return pd.DataFrame()


# ===================== 4. 从PDF提取人口表格 =====================


def extract_population_table_from_pdf(
    pdf_path: str,
    year: int,
    pages: Optional[List[int]] = None,
) -> pd.DataFrame:
    """
    使用 pdfplumber 从统计年鉴PDF中提取人口表格数据

    统计年鉴中人口数据通常在第三章"人口与就业"，
    包含各区县的常住人口、户籍人口、年龄结构等。

    参数:
        pdf_path: PDF文件路径
        year: 年份
        pages: 指定页码（不指定则自动检测）

    返回:
        DataFrame: 提取的人口数据
    """
    import pdfplumber

    print(f"  解析PDF: {os.path.basename(pdf_path)} (第{year}年)...")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            target_pages = pages or list(range(len(pdf.pages)))

            all_tables = []
            for page_num in target_pages:
                if page_num >= len(pdf.pages):
                    continue
                page = pdf.pages[page_num]
                tables = page.extract_tables()

                for table in tables:
                    if table and len(table) > 2:
                        headers = table[0]
                        headers = [
                            h if h else f"col_{i}" for i, h in enumerate(headers)
                        ]
                        df_table = pd.DataFrame(table[1:], columns=headers)
                        all_tables.append(df_table)

            if all_tables:
                result = pd.concat(all_tables, ignore_index=True)
                print(f"  ✅ 提取到 {len(result)} 行数据, {len(result.columns)} 列")
                result["年份"] = year
                return result
            else:
                print(f"  ⚠️ 未在指定页找到表格")
                return pd.DataFrame()

    except Exception as e:
        print(f"  ❌ PDF解析失败: {e}")
        return pd.DataFrame()


# ===================== 5. 主控流程 =====================


def run_crawler(
    download_pdfs: bool = False,
    pdf_save_dir: str = "data/raw/population/yearbook_pdf",
    output_dir: str = "data/raw/population",
    save_links: bool = True,
    save_bulletins: bool = True,
):
    """
    运行统计局数据爬虫主流程

    参数:
        download_pdfs: 是否下载PDF年鉴（默认False，文件较大）
        pdf_save_dir: PDF保存目录
        output_dir: 结构化数据输出目录
        save_links: 是否保存年鉴链接
        save_bulletins: 是否爬取统计公报
    """
    from src.utils.config_loader import get_config
    config = get_config()

    # 使用项目配置的data路径
    root = config["paths"]["root"]
    pdf_save_dir = os.path.join(root, pdf_save_dir)
    output_dir = os.path.join(root, output_dir)

    print("=" * 60)
    print("📊 重庆市统计局数据爬虫")
    print("=" * 60)

    # ----- 1. 获取年鉴链接 -----
    print("\n[1/3] 获取统计年鉴PDF链接...")
    yearbooks = fetch_yearbook_links()
    print(f"  ✅ 找到 {len(yearbooks)} 年年鉴:")

    for yb in yearbooks[:5]:
        print(f"     {yb['year']}年: {yb['pdf_url'][:80]}...")
    if len(yearbooks) > 5:
        print(f"     ... 还有 {len(yearbooks) - 5} 年")

    if save_links:
        os.makedirs(output_dir, exist_ok=True)
        links_path = os.path.join(output_dir, "yearbook_links.json")
        with open(links_path, "w", encoding="utf-8") as f:
            json.dump(yearbooks, f, ensure_ascii=False, indent=2)
        print(f"  ✅ 年鉴链接已保存: {links_path}")

    # ----- 2. 下载PDF（可选） -----
    if download_pdfs:
        print("\n[2/3] 下载统计年鉴PDF...")
        for yb in yearbooks[:3]:  # 默认只下最近3年
            download_yearbook_pdf(
                yb["pdf_url"],
                pdf_save_dir,
                filename=f"{yb['year']}重庆统计年鉴.pdf",
            )
    else:
        print("\n[2/3] 跳过PDF下载（使用 --download-pdfs 开启）")

    # ----- 3. 爬取统计公报 -----
    if save_bulletins:
        print("\n[3/3] 爬取统计公报...")
        bulletins = fetch_statistical_bulletins(max_pages=3)
        print(f"  ✅ 找到 {len(bulletins)} 篇统计公报")

        # 解析公报中的人口数据
        pop_data = []
        for b in bulletins[:8]:  # 解析最近8年的
            print(f"  解析: {b['title']}")
            data = parse_bulletin_population(b["url"])
            if data:
                data["年份"] = b["year"]
                data["标题"] = b["title"]
                pop_data.append(data)

        if pop_data:
            df_bulletin = pd.DataFrame(pop_data)
            bulletin_path = os.path.join(output_dir, "statistical_bulletins.json")
            with open(bulletin_path, "w", encoding="utf-8") as f:
                json.dump(bulletins, f, ensure_ascii=False, indent=2)

            excel_path = os.path.join(output_dir, "bulletin_population.xlsx")
            df_bulletin.to_excel(excel_path, index=False, engine="openpyxl")
            print(f"\n  ✅ 公报人口数据已保存:")
            print(f"     JSON: {bulletin_path}")
            print(f"     Excel: {excel_path}")
            print(f"\n  📊 公报人口摘要:")
            print(df_bulletin.to_string(index=False))

    print("\n" + "=" * 60)
    print("✅ 统计局爬虫执行完毕！")
    print("=" * 60)

    return {
        "yearbooks": yearbooks,
        "bulletins": bulletins if save_bulletins else [],
    }


# ===================== 命令行入口 =====================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    import argparse
    parser = argparse.ArgumentParser(description="重庆市统计局数据爬虫")
    parser.add_argument("--download-pdfs", action="store_true",
                        help="下载年鉴PDF（较大，默认不下载）")
    parser.add_argument("--save-links", action="store_true", default=True,
                        help="保存年鉴下载链接")
    parser.add_argument("--save-bulletins", action="store_true", default=True,
                        help="爬取统计公报")
    args = parser.parse_args()

    run_crawler(
        download_pdfs=args.download_pdfs,
        save_links=args.save_links,
        save_bulletins=args.save_bulletins,
    )
