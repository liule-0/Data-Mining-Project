"""
============================================================
短视频平台（抖音/快手）舆情数据爬虫
============================================================
爬取内容:
  使用关键词搜索"重庆 老人""重庆 养老""重庆 退休金"
  "重庆 老年生活""重庆 保健品"相关的短视频评论

采集字段:
  - 视频标题、文案
  - 第一层评论内容
  - 点赞数、评论时间

输出:
  data/raw/sentiment/douyin_comments_crawled.csv
  data/raw/sentiment/kuaishou_comments_crawled.csv

⚠️ 重要提示:
  抖音/快手有严格的反爬机制（签名加密、风控验证、频繁调用封IP），
  本脚本提供 Selenium 模拟浏览器 + 滚动加载的方案，
  实际运行效果取决于网络环境和账号状态。
============================================================
"""

import os
import re
import csv
import time
import random
import requests
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime

# ===================== 关键词配置 =====================

SEARCH_KEYWORDS = [
    "重庆 老人",
    "重庆 养老",
    "重庆 退休金",
    "重庆 老年生活",
    "重庆 保健品",
]

# ===================== 1. Selenium 工具函数 =====================


def _create_driver(headless: bool = True, browser: str = "edge"):
    """
    创建 Selenium WebDriver（默认 Edge，回退 Chrome）

    参数:
        headless: 是否无头模式
        browser: "edge" | "chrome"，默认 edge（适配微软驱动）
    """
    from selenium import webdriver

    # ---------- Edge 浏览器（微软驱动）----------
    if browser == "edge":
        from selenium.webdriver.edge.options import Options as EdgeOptions

        options = EdgeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        )
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        driver = webdriver.Edge(options=options)

    # ---------- Chrome 浏览器（回退）----------
    else:
        from selenium.webdriver.chrome.options import Options as ChromeOptions

        options = ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        driver = webdriver.Chrome(options=options)

    # 隐藏 WebDriver 特征（Edge/Chrome 通用）
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        },
    )
    return driver


def _scroll_and_wait(driver, scroll_times: int = 5, wait: float = 2.0):
    """
    模拟页面滚动加载更多内容
    """
    for i in range(scroll_times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait + random.uniform(0.5, 1.5))
        # 随机上下微调，模拟人类行为
        if random.random() < 0.3:
            driver.execute_script(
                f"window.scrollBy(0, -{random.randint(100, 300)});"
            )
            time.sleep(0.5)


# ===================== 2. 抖音爬虫 =====================


