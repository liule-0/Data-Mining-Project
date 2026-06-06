"""
人口结构分析模块
分析各区县老龄化率、人口结构变化趋势及区域差异
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


def aging_rate_trend(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算各区县老龄化率年度趋势

    返回:
        DataFrame: 区县 × 年份 的老龄化率矩阵
    """
    df = df.copy()
    df["老龄化率"] = df["65岁及以上人口"] / df["常住人口"]
    pivot = df.pivot_table(
        index="区县", columns="年份", values="老龄化率", aggfunc="mean"
    )
    return pivot.round(4)


def regional_aging_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """
    按四大区域（中心城区、主城新区、渝东北、渝东南）统计老龄化率

    返回:
        DataFrame: 各区域各年份的平均老龄化率
    """
    from src.data.data_preprocessor import region_classify

    df = df.copy()
    df["老龄率"] = df["65岁及以上人口"] / df["常住人口"]
    df["区域"] = df["区县"].apply(region_classify)

    summary = df.groupby(["区域", "年份"])["老龄率"].agg(["mean", "std", "min", "max"])
    return summary.round(4)


def aging_speed_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    分析各区县老龄化速度（2016-2024 年老龄化率增量）

    返回:
        DataFrame: 各区县老龄化增速排名
    """
    pivot = aging_rate_trend(df)

    if 2016 in pivot.columns and 2024 in pivot.columns:
        result = pd.DataFrame({
            "2016年老龄化率": pivot[2016],
            "2024年老龄化率": pivot[2024],
            "增幅(百分点)": (pivot[2024] - pivot[2016]) * 100,
            "增长率(%)": ((pivot[2024] - pivot[2016]) / pivot[2016]) * 100,
        })
        return result.sort_values("增幅(百分点)", ascending=False).round(2)

    return pd.DataFrame()


def age_structure_shift(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    分析特定年份各年龄段人口占比
    """
    age_cols = [c for c in df.columns if "岁" in c]
    df = df.copy()
    age_df = df[df["年份"] == year][["区县"] + age_cols].copy()

    if "常住人口" in df.columns:
        pop_series = df[df["年份"] == year].set_index("区县")["常住人口"]
        for col in age_cols:
            age_df[col + "_占比"] = age_df[col] / age_df["区县"].map(pop_series)

    return age_df
