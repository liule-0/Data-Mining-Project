"""
============================================================
维度二：医疗压力演变趋势（时间序列 + 疾病谱分析）
============================================================
分析功能:
  1. 老年住院占比趋势：2016-2024 年度折线 + 年增长率
  2. 慢病住院量变化：分病种对比 + 增长倍数
  3. 疾病谱结构变迁：各慢病占比堆叠，展示谱系演变
  4. 老年住院总费用趋势（如有数据）

方法:
  - 环比年增长率 (YoY)、复合年增长率 (CAGR)
  - 疾病谱占比 = 各病种住院量 / 慢病总住院量
============================================================
"""

import pandas as pd
import numpy as np
from typing import List, Optional


# 慢病标准名称映射（兼容不同命名风格）
DISEASE_MAP = {
    "心衰": "心衰",
    "心力衰竭": "心衰",
    "高血压": "高血压",
    "糖尿病": "糖尿病",
    "慢阻肺": "慢阻肺",
    "慢性阻塞性肺疾病": "慢阻肺",
    "脑卒中": "脑卒中",
    "冠心病": "冠心病",
}

# 默认关注的慢病列表（短名）
DEFAULT_DISEASES = ["心衰", "高血压", "糖尿病", "慢阻肺", "脑卒中"]

# 配色方案
DISEASE_COLORS = {
    "心衰": "#e74c3c",
    "高血压": "#3498db",
    "糖尿病": "#f39c12",
    "慢阻肺": "#2ecc71",
    "脑卒中": "#9b59b6",
    "冠心病": "#1abc9c",
}


def _match_disease_columns(df: pd.DataFrame, diseases: List[str] = None) -> dict:
    """
    根据疾病短名匹配数据列名

    返回:
        {短名: 列名} 字典
    """
    if diseases is None:
        diseases = DEFAULT_DISEASES

    result = {}
    for short in diseases:
        # 尝试直接匹配包含关系
        for col in df.columns:
            if short in col or DISEASE_MAP.get(short, short) in col:
                # 排除非数据列
                if "住院" in col or "量" in col or "人次" in col:
                    result[short] = col
                    break
        # 如果没找到，再尝试用全名匹配
        if short not in result:
            for full_short, mapped in DISEASE_MAP.items():
                if mapped == short:
                    for col in df.columns:
                        if full_short in col and ("住院" in col or "量" in col):
                            result[short] = col
                            break
                    if short in result:
                        break
    return result


def elderly_hospitalization_yearly(df: pd.DataFrame) -> pd.DataFrame:
    """
    老年住院占比年度趋势 + 年增长率 + CAGR

    返回:
        DataFrame 包含:
            - 老年住院占比 mean/std/min/max
            - YoY(百分点): 环比增幅（百分点）
            - CAGR(基准2016): 复合年增长率
    """
    df = df.copy()
    df["老年住院占比"] = df["老年住院人次"] / df["总住院人次"]

    trend = (
        df.groupby("年份")["老年住院占比"]
        .agg(["mean", "std", "min", "max", "median"])
        .round(4)
    )

    # 逐年变化（百分点）
    trend["YoY(百分点)"] = trend["mean"].diff() * 100

    # CAGR 以 2016 为基年
    if 2016 in trend.index:
        base = trend.loc[2016, "mean"]
        for yr in sorted(trend.index):
            if yr > 2016:
                years_diff = yr - 2016
                cagr = (trend.loc[yr, "mean"] / base) ** (1 / years_diff) - 1
                trend.loc[yr, "CAGR(%)"] = cagr * 100
            else:
                trend.loc[yr, "CAGR(%)"] = 0.0

    # 总增幅
    trend["总增幅(百分点)"] = (trend["mean"] - trend.loc[2016, "mean"]) * 100

    return trend.round(2)


def chronic_disease_growth_analysis(
    df: pd.DataFrame,
    diseases: List[str] = None,
    base_year: int = 2016,
) -> pd.DataFrame:
    """
    慢病住院量增长分析

    返回:
        每病种的年度量、增长倍数、占比
    """
    col_map = _match_disease_columns(df, diseases)
    if not col_map:
        raise ValueError(f"未找到匹配的慢病列，可用列: {df.columns.tolist()}")

    short_names = list(col_map.keys())
    actual_cols = [col_map[s] for s in short_names]

    trend = df.groupby("年份")[actual_cols].sum()
    trend.columns = short_names  # 重命名为短名

    # 增长倍数（以 base_year 为基准）
    if base_year in trend.index:
        base = trend.loc[base_year]
        growth = trend.div(base).round(2)
        growth.columns = [f"{c}_增长倍数" for c in growth.columns]
        trend = pd.concat([trend, growth], axis=1)

    # 各病种占比（占慢病总和比例）
    total_disease = trend[short_names].sum(axis=1)
    for s in short_names:
        trend[f"{s}_占比"] = (trend[s] / total_disease).round(4)

    return trend