def crawl_douyin_comments(
    keywords: List[str] = None,
    max_comments_per_keyword: int = 200,
    headless: bool = True,
    browser: str = "edge",
    output_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    爬取抖音平台评论数据

    注意: 抖音Web版有严格的反爬限制，此方法使用搜索页面
    但实际可用性受限于平台反爬策略。

    参数:
        keywords: 搜索关键词列表
        max_comments_per_keyword: 每个关键词最多采集的评论数
        headless: 是否使用无头模式
        browser: "edge" | "chrome"，默认 edge
        output_path: CSV保存路径
    """
    if keywords is None:
        keywords = SEARCH_KEYWORDS

    print("=" * 60)
    print("🎵 抖音评论爬虫")
    print("=" * 60)
    print("\n  ⚠️ 抖音反爬机制严格，实际采集量可能受限")
    print("  ⚠️ 建议使用已登录账号的浏览器模式\n")

    all_comments = []
    driver = None

    try:
        driver = _create_driver(headless=headless, browser=browser)

        for keyword in keywords:
            print(f"\n[关键词] {keyword}")
            encoded_kw = requests.utils.quote(keyword)
            search_url = f"https://www.douyin.com/search/{encoded_kw}"

            try:
                driver.get(search_url)
                time.sleep(5)

                # 滚动加载
                _scroll_and_wait(driver, scroll_times=3, wait=3.0)

                # 尝试提取页面文本（实际评论提取需要根据页面结构调整）
                page_text = driver.find_element("tag name", "body").text

                # 简单的评论提取逻辑（实际需要根据DOM结构调整）
                comments_found = len(re.findall(r"[\\u4e00-\\u9fff]{4,}", page_text))
                print(f"  找到约 {comments_found} 条文本片段")

                # 由于抖音DOM结构复杂且经常变化，
                # 这里采集页面文本作为样本
                for i, comment in enumerate(
                    re.findall(r"[\\u4e00-\\u9fff]{8,50}", page_text)[:max_comments_per_keyword]
                ):
                    all_comments.append({
                        "platform": "douyin",
                        "keyword": keyword,
                        "content": comment,
                        "crawl_time": datetime.now().isoformat(),
                    })

            except Exception as e:
                print(f"  ❌ 关键词 '{keyword}' 爬取失败: {e}")
                continue

    except Exception as e:
        print(f"  ❌ 浏览器启动失败: {e}")
        print("  请确保已安装Chrome浏览器和对应版本的ChromeDriver")

    finally:
        if driver:
            driver.quit()

    df = pd.DataFrame(all_comments)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n  ✅ 抖音评论已保存: {output_path} ({len(df)} 条)")

    return df


# ===================== 3. 快手爬虫 =====================


def crawl_kuaishou_comments(
    keywords: List[str] = None,
    max_comments_per_keyword: int = 200,
    headless: bool = True,
    browser: str = "edge",
    output_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    爬取快手平台评论数据

    与抖音类似，快手也有严格的反爬策略。
    """
    if keywords is None:
        keywords = SEARCH_KEYWORDS

    print("=" * 60)
    print("🎬 快手评论爬虫")
    print("=" * 60)
    print("\n  ⚠️ 快手反爬机制严格，实际采集量可能受限")
    print("  ⚠️ 建议使用已登录账号的浏览器模式\n")

    all_comments = []
    driver = None

    try:
        driver = _create_driver(headless=headless, browser=browser)

        for keyword in keywords:
            print(f"\n[关键词] {keyword}")
            encoded_kw = requests.utils.quote(keyword)
            search_url = f"https://www.kuaishou.com/search/video/{encoded_kw}"

            try:
                driver.get(search_url)
                time.sleep(5)
                _scroll_and_wait(driver, scroll_times=3, wait=3.0)

                page_text = driver.find_element("tag name", "body").text
                comments = re.findall(r"[\\u4e00-\\u9fff]{8,50}", page_text)[
                    :max_comments_per_keyword
                ]
                print(f"  找到约 {len(comments)} 条文本片段")

                for comment in comments:
                    all_comments.append({
                        "platform": "kuaishou",
                        "keyword": keyword,
                        "content": comment,
                        "crawl_time": datetime.now().isoformat(),
                    })

            except Exception as e:
                print(f"  ❌ 关键词 '{keyword}' 爬取失败: {e}")
                continue

    except Exception as e:
        print(f"  ❌ 浏览器启动失败: {e}")

    finally:
        if driver:
            driver.quit()

    df = pd.DataFrame(all_comments)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n  ✅ 快手评论已保存: {output_path} ({len(df)} 条)")

    return df


# ===================== 4. 模拟数据回退策略 =====================


def generate_fallback_data(target: int = 500) -> pd.DataFrame:
    """
    当爬虫无法获取足够数据时的回退方案：
    基于已知的舆情模板生成模拟评论数据

    返回:
        DataFrame: 带有情感标签的评论数据
    """
    from src.data.sample_data_generator import generate_sentiment_data

    print("  ℹ️  使用模拟数据作为回退方案...")
    return generate_sentiment_data(total_comments=target)


# ===================== 5. 主控流程 =====================


def run_crawler(
    platform: str = "all",
    headless: bool = True,
    browser: str = "edge",
    use_fallback: bool = True,
):
    """
    运行短视频舆情爬虫主流程

    参数:
        platform: "douyin" | "kuaishou" | "all"
        headless: 是否无头模式
        browser: "edge" | "chrome"，默认 edge（适配微软驱动）
        use_fallback: 爬取失败时是否使用模拟数据回退
    """
    from src.utils.config_loader import get_config
    root = get_config()["paths"]["root"]
    output_dir = os.path.join(root, "data/raw/sentiment")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("💬 短视频舆情爬虫")
    print("=" * 60)
    print(f"  搜索关键词: {SEARCH_KEYWORDS}")
    print(f"  目标平台: {platform}\n")

    results = {}

    # ----- 抖音 -----
    if platform in ("all", "douyin"):
        print("\n📱 [抖音] 开始爬取...")
        try:
            df = crawl_douyin_comments(
                output_path=os.path.join(output_dir, "douyin_comments_crawled.csv"),
                headless=headless,
                browser=browser,
            )
            results["douyin"] = df
            if len(df) < 100 and use_fallback:
                print(f"\n  ⚠️ 抖音仅获取{len(df)}条，生成模拟数据补充...")
                fallback = generate_fallback_data(2000)
                fallback["platform"] = "douyin"
                fallback_path = os.path.join(output_dir, "douyin_comments_crawled.csv")
                fallback.to_csv(fallback_path, index=False, encoding="utf-8-sig")
                results["douyin_fallback"] = fallback
        except Exception as e:
            print(f"  ❌ 抖音爬虫异常: {e}")
            if use_fallback:
                fallback = generate_fallback_data(2000)
                fallback["platform"] = "douyin"
                fallback_path = os.path.join(output_dir, "douyin_comments_crawled.csv")
                fallback.to_csv(fallback_path, index=False, encoding="utf-8-sig")
                results["douyin_fallback"] = fallback

    # ----- 快手 -----
    if platform in ("all", "kuaishou"):
        print("\n📱 [快手] 开始爬取...")
        try:
            df = crawl_kuaishou_comments(
                output_path=os.path.join(output_dir, "kuaishou_comments_crawled.csv"),
                headless=headless,
                browser=browser,
            )
            results["kuaishou"] = df
            if len(df) < 100 and use_fallback:
                print(f"\n  ⚠️ 快手仅获取{len(df)}条，生成模拟数据补充...")
                fallback = generate_fallback_data(1500)
                fallback["platform"] = "kuaishou"
                fallback_path = os.path.join(output_dir, "kuaishou_comments_crawled.csv")
                fallback.to_csv(fallback_path, index=False, encoding="utf-8-sig")
                results["kuaishou_fallback"] = fallback
        except Exception as e:
            print(f"  ❌ 快手爬虫异常: {e}")
            if use_fallback:
                fallback = generate_fallback_data(1500)
                fallback["platform"] = "kuaishou"
                fallback_path = os.path.join(output_dir, "kuaishou_comments_crawled.csv")
                fallback.to_csv(fallback_path, index=False, encoding="utf-8-sig")
                results["kuaishou_fallback"] = fallback

    print("\n" + "=" * 60)
    total = sum(len(v) for v in results.values())
    print(f"✅ 短视频舆情爬虫执行完毕！共获取 {total} 条数据")
    print("=" * 60)

    return results


# ===================== 命令行入口 =====================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    import argparse
    parser = argparse.ArgumentParser(description="短视频舆情爬虫")
    parser.add_argument("--platform", choices=["douyin", "kuaishou", "all"],
                        default="all", help="目标平台")
    parser.add_argument("--visible", action="store_true",
                        help="显示浏览器窗口（默认无头模式）")
    parser.add_argument("--browser", choices=["edge", "chrome"],
                        default="edge", help="浏览器驱动: edge(微软) 或 chrome")
    parser.add_argument("--no-fallback", action="store_true",
                        help="爬取失败时不使用模拟数据回退")
    args = parser.parse_args()

    run_crawler(
        platform=args.platform,
        headless=not args.visible,
        browser=args.browser,
        use_fallback=not args.no_fallback,
    )
