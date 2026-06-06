"""
维度一：空间分析专用可视化图表
生成各区县排名、城乡对比、一区两群对比、主城内部差异等统计图
"""

import os
from typing import Optional
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# 中文字体
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei", "Noto Sans CJK SC", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def plot_aging_ranking(
    df: pd.DataFrame,
    year: int = 2024,
    top_n: int = 38,
    save_path: Optional[str] = None,
):
    """
    各区县老龄化率排名水平条形图（从高到低）
    按"一区两群"着色
    """
    from src.analysis.spatial_analysis import compute_aging_rates

    df = compute_aging_rates(df)
    sub = df[df["年份"] == year].copy()
    sub = sub.sort_values("老龄化率", ascending=True)

    colors = {
        "主城都市区": "#3498db",
        "渝东北": "#2ecc71",
        "渝东南": "#e74c3c",
    }
    bar_colors = [colors.get(r, "#95a5a6") for r in sub["一区两群"]]

    fig, ax = plt.subplots(figsize=(10, 14))
    bars = ax.barh(range(len(sub)), sub["老龄化率"].values * 100,
                   color=bar_colors, edgecolor="white", height=0.7)

    # 标注数值
    for i, (v, district) in enumerate(zip(sub["老龄化率"].values, sub["区县"].values)):
        ax.text(v * 100 + 0.3, i, f"{v:.1%}", va="center", fontsize=7.5)

    ax.set_yticks(range(len(sub)))
    ax.set_yticklabels(sub["区县"].values, fontsize=8)
    ax.set_xlabel("老龄化率（%）", fontsize=11)
    ax.set_title(f"重庆市各区县老龄化率排名（{year}年）", fontsize=14, fontweight="bold")
    ax.set_xlim(0, sub["老龄化率"].max() * 100 + 5)

    # 图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#3498db", label="主城都市区"),
        Patch(facecolor="#2ecc71", label="渝东北"),
        Patch(facecolor="#e74c3c", label="渝东南"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=9)

    # 阈值线
    for threshold, label, style in [(18, "轻度", "dashed"), (25, "中度", "dashed"),
                                     (30, "深度", "dashed")]:
        ax.axvline(x=threshold, color="gray", linestyle=style, alpha=0.4, linewidth=0.8)
        ax.text(threshold + 0.1, -0.5, label, fontsize=7, color="gray", alpha=0.6)

    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"  ✅ 老龄化率排名图已保存: {save_path}")
    plt.close()


def plot_urban_remote_comparison(
    df: pd.DataFrame,
    years: list = None,
    save_path: Optional[str] = None,
):
    """
    中心城区 vs 远郊区县 老龄化率趋势对比折线图
    """
    from src.analysis.spatial_analysis import compute_aging_rates

    if years is None:
        years = list(range(2016, 2025))

    df = compute_aging_rates(df)
    trend = df.groupby(["年份", "城乡类型"])["老龄化率"].mean().unstack()

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = {"中心城区": "#e74c3c", "远郊区县": "#2c3e50"}
    markers = {"中心城区": "o", "远郊区县": "s"}

    for cat in ["中心城区", "远郊区县"]:
        if cat in trend.columns:
            data = trend[cat].loc[years]
            ax.plot(data.index, data.values * 100,
                    marker=markers[cat], color=colors[cat],
                    linewidth=2.5, markersize=7, label=cat)

            # 标注起止数值
            ax.annotate(f"{data.iloc[0]:.1f}%", xy=(data.index[0], data.values[0] * 100),
                       textcoords="offset points", xytext=(-20, 10), fontsize=10,
                       color=colors[cat], fontweight="bold")
            ax.annotate(f"{data.iloc[-1]:.1f}%", xy=(data.index[-1], data.values[-1] * 100),
                       textcoords="offset points", xytext=(10, -15), fontsize=10,
                       color=colors[cat], fontweight="bold")

            # 计算增幅
            inc = (data.iloc[-1] - data.iloc[0]) * 100
            mid_x = data.index[len(data)//2]
            mid_y = (data.values[0] + data.values[-1]) / 2 * 100
            ax.annotate(f"+{inc:.1f}pp", xy=(mid_x, mid_y),
                       textcoords="offset points", xytext=(30, 0),
                       fontsize=9, color=colors[cat], alpha=0.7,
                       arrowprops=dict(arrowstyle="->", color=colors[cat], alpha=0.5))

    ax.set_xlabel("年份", fontsize=12)
    ax.set_ylabel("老龄化率（%）", fontsize=12)
    ax.set_title("中心城区 vs 远郊区县 老龄化率趋势对比", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11, loc="upper left")
    ax.grid(True, alpha=0.3)
    ax.set_xticks(years)
    ax.set_xticklabels(years)

    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"  ✅ 城乡对比趋势图已保存: {save_path}")
    plt.close()


