"""
维度二：医疗压力演变趋势可视化图表
- 老年住院占比折线图（含年增长率标注）
- 慢病住院量堆叠面积图（疾病谱演变）
"""

import os
from typing import List, Optional
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei",
                                    "Noto Sans CJK SC", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

# 配色方案
DISEASE_COLORS = {
    "心衰": "#e74c3c",
    "高血压": "#3498db",
    "糖尿病": "#f39c12",
    "慢阻肺": "#2ecc71",
    "脑卒中": "#9b59b6",
    "冠心病": "#1abc9c",
}


def plot_elderly_hospitalization_with_growth(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
):
    """
    老年住院占比趋势折线图 + 年增长率柱状图（双轴）
    """
    from src.analysis.healthcare_evolution import elderly_hospitalization_yearly

    trend = elderly_hospitalization_yearly(df)

    fig, ax1 = plt.subplots(figsize=(12, 6.5))

    years = trend.index.tolist()
    means = trend["mean"].values * 100  # 转为%
    min_vals = trend["min"].values * 100
    max_vals = trend["max"].values * 100

    # ---- 主轴：占比折线 ----
    color_main = "#2c3e50"
    ax1.plot(years, means, color=color_main, marker="o", linewidth=2.5,
             markersize=8, zorder=5, label="老年住院占比")
    # 置信区间
    ax1.fill_between(years, min_vals, max_vals, alpha=0.12, color=color_main)
    # 标注数值
    for x, y in zip(years, means):
        ax1.annotate(f"{y:.1f}%", xy=(x, y), textcoords="offset points",
                    xytext=(0, 12), ha="center", fontsize=9, fontweight="bold",
                    color=color_main)

    ax1.set_xlabel("年份", fontsize=12)
    ax1.set_ylabel("老年住院占比（%）", fontsize=12, color=color_main)
    ax1.tick_params(axis="y", labelcolor=color_main)
    ax1.set_xticks(years)
    ax1.set_xticklabels(years)
    ax1.set_ylim(0, max_vals.max() * 1.25)
    ax1.grid(True, alpha=0.25, linestyle="dashed")

    # ---- 副轴：年增长率柱状图 ----
    ax2 = ax1.twinx()
    yoy = trend["YoY(百分点)"].dropna()
    colors_bar = ["#e74c3c" if v >= 0 else "#3498db" for v in yoy.values]
    bars = ax2.bar(yoy.index, yoy.values, width=0.5, alpha=0.35,
                   color=colors_bar, edgecolor="gray", linewidth=0.5,
                   zorder=0, label="年变化(百分点)")

    # 标注增长率
    for x, v in zip(yoy.index, yoy.values):
        offset = 8 if v >= 0 else -16
        ax2.annotate(f"{v:+.1f}pp", xy=(x, v), textcoords="offset points",
                    xytext=(0, offset), ha="center", fontsize=7.5,
                    color="#c0392b" if v >= 0 else "#2980b9")

    ax2.axhline(y=0, color="gray", linewidth=0.5, alpha=0.5)
    ax2.set_ylabel("年变化（百分点）", fontsize=12, color="#7f8c8d")
    ax2.tick_params(axis="y", labelcolor="#7f8c8d")

    # 总增幅标注
    total_rise = trend["总增幅(百分点)"].iloc[-1]
    cagr = trend["CAGR(%)"].iloc[-1]
    summary_text = (
        f"2016→2024 总增幅: {total_rise:.1f}pp\n"
        f"年均复合增长率(CAGR): {cagr:.1f}%/年"
    )
    ax1.text(0.98, 0.05, summary_text, transform=ax1.transAxes,
            fontsize=10, va="bottom", ha="right",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                     edgecolor="gray", alpha=0.9))

    # 合并图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)

    ax1.set_title("老年住院占比趋势（2016-2024）", fontsize=14, fontweight="bold")
    fig.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"  ✅ 老年住院占比趋势图已保存: {save_path}")
    plt.close()


