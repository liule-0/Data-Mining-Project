"""
============================================================
维度一：老龄化空间分布（时空分析）
============================================================
分析功能:
  1. 一区两群（主城都市区 / 渝东北 / 渝东南）分区统计
  2. 城区 vs 远郊对比（中心城区 9 区 vs 远郊区县 29 区）
  3. 老年抚养比（城乡分列）
  4. 主城内部差异（渝中老城 vs 两江新区/渝北）
  5. 各区县老龄化率排名

方法:
  使用 GeoPandas + Folium 生成分级设色图
  使用 matplotlib 生成对比统计图
============================================================
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


# ==================== 1. 区域分类 ====================

# 中心城区（主城9区）
CORE_DISTRICTS = [
    "渝中区", "大渡口区", "江北区", "沙坪坝区", "九龙坡区",
    "南岸区", "北碚区", "渝北区", "巴南区",
]

# 主城都市区 = 中心城区9区 + 主城新区12区
METRO_DISTRICTS = CORE_DISTRICTS + [
    "涪陵区", "长寿区", "江津区", "合川区", "永川区",
    "南川区", "綦江区", "大足区", "璧山区", "铜梁区",
    "潼南区", "荣昌区",
]

# 渝东北11区县
YUDONGBEI_DISTRICTS = [
    "万州区", "梁平区", "开州区", "城口县", "丰都县",
    "垫江县", "忠县", "云阳县", "奉节县", "巫山县", "巫溪县",
]

# 渝东南6区县
YUDONGNAN_DISTRICTS = [
    "黔江区", "武隆区", "石柱县", "秀山县", "酉阳县", "彭水县",
]


def region_classify_yiqu(district: str) -> str:
    """
    按"一区两群"分类（重庆官方空间规划）:
        - 主城都市区（21区）
        - 渝东北三峡库区城镇群（11区县）
        - 渝东南武陵山区城镇群（6区县）
    """
    if district in METRO_DISTRICTS:
        return "主城都市区"
    elif district in YUDONGBEI_DISTRICTS:
        return "渝东北"
    elif district in YUDONGNAN_DISTRICTS:
        return "渝东南"
    return "其他"


def urban_vs_remote_classify(district: str) -> str:
    """
    城区 vs 远郊分类:
        - 城区: 中心城区9区
        - 远郊: 其余29区县
    """
    return "中心城区" if district in CORE_DISTRICTS else "远郊区县"


def urban_internal_zone(district: str) -> str:
    """
    主城内部功能区划分:
        - 老城核心: 渝中区（历史文化老城）
        - 都市核心: 大渡口、江北、沙坪坝、九龙坡、南岸
        - 都市拓展: 北碚、渝北、巴南（含两江新区）
    """
    old_core = ["渝中区"]
    core = ["大渡口区", "江北区", "沙坪坝区", "九龙坡区", "南岸区"]
    expansion = ["北碚区", "渝北区", "巴南区"]
    if district in old_core:
        return "老城核心"
    elif district in core:
        return "都市核心"
    elif district in expansion:
        return "都市拓展区"
    return "远郊区县"


# ==================== 2. 核心分析函数 ====================


def compute_aging_rates(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算各区县各年份老龄化率，并附加分类标签

    返回:
        DataFrame 增加列:
            - 老龄化率: 65岁及以上人口 / 常住人口
            - 一区两群: 区域分类
            - 城乡类型: 城区/远郊
    """
    df = df.copy()
    df["老龄化率"] = df["65岁及以上人口"] / df["常住人口"]
    df["一区两群"] = df["区县"].apply(region_classify_yiqu)
    df["城乡类型"] = df["区县"].apply(urban_vs_remote_classify)
    df["主城功能"] = df["区县"].apply(urban_internal_zone)
    return df