def disease_spectrum_evolution(
    df: pd.DataFrame,
    diseases: List[str] = None,
    years: List[int] = None,
) -> pd.DataFrame:
    """
    疾病谱演变分析——每一年各慢病在全部慢病中的占比

    用于堆叠面积图的数据格式
    """
    if years is None:
        years = sorted(df["年份"].unique())

    col_map = _match_disease_columns(df, diseases)
    short_names = list(col_map.keys())
    actual_cols = [col_map[s] for s in short_names]

    yearly = df.groupby("年份")[actual_cols].sum()
    yearly.columns = short_names

    # 只保留指定年份
    yearly = yearly.loc[years]

    # 计算谱占比
    total = yearly.sum(axis=1)
    spectrum = yearly.div(total, axis=0).round(4)
    spectrum.columns = [f"{c}" for c in spectrum.columns]

    return spectrum


def hospitalization_growth_rate(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    总住院人次和老年住院人次的年度增长率对比
    """
    df = df.copy()
    totals = df.groupby("年份")[["总住院人次", "老年住院人次"]].sum()

    # 年增长率
    for col in ["总住院人次", "老年住院人次"]:
        totals[f"{col}_增长率(%)"] = totals[col].pct_change() * 100

    totals["老年占比"] = totals["老年住院人次"] / totals["总住院人次"]

    return totals.round(2)


def medical_pressure_index(
    df: pd.DataFrame,
    df_pop: Optional[pd.DataFrame] = None,
    year: int = 2024,
) -> pd.DataFrame:
    """
    医疗压力综合指数（各区县）
    - 老年住院占比
    - 人均住院次数 = 总住院人次 / 常住人口
    - 老年住院集中度
    """
    from src.data.data_preprocessor import region_classify

    df = df.copy()
    df["老年住院占比"] = df["老年住院人次"] / df["总住院人次"]

    sub = df[df["年份"] == year].copy()

    if df_pop is not None:
        pop = df_pop[df_pop["年份"] == year][["区县", "常住人口"]]
        sub = sub.merge(pop, on="区县", how="left")
        sub["人均住院次数"] = sub["总住院人次"] / sub["常住人口"]
        sub["千人住院率"] = sub["总住院人次"] / sub["常住人口"] * 1000

    sub["区域"] = sub["区县"].apply(region_classify)
    return sub.sort_values("老年住院占比", ascending=False)


def full_healthcare_evolution_report(df: pd.DataFrame) -> dict:
    """
    运行所有医疗演变分析，返回汇总结果字典
    """
    results = {}

    # 1. 老年住院占比趋势 + 增长率
    results["elderly_trend"] = elderly_hospitalization_yearly(df)

    # 2. 慢病增长分析
    results["disease_growth"] = chronic_disease_growth_analysis(df)

    # 3. 疾病谱演变
    results["spectrum"] = disease_spectrum_evolution(df)

    # 4. 住院增长率对比
    results["growth_rate"] = hospitalization_growth_rate(df)

    _print_report(results)

    return results


def _print_report(results: dict):
    """打印分析报告"""
    print(f"\n{'='*60}")
    print(f"📈 维度二：医疗压力演变趋势")
    print(f"{'='*60}")

    # 老年住院占比
    trend = results["elderly_trend"]
    print(f"\n  📌 老年住院占比趋势:")
    for yr, row in trend.iterrows():
        yoy = row.get("YoY(百分点)", 0)
        yoy_str = f"（{'↑' if yoy>0 else '↓'}{abs(yoy):.1f}pp）" if not pd.isna(yoy) else ""
        print(f"     {yr}: {row['mean']:.1%}  {yoy_str}")
    print(f"     总增幅: {trend['总增幅(百分点)'].iloc[-1]:.1f}pp")
    print(f"     CAGR: {trend['CAGR(%)'].iloc[-1]:.1f}%/年")

    # 慢病增长
    disease = results["disease_growth"]
    short_names = [c for c in disease.columns if "_增长倍数" in c]
    print(f"\n  📌 慢病住院量增长倍数（以2016为基准）:")
    for c in short_names:
        final_val = disease[c].iloc[-1]
        print(f"     {c.replace('_增长倍数',''):6s}: {final_val:.2f}倍")

    # 疾病谱最近一年
    spectrum = results["spectrum"]
    latest = spectrum.iloc[-1]
    print(f"\n  📌 {spectrum.index[-1]}年疾病谱构成:")
    for disease, pct in latest.sort_values(ascending=False).items():
        bar = "█" * int(pct * 40)
        print(f"     {disease:6s}: {pct:.1%} {bar}")

    print(f"\n{'='*60}")
