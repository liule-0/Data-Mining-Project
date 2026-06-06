"""
数据加载模块
支持从 Excel、CSV、GeoJSON 等多种格式加载原始数据
"""

import os
import json
import pandas as pd
from typing import Optional
from src.utils.config_loader import get_config

# geopandas 可选导入（用于地理数据）
try:
    import geopandas as gpd
    _HAS_GEOPANDAS = True
except ImportError:
    _HAS_GEOPANDAS = False


def _resolve_data_file(config_key: str, sub_key: str = "file") -> str:
    """
    解析数据文件路径，优先使用爬取数据，回退到模拟数据

    爬取数据命名规则: {basename}_crawled.{ext}
    """
    config = get_config()
    root = config["paths"]["root"]

    # 找原始配置中的文件路径
    sources = config["data_sources"].get(config_key, [])
    if not sources:
        return ""

    orig_path = os.path.join(root, sources[0][sub_key])
    orig_dir = os.path.dirname(orig_path)
    orig_name = os.path.basename(orig_path)
    name_parts = os.path.splitext(orig_name)
    ext = name_parts[1]

    # 检查爬取数据文件: {basename}_crawled.{ext} 或 crawled_{basename}
    crawled_variants = [
        os.path.join(orig_dir, f"{name_parts[0]}_crawled{ext}"),
    ]

    for cpath in crawled_variants:
        full_path = os.path.join(root, cpath)
        if os.path.exists(full_path) and os.path.getsize(full_path) > 100:
            print(f"  📥 使用爬取数据: {cpath}")
            return full_path
        elif os.path.exists(full_path):
            print(f"  ⚠️ 爬取数据为空，跳过: {cpath} ({os.path.getsize(full_path)} bytes)")

    # 回退到原始文件
    return orig_path


def load_population_data(year: Optional[int] = None) -> pd.DataFrame:
    """
    加载重庆市人口结构数据

    优先级:
        1. data/raw/population/cq_population_crawled.xlsx (爬取数据)
        2. data/raw/population/cq_population_2016_2024.xlsx (模拟数据)

    参数:
        year: 指定年份，若为 None 则加载所有年份

    返回:
        DataFrame: 包含区县、年份、常住人口、户籍人口、老年人口占比等
    """
    file_path = _resolve_data_file("population")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"人口数据文件未找到: {file_path}")

    df = pd.read_excel(file_path)
    if year:
        df = df[df["年份"] == year]
    return df


def load_healthcare_data(year: Optional[int] = None) -> pd.DataFrame:
    """
    加载重庆市医疗压力数据

    优先级:
        1. data/raw/healthcare/healthcare_crawled.xlsx (爬取数据)
        2. data/raw/healthcare/cq_hospitalization_2016_2024.xlsx (模拟数据)

    参数:
        year: 指定年份

    返回:
        DataFrame: 各区县住院人次、疾病分类、老年住院占比等
    """
    file_path = _resolve_data_file("healthcare")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"医疗数据文件未找到: {file_path}")

    df = pd.read_excel(file_path)
    if year:
        df = df[df["年份"] == year]
    return df


def load_sentiment_data(platform: str = "all") -> pd.DataFrame:
    """
    加载短视频平台舆情评论数据

    优先级:
        1. data/raw/sentiment/{platform}_comments_crawled.csv (爬取数据)
        2. data/raw/sentiment/{platform}_comments.csv (模拟数据)

    参数:
        platform: "douyin" | "kuaishou" | "all"

    返回:
        DataFrame: 评论内容、情感标签、点赞数、时间等
    """
    config = get_config()
    sources = config["data_sources"]["sentiment"]

    dfs = []
    for src in sources:
        if platform != "all" and platform not in src["file"]:
            continue
        file_path = os.path.join(config["paths"]["root"], src["file"])

        # 检查爬取版本
        dir_name = os.path.dirname(file_path)
        base_name = os.path.basename(file_path)
        name_parts = os.path.splitext(base_name)
        crawled_path = os.path.join(dir_name, f"{name_parts[0]}_crawled{name_parts[1]}")

        if os.path.exists(os.path.join(config["paths"]["root"], crawled_path)):
            full_crawled = os.path.join(config["paths"]["root"], crawled_path)
            if os.path.getsize(full_crawled) > 100:
                file_path = full_crawled
                print(f"  📥 使用爬取数据: {crawled_path}")
            else:
                print(f"  ⚠️ 爬取数据为空，跳过: {crawled_path} ({os.path.getsize(full_crawled)} bytes)")

        if os.path.exists(file_path):
            dfs.append(pd.read_csv(file_path, encoding="utf-8"))

    if not dfs:
        raise FileNotFoundError(f"未找到舆情数据文件 (platform={platform})")

    return pd.concat(dfs, ignore_index=True)


def load_geo_data():
    """
    加载重庆市行政区划 GeoJSON 数据

    返回:
        GeoDataFrame 或 dict: 38个区县边界及属性信息
    """
    config = get_config()
    file_path = os.path.join(
        config["paths"]["root"],
        config["data_sources"]["geo"][0]["file"],
    )

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"地理数据文件未找到: {file_path}")

    if _HAS_GEOPANDAS:
        return gpd.read_file(file_path, encoding="utf-8")
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
