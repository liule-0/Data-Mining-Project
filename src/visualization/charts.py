"""
图表可视化模块
生成老龄化趋势、医疗压力、舆情分析等静态图表
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.rc("font", family="Microsoft YaHei", size=10)
matplotlib.rc("axes", unicode_minus=False)
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, List, Tuple


def plot_aging_trend(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
    title: str = "重庆市各区县老龄化率年度趋势（2016-2024）",
    figsize: Tuple = (12, 6),
):
    """绘制各区县老龄化率趋势折线图"""
    fig, ax = plt.subplots(figsize=figsize)
    for district in df.index:
        ax.plot(df.columns, df.loc[district].values, marker="o", label=district, linewidth=1.5)
    ax.set_xlabel("年份")
    ax.set_ylabel("老龄化率")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"图表已保存: {save_path}")
    return fig


def plot_aging_regional_comparison(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
    title: str = "重庆市四大区域老龄化率对比",
    figsize: Tuple = (10, 6),
):
    """绘制四大区域老龄化率柱状图对比"""
    fig, ax = plt.subplots(figsize=figsize)
    regions = df.index.get_level_values("区域").unique()
    years = df.index.get_level_values("年份").unique()
    width = 0.18
    x = np.arange(len(years))
    colors = ["#2196F3", "#FF9800", "#4CAF50", "#F44336"]
    for i, region in enumerate(regions):
        vals = df.loc[region]["mean"].values
        ax.bar(x + i * width, vals, width, label=region, color=colors[i], alpha=0.8)
    ax.set_xlabel("年份")
    ax.set_ylabel("平均老龄化率")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(years)
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig


def plot_elderly_hospitalization_trend(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
    title: str = "重庆市老年住院占比年度趋势（2016-2024）",
    figsize: Tuple = (10, 5),
):
    """绘制老年住院占比趋势"""
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(df.index, df["mean"] * 100, marker="s", color="#D32F2F", linewidth=2.5, label="平均老年住院占比")
    ax.fill_between(df.index, df["min"] * 100, df["max"] * 100, alpha=0.2, color="#D32F2F", label="范围")
    ax.set_xlabel("年份")
    ax.set_ylabel("老年住院占比 (%)")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig


def plot_chronic_disease_growth(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
    title: str = "主要慢病住院量增长倍数（以2016年为基准）",
    figsize: Tuple = (12, 6),
):
    """绘制慢病住院量增长倍数"""
    growth_cols = [c for c in df.columns if "增长倍数" in c]
    if not growth_cols:
        return None
    fig, ax = plt.subplots(figsize=figsize)
    years = df.index[1:]  # 排除基年
    for col in growth_cols:
        disease_name = col.replace("_增长倍数", "")
        ax.plot(years, df.loc[years, col].values, marker="o", linewidth=2, label=disease_name)
    ax.axhline(y=1, color="gray", linestyle="--", alpha=0.5, label="基准线（1倍）")
    ax.set_xlabel("年份")
    ax.set_ylabel("增长倍数")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig


def plot_sentiment_distribution(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
    title: str = "短视频平台老龄化话题评论情感分布",
    figsize: Tuple = (8, 6),
):
    """绘制情感分布饼图"""
    fig, ax = plt.subplots(figsize=figsize)
    dist = df["sentiment_label"].value_counts()
    colors_map = {"正面": "#4CAF50", "中性": "#FFC107", "负面": "#F44336"}
    colors = [colors_map.get(c, "#999") for c in dist.index]
    wedges, texts, autotexts = ax.pie(
        dist.values,
        labels=dist.index,
        autopct="%1.1f%%",
        colors=colors,
        startangle=90,
        explode=[0.03] * len(dist),
        textprops={"fontsize": 12},
    )
    ax.set_title(title, fontsize=14, fontweight="bold")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig


def plot_negative_keywords(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
    title: str = "负面评论高频关键词TOP15",
    figsize: Tuple = (10, 6),
):
    """绘制负面评论关键词水平柱状图"""
    fig, ax = plt.subplots(figsize=figsize)
    df = df.head(15)
    ax.barh(range(len(df)), df["出现频次"], color="#F44336", alpha=0.8)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["关键词"])
    ax.set_xlabel("出现频次")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3, axis="x")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig
