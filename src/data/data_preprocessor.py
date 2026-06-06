"""
数据预处理模块
包含数据清洗、特征工程、重采样等通用预处理函数
"""

import pandas as pd
import numpy as np
from typing import List, Optional


def clean_population_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    清洗人口数据：处理缺失值、异常值、统一区县名称

    步骤:
        1. 删除全空行/列
        2. 统一区县名称格式（去除空格、统一简称）
        3. 填充或插值缺失值
        4. 标记异常值
    """
    df = df.copy()
    # 去除首尾空格
    df.columns = df.columns.str.strip()

    if "区县" in df.columns:
        df["区县"] = df["区县"].str.strip().str.replace(" ", "")

    # 数值列填充
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df[col].isnull().any():
            df[col] = df.groupby("区县", group_keys=False)[col].apply(
                lambda x: x.interpolate(method="linear").fillna(method="bfill").fillna(method="ffill")
            )

    return df


def clean_healthcare_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    清洗医疗数据
    """
    df = df.copy()
    if "区县" in df.columns:
        df["区县"] = df["区县"].str.strip().str.replace(" ", "")

    # 确保年份为整数
    if "年份" in df.columns:
        df["年份"] = df["年份"].astype(int)

    return df


def clean_sentiment_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    清洗评论数据：去重、过滤无效评论、标准化

    步骤:
        1. 去除重复评论
        2. 过滤过短评论（< 2字）
        3. 去除纯标点/表情评论
        4. 统一时间格式
    """
    df = df.copy()

    # 去除重复
    if "content" in df.columns:
        df = df.drop_duplicates(subset=["content"])

        # 过滤过短评论
        df = df[df["content"].str.len() >= 2]

        # 过滤纯标点/空内容（支持中文和英文）
        df = df[df["content"].str.contains(r"[\u4e00-\u9fff\w]+", regex=True)]

    # 时间格式标准化
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")

    return df.reset_index(drop=True)


def compute_aging_rate(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算各区县老龄化率
    老龄化率 = 65岁及以上人口 / 常住总人口
    """
    df = df.copy()
    df["老龄化率"] = df["65岁及以上人口"] / df["常住人口"]
    return df


def classify_aging_level(rate: float) -> str:
    """
    根据老龄化率划分等级

    阈值:
        轻度老龄化: < 18%
        中度老龄化: 18% ~ 25%
        重度老龄化: 25% ~ 30%
        深度老龄化: > 30%
    """
    if rate < 0.18:
        return "轻度老龄化"
    elif rate < 0.25:
        return "中度老龄化"
    elif rate < 0.30:
        return "重度老龄化"
    else:
        return "深度老龄化"


def region_classify(district: str) -> str:
    """
    根据区县名称划分区域类型

    分类:
        - 中心城区: 渝中区、江北区、南岸区、九龙坡区、沙坪坝区、大渡口区、
                     渝北区、巴南区、北碚区
        - 主城新区: 涪陵区、长寿区、江津区、合川区、永川区、南川区、綦江区、
                     大足区、璧山区、铜梁区、潼南区、荣昌区
        - 渝东北: 万州区、开州区、梁平区、城口县、丰都县、垫江县、忠县、
                  云阳县、奉节县、巫山县、巫溪县
        - 渝东南: 黔江区、武隆区、石柱县、秀山县、酉阳县、彭水县
    """
    central = [
        "渝中区", "江北区", "南岸区", "九龙坡区", "沙坪坝区",
        "大渡口区", "渝北区", "巴南区", "北碚区",
    ]
    new_urban = [
        "涪陵区", "长寿区", "江津区", "合川区", "永川区",
        "南川区", "綦江区", "大足区", "璧山区", "铜梁区",
        "潼南区", "荣昌区",
    ]
    northeast = [
        "万州区", "开州区", "梁平区", "城口县", "丰都县",
        "垫江县", "忠县", "云阳县", "奉节县", "巫山县", "巫溪县",
    ]
    southeast = [
        "黔江区", "武隆区", "石柱县", "秀山县", "酉阳县", "彭水县",
    ]

    if district in central:
        return "中心城区"
    elif district in new_urban:
        return "主城新区"
    elif district in northeast:
        return "渝东北"
    elif district in southeast:
        return "渝东南"
    else:
        return "其他"