def aging_rate_ranking(df: pd.DataFrame, year: int = 2024) -> pd.DataFrame:
    """
    各区县老龄化率排名（从高到低）
    """
    sub = df[df["年份"] == year].copy()
    sub["老龄化率"] = sub["65岁及以上人口"] / sub["常住人口"]
    result = sub[["区县", "老龄化率", "一区两群", "城乡类型"]].copy()
    result = result.sort_values("老龄化率", ascending=False).reset_index(drop=True)
    result["排名"] = range(1, len(result) + 1)
    result["老龄化等级"] = result["老龄化率"].apply(
        lambda x: "深度" if x > 0.30 else ("重度" if x > 0.25 else (
                  "中度" if x > 0.18 else "轻度"))
    )
    return result


def yiqu_liangqun_statistics(df: pd.DataFrame, year: int = 2024) -> pd.DataFrame:
    """
    一区两群分区统计：平均老龄化率、最高/最低、标准差
    """
    df = compute_aging_rates(df)
    sub = df[df["年份"] == year]
    stats = sub.groupby("一区两群").agg(
        平均老龄化率=("老龄化率", "mean"),
        最高区县=("老龄化率", "max"),
        最低区县=("老龄化率", "min"),
        标准差=("老龄化率", "std"),
        区县数量=("区县", "count"),
    ).round(4)
    stats["平均老龄化率"] = stats["平均老龄化率"].map("{:.1%}".format)
    stats["最高区县"] = stats["最高区县"].map("{:.1%}".format)
    stats["最低区县"] = stats["最低区县"].map("{:.1%}".format)
    return stats


def urban_remote_comparison(df: pd.DataFrame, year: int = 2024) -> pd.DataFrame:
    """
    中心城区 vs 远郊区县 老龄化率对比
    """
    df = compute_aging_rates(df)
    sub = df[df["年份"] == year]
    stats = sub.groupby("城乡类型").agg(
        平均老龄化率=("老龄化率", "mean"),
        中位数=("老龄化率", "median"),
        最高=("老龄化率", "max"),
        最低=("老龄化率", "min"),
        区县数量=("区县", "count"),
    ).round(4)
    return stats


def elderly_dependency_ratio(df: pd.DataFrame, year: int = 2024) -> pd.DataFrame:
    """
    老年抚养比计算

    老年抚养比 = 65岁及以上人口 / 15-64岁劳动年龄人口

    分城镇（中心城区）和农村（远郊区县）计算
    """
    df = compute_aging_rates(df)
    sub = df[df["年份"] == year].copy()
    sub["老年抚养比"] = sub["65岁及以上人口"] / sub["15-64岁人口"]

    stats = sub.groupby("城乡类型").agg(
        老年抚养比=("老年抚养比", "mean"),
        最高区县=("老年抚养比", "max"),
        最低区县=("老年抚养比", "min"),
        劳动人口_万人=("15-64岁人口", lambda x: x.sum() / 1e4),
        老年人口_万人=("65岁及以上人口", lambda x: x.sum() / 1e4),
    ).round(4)

    stats["抚养比说明"] = stats["老年抚养比"].apply(
        lambda x: f"每{int(1/x)}个劳动力抚养1个老人" if x > 0 else ""
    )
    return stats


def urban_internal_comparison(df: pd.DataFrame, year: int = 2024) -> pd.DataFrame:
    """
    主城内部差异分析:
        - 老城核心（渝中区）vs 都市拓展区（渝北区等）
        - 显示老龄化率、抚养比、人口密度等
    """
    df = compute_aging_rates(df)
    sub = df[df["年份"] == year].copy()
    sub["老年抚养比"] = sub["65岁及以上人口"] / sub["15-64岁人口"]
    sub["少儿抚养比"] = sub["0-14岁人口"] / sub["15-64岁人口"]
    sub["总抚养比"] = (sub["65岁及以上人口"] + sub["0-14岁人口"]) / sub["15-64岁人口"]

    # 只看主城区
    core = sub[sub["区县"].isin(CORE_DISTRICTS)].copy()
    core["主城功能"] = core["区县"].apply(urban_internal_zone)

    stats = core.groupby("主城功能").agg(
        区县数量=("区县", "count"),
        平均老龄化率=("老龄化率", "mean"),
        最高老龄化率=("老龄化率", "max"),
        最低老龄化率=("老龄化率", "min"),
        老年抚养比=("老年抚养比", "mean"),
        总抚养比=("总抚养比", "mean"),
    ).round(4)

    return stats