def plot_disease_spectrum_stacked_area(
    df: pd.DataFrame,
    diseases: List[str] = None,
    save_path: Optional[str] = None,
):
    """
    疾病谱变迁——堆叠面积图
    展示各慢病在慢病总住院量中占比的逐年变化
    """
    from src.analysis.healthcare_evolution import disease_spectrum_evolution

    if diseases is None:
        diseases = ["心衰", "高血压", "糖尿病", "慢阻肺", "脑卒中"]

    spectrum = disease_spectrum_evolution(df, diseases=diseases)
    years = spectrum.index.tolist()

    colors = [DISEASE_COLORS.get(d, "#95a5a6") for d in spectrum.columns]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6.5),
                                    gridspec_kw={"width_ratios": [1.5, 1]})

    # ===== 左图：堆叠面积图 =====
    ax1.stackplot(years,
                  [spectrum[c].values for c in spectrum.columns],
                  labels=spectrum.columns.tolist(),
                  colors=colors, alpha=0.85, edgecolor="white", linewidth=0.3)

    # 标注2016和2024的构成
    for yr in [years[0], years[-1]]:
        cumsum = 0
        proportions = spectrum.loc[yr]
        for disease, pct in proportions.items():
            cumsum += pct
            y_pos = (cumsum - pct / 2) * 100
            if pct > 0.08:  # 占比>8%才标注
                ax1.text(yr, cumsum * 100 - pct * 50, f"{disease}\n{pct:.0%}",
                        ha="center", va="center", fontsize=6.5,
                        color="white", fontweight="bold")

    ax1.set_xlabel("年份", fontsize=12)
    ax1.set_ylabel("疾病谱占比（%）", fontsize=12)
    ax1.set_title("慢病疾病谱演变（堆叠面积图）", fontsize=14, fontweight="bold")
    ax1.set_ylim(0, 1.05)
    ax1.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax1.set_yticklabels(["0%", "20%", "40%", "60%", "80%", "100%"])
    ax1.set_xticks(years)
    ax1.set_xticklabels(years, rotation=45)
    ax1.legend(loc="upper left", fontsize=8, framealpha=0.8)
    ax1.grid(axis="y", alpha=0.2)

    # ===== 右图：2016 vs 2024 谱对比条形图 =====
    year_start = years[0]
    year_end = years[-1]
    s_start = spectrum.loc[year_start]
    s_end = spectrum.loc[year_end]

    disease_names = spectrum.columns.tolist()
    y_pos = range(len(disease_names))

    start_vals = [s_start[d] * 100 for d in disease_names]
    end_vals = [s_end[d] * 100 for d in disease_names]

    ax2.barh([y - 0.15 for y in y_pos], start_vals, height=0.3,
             color=[DISEASE_COLORS.get(d, "#95a5a6") for d in disease_names],
             alpha=0.6, label=str(year_start), edgecolor="white")
    ax2.barh([y + 0.15 for y in y_pos], end_vals, height=0.3,
             color=[DISEASE_COLORS.get(d, "#95a5a6") for d in disease_names],
             alpha=1.0, label=str(year_end), edgecolor="white")

    # 标注变化箭头
    for i, d in enumerate(disease_names):
        change = end_vals[i] - start_vals[i]
        arrow = "↑" if change > 0 else "↓"
        color = "#e74c3c" if change > 0 else "#27ae60"
        ax2.text(max(start_vals[i], end_vals[i]) + 1.5, i,
                f"{arrow}{abs(change):.1f}pp", va="center", fontsize=8,
                color=color, fontweight="bold")

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(disease_names, fontsize=10)
    ax2.set_xlabel("疾病谱占比（%）", fontsize=11)
    ax2.set_title(f"疾病谱结构对比: {year_start} vs {year_end}", fontsize=14, fontweight="bold")
    ax2.legend(fontsize=9, loc="lower right")
    ax2.invert_yaxis()
    ax2.grid(axis="x", alpha=0.2)

    fig.tight_layout(pad=2.0)
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"  ✅ 疾病谱演变堆叠面积图已保存: {save_path}")
    plt.close()


def plot_disease_growth_multi_line(
    df: pd.DataFrame,
    diseases: List[str] = None,
    save_path: Optional[str] = None,
):
    """
    各慢病住院量增长倍数折线图（以2016为基准=1）
    """
    from src.analysis.healthcare_evolution import chronic_disease_growth_analysis

    if diseases is None:
        diseases = ["心衰", "高血压", "糖尿病", "慢阻肺", "脑卒中"]

    trend = chronic_disease_growth_analysis(df, diseases=diseases)

    growth_cols = [f"{d}_增长倍数" for d in diseases]
    growth_cols = [c for c in growth_cols if c in trend.columns]
    short_names = [c.replace("_增长倍数", "") for c in growth_cols]

    fig, ax = plt.subplots(figsize=(11, 6))

    for i, (col, short) in enumerate(zip(growth_cols, short_names)):
        data = trend[col]
        color = DISEASE_COLORS.get(short, None)
        ax.plot(data.index, data.values, marker="o", linewidth=2.2,
                markersize=6, label=short, color=color)
        # 标注最终值
        ax.annotate(f"{data.iloc[-1]:.2f}x", xy=(data.index[-1], data.iloc[-1]),
                   textcoords="offset points", xytext=(10, 0),
                   fontsize=9, fontweight="bold", color=color)

    ax.axhline(y=1, color="gray", linestyle="dashed", alpha=0.4, linewidth=0.8)
    ax.set_xlabel("年份", fontsize=12)
    ax.set_ylabel("增长倍数（基准年=1）", fontsize=12)
    ax.set_title("主要慢病住院量增长趋势（2016=1倍基准）", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10, loc="upper left")
    ax.grid(True, alpha=0.25)
    ax.set_xticks(trend.index.tolist())

    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"  ✅ 慢病增长倍数图已保存: {save_path}")
    plt.close()


def plot_hospitalization_growth_comparison(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
):
    """
    总住院 vs 老年住院 增长率对比
    """
    from src.analysis.healthcare_evolution import hospitalization_growth_rate

    growth = hospitalization_growth_rate(df)

    fig, ax = plt.subplots(figsize=(11, 6))

    years = growth.index.tolist()
    total_growth = growth["总住院人次_增长率(%)"]
    elderly_growth = growth["老年住院人次_增长率(%)"]

    ax.plot(years, total_growth.values, marker="s", color="#3498db",
            linewidth=2, markersize=7, label="总住院人次增长率")
    ax.plot(years, elderly_growth.values, marker="o", color="#e74c3c",
            linewidth=2.5, markersize=8, label="老年住院人次增长率")

    # 标注差异
    for x, tv, ev in zip(years, total_growth.values, elderly_growth.values):
        diff = ev - tv
        if not pd.isna(diff) and abs(diff) > 1:
            offset = 8 if diff > 0 else -12
            ax.annotate(f"+{diff:.1f}pp", xy=(x, ev),
                       textcoords="offset points", xytext=(0, offset),
                       ha="center", fontsize=7, color="#e74c3c")

    ax.axhline(y=0, color="gray", linewidth=0.6, alpha=0.5)
    ax.set_xlabel("年份", fontsize=12)
    ax.set_ylabel("年增长率（%）", fontsize=12)
    ax.set_title("总住院 vs 老年住院 年增长率对比", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.25)
    ax.set_xticks(years)

    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"  ✅ 住院增长率对比图已保存: {save_path}")
    plt.close()