def plot_yiqu_comparison(
    df: pd.DataFrame,
    year: int = 2024,
    save_path: Optional[str] = None,
):
    """
    一区两群分组箱线图/柱状图
    """
    from src.analysis.spatial_analysis import compute_aging_rates

    df = compute_aging_rates(df)
    sub = df[df["年份"] == year].copy()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # 左图：柱状图（各区县分布）
    order = ["主城都市区", "渝东北", "渝东南"]
    colors = {"主城都市区": "#3498db", "渝东北": "#2ecc71", "渝东南": "#e74c3c"}

    # 均值柱状图
    means = sub.groupby("一区两群")["老龄化率"].mean()
    stds = sub.groupby("一区两群")["老龄化率"].std()

    x_pos = range(len(order))
    bars = ax1.bar(x_pos, [means[o] * 100 for o in order],
                   yerr=[stds[o] * 100 for o in order],
                   color=[colors[o] for o in order],
                   capsize=8, width=0.5, edgecolor="white", linewidth=1.5)

    for i, (o, bar) in enumerate(zip(order, bars)):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{means[o]:.1%}", ha="center", fontsize=11, fontweight="bold")

    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(order, fontsize=11)
    ax1.set_ylabel("平均老龄化率（%）", fontsize=11)
    ax1.set_title(f"一区两群平均老龄化率对比（{year}年）", fontsize=13, fontweight="bold")
    ax1.grid(axis="y", alpha=0.3)

    # 右图：各区县散点分布
    for region in order:
        region_data = sub[sub["一区两群"] == region]
        jitter = np.random.normal(0, 0.05, len(region_data))
        x = order.index(region) + jitter
        ax2.scatter(x, region_data["老龄化率"] * 100,
                   c=colors[region], alpha=0.6, s=40, edgecolors="white", linewidth=0.5)

    # 添加均值线
    for i, region in enumerate(order):
        ax2.axhline(y=means[region] * 100, xmin=i/3, xmax=(i+1)/3,
                   color=colors[region], linestyle="dashed", alpha=0.5)

    ax2.set_xticks(range(len(order)))
    ax2.set_xticklabels(order, fontsize=11)
    ax2.set_ylabel("老龄化率（%）", fontsize=11)
    ax2.set_title("各区县老龄化率分布散点", fontsize=13, fontweight="bold")
    ax2.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"  ✅ 一区两群对比图已保存: {save_path}")
    plt.close()


def plot_dependency_ratio(
    df: pd.DataFrame,
    year: int = 2024,
    save_path: Optional[str] = None,
):
    """
    老年抚养比对比图（城区 vs 远郊）
    """
    from src.analysis.spatial_analysis import compute_aging_rates, elderly_dependency_ratio

    dep = elderly_dependency_ratio(df, year)

    fig, ax = plt.subplots(figsize=(8, 5))

    categories = ["中心城区", "远郊区县"]
    values = [dep.loc["中心城区", "老年抚养比"] * 100,
              dep.loc["远郊区县", "老年抚养比"] * 100]

    bars = ax.bar(categories, values, color=["#e74c3c", "#2c3e50"],
                  width=0.4, edgecolor="white", linewidth=2)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
               f"{val:.1f}%", ha="center", fontsize=14, fontweight="bold")

    # 添加说明文字
    dep_texts = {
        "中心城区": f"每{int(1/dep.loc['中心城区','老年抚养比'])}个劳动力抚养1个老人",
        "远郊区县": f"每{int(1/dep.loc['远郊区县','老年抚养比'])}个劳动力抚养1个老人",
    }
    for i, cat in enumerate(categories):
        ax.text(i, values[i]/2, dep_texts[cat], ha="center", fontsize=9,
               color="white", fontweight="bold")

    ax.set_ylabel("老年抚养比（%）", fontsize=12)
    ax.set_title(f"老年抚养比对比：城区 vs 远郊（{year}年）", fontsize=14, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"  ✅ 老年抚养比对比图已保存: {save_path}")
    plt.close()


def plot_urban_internal(
    df: pd.DataFrame,
    year: int = 2024,
    save_path: Optional[str] = None,
):
    """
    主城内部功能区分化对比图
    """
    from src.analysis.spatial_analysis import compute_aging_rates, urban_internal_comparison

    ui = urban_internal_comparison(df, year)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    zones = ui.index.tolist()
    zone_colors = {"老城核心": "#c0392b", "都市核心": "#e67e22", "都市拓展区": "#2980b9"}

    # 左图：老龄化率
    rates = [ui.loc[z, "平均老龄化率"] * 100 for z in zones]
    bars1 = ax1.bar(zones, rates, color=[zone_colors[z] for z in zones],
                    width=0.4, edgecolor="white", linewidth=2)
    for bar, val in zip(bars1, rates):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f"{val:.1f}%", ha="center", fontsize=10, fontweight="bold")
    ax1.set_ylabel("平均老龄化率（%）", fontsize=11)
    ax1.set_title(f"主城内部老龄化率对比（{year}年）", fontsize=12, fontweight="bold")
    ax1.grid(axis="y", alpha=0.3)

    # 右图：抚养比
    x_labels = ["老年抚养比", "总抚养比"]
    dep_values = [[ui.loc[z, "老年抚养比"] * 100 for z in zones],
                  [ui.loc[z, "总抚养比"] * 100 for z in zones]]
    
    x = np.arange(len(zones))
    width = 0.3
    for i, (label, vals) in enumerate(zip(x_labels, dep_values)):
        offset = (i - 0.5) * width
        bars = ax2.bar(x + offset, vals, width, label=label,
                      color=["#e74c3c", "#3498db"][i], alpha=0.8)
        for bar, val in zip(bars, vals):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f"{val:.1f}%", ha="center", fontsize=7)

    ax2.set_xticks(x)
    ax2.set_xticklabels(zones, fontsize=9)
    ax2.set_ylabel("抚养比（%）", fontsize=11)
    ax2.set_title("主城内部抚养比对比", fontsize=12, fontweight="bold")
    ax2.legend(fontsize=9)
    ax2.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"  ✅ 主城内部差异图已保存: {save_path}")
    plt.close()
