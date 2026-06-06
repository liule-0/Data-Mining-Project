"""
医疗压力分析模块
分析老年住院趋势、疾病负担演变及医疗资源配置
"""

import pandas as pd
import numpy as np
from typing import List, Dict


def elderly_hospitalization_trend(df: pd.DataFrame) -> pd.DataFrame:
    """
    分析老年住院占比年度趋势（2016-2024）
    """
    df = df.copy()
    df["老年住院占比"] = df["老年住院人次"] / df["总住院人次"]

    trend = (
        df.groupby("年份")["老年住院占比"]
        .agg(["mean", "std", "min", "max"])
        .round(4)
    )
    return trend


def chronic_disease_trend(
    df: pd.DataFrame, diseases: List[str] = None
) -> pd.DataFrame:
    """
    分析慢病住院量变化趋势

    参数:
        diseases: 慢病列表，默认使用配置中的疾病列表
    """
    if diseases is None:
        diseases = ["心衰", "高血压", "糖尿病", "慢性阻塞性肺疾病", "脑卒中"]

    disease_cols = [c for c in df.columns if any(d in c for d in diseases)]
    if not disease_cols:
        raise ValueError("数据中未找到慢病相关列")

    trend = df.groupby("年份")[disease_cols].sum()

    # 以基年（2016）为基准计算增长倍数
    if 2016 in trend.index:
        base = trend.loc[2016]
        growth = trend.div(base).round(2)
        growth.columns = [f"{c}_增长倍数" for c in growth.columns]
        return pd.concat([trend, growth], axis=1)

    return trend


def regional_healthcare_pressure(df: pd.DataFrame) -> pd.DataFrame:
    """
    按区域统计医疗压力指标

    返回:
        DataFrame: 各区县老年住院率、人均住院费用等汇总
    """
    from src.data.data_preprocessor import region_classify

    df = df.copy()
    if "老年住院占比" not in df.columns:
        df["老年住院占比"] = df["老年住院人次"] / df["总住院人次"]

    df["区域"] = df["区县"].apply(region_classify)

    summary = df.groupby(["区域", "年份"]).agg(
        平均老年住院占比=("老年住院占比", "mean"),
        总住院人次=("总住院人次", "sum"),
        老年住院人次=("老年住院人次", "sum"),
    ).round(4)

    return summary


def disease_structure_change(df: pd.DataFrame, year1: int, year2: int) -> pd.DataFrame:
    """
    对比两个年份的疾病谱结构变化
    """
    df1 = df[df["年份"] == year1].select_dtypes(include=[np.number]).sum()
    df2 = df[df["年份"] == year2].select_dtypes(include=[np.number]).sum()

    comparison = pd.DataFrame({
        str(year1): df1,
        str(year2): df2,
        "变化量": df2 - df1,
        "变化率(%)": ((df2 - df1) / df1 * 100).round(2),
    }).dropna()

    return comparison.sort_values("变化量", ascending=False)