def aging_rate_trend_comparison(
    df: pd.DataFrame,
    districts_a: List[str],
    districts_b: List[str],
    label_a: str = "组A",
    label_b: str = "组B",
) -> pd.DataFrame:
    """
    两组区县老龄化率趋势对比
    """
    df = compute_aging_rates(df)
    df["分组"] = df["区县"].apply(
        lambda x: label_a if x in districts_a else (
                  label_b if x in districts_b else "其他")
    )
    trend = df[df["分组"] != "其他"].groupby(["年份", "分组"])["老龄化率"].mean().unstack()
    return trend.round(4)


# ==================== 3. 汇总输出 ====================


def full_spatial_report(df: pd.DataFrame, year: int = 2024) -> dict:
    """
    运行所有空间分析，返回汇总结果字典
    """
    df = compute_aging_rates(df)

    results = {}

    # 1. 各区县排名
    results["ranking"] = aging_rate_ranking(df, year)

    # 2. 一区两群
    results["yiqu"] = yiqu_liangqun_statistics(df, year)

    # 3. 城乡对比
    results["urban_remote"] = urban_remote_comparison(df, year)

    # 4. 老年抚养比
    results["dependency"] = elderly_dependency_ratio(df, year)

    # 5. 主城内部
    results["urban_internal"] = urban_internal_comparison(df, year)

    # 6. 极端值区县
    sub = df[df["年份"] == year]
    top5 = sub.nlargest(5, "老龄化率")[["区县", "老龄化率", "一区两群", "城乡类型"]]
    bottom5 = sub.nsmallest(5, "老龄化率")[["区县", "老龄化率", "一区两群", "城乡类型"]]
    results["top5"] = top5
    results["bottom5"] = bottom5

    # 打印报告
    _print_report(results, year)

    return results


def _print_report(results: dict, year: int):
    """打印分析报告"""
    print(f"\n{'='*60}")
    print(f"📊 维度一：老龄化空间分布分析（{year}年）")
    print(f"{'='*60}")

    # 排名 TOP/BOTTOM
    top5 = results["top5"]
    bottom5 = results["bottom5"]
    print(f"\n  🔺 老龄化率最高 TOP 5:")
    for _, r in top5.iterrows():
        print(f"     {r['区县']:6s}  {r['老龄化率']:.1%}  [{r['一区两群']}]")
    print(f"\n  🔻 老龄化率最低 TOP 5:")
    for _, r in bottom5.iterrows():
        print(f"     {r['区县']:6s}  {r['老龄化率']:.1%}  [{r['一区两群']}]")

    # 一区两群
    yiqu = results["yiqu"]
    print(f"\n  📌 一区两群分区统计:")
    for region, row in yiqu.iterrows():
        print(f"     {region:8s} | {row['平均老龄化率']:>6s} | 区县{int(row['区县数量'])}个")

    # 城乡对比
    ur = results["urban_remote"]
    print(f"\n  📌 城区 vs 远郊对比:")
    for cat, row in ur.iterrows():
        print(f"     {cat:6s} | 平均老龄化率 {row['平均老龄化率']:.1%} | 中位数 {row['中位数']:.1%}")

    # 抚养比
    dep = results["dependency"]
    print(f"\n  📌 老年抚养比:")
    for cat, row in dep.iterrows():
        print(f"     {cat:6s} | {row['老年抚养比']:.1%} | {row['抚养比说明']}")

    # 主城内部
    ui = results["urban_internal"]
    print(f"\n  📌 主城内部差异:")
    for zone, row in ui.iterrows():
        print(f"     {zone:8s} | 平均老龄化率 {row['平均老龄化率']:.1%} | 老年抚养比 {row['老年抚养比']:.1%}")

    print(f"\n{'='*60}")
