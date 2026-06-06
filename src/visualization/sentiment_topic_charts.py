"""
维度三：舆情情感与主题可视化
- SnowNLP 情感分布图
- LDA 主题词云/条形图
- 各主题情感对比
"""

import os
from typing import List, Optional
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from wordcloud import WordCloud

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei",
                                    "Noto Sans CJK SC", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def plot_snownlp_distribution(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
):
    """
    SnowNLP 情感分值分布直方图 + 阈值线
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    scores = df["snownlp_score"]

    # ===== 左图：分值分布直方图 =====
    ax1.hist(scores, bins=50, color="#3498db", alpha=0.7, edgecolor="white", linewidth=0.3)
    ax1.axvline(x=0.5, color="#e74c3c", linestyle="dashed", linewidth=2, label="阈值 0.5")
    ax1.axvline(x=scores.mean(), color="#2c3e50", linestyle="dotted", linewidth=1.5,
               label=f"均值 {scores.mean():.2f}")
    ax1.set_xlabel("SnowNLP 情感分值", fontsize=11)
    ax1.set_ylabel("评论数量", fontsize=11)
    ax1.set_title("情感分值分布直方图", fontsize=13, fontweight="bold")
    ax1.legend(fontsize=9)
    ax1.grid(axis="y", alpha=0.25)

    # ===== 右图：情感类别饼图 =====
    labels = df["snownlp_label"].value_counts().index.tolist()
    values = df["snownlp_label"].value_counts().values.tolist()
    colors_pie = {"正面": "#2ecc71", "中性": "#95a5a6", "负面": "#e74c3c"}
    pie_colors = [colors_pie.get(l, "#95a5a6") for l in labels]

    wedges, texts, autotexts = ax2.pie(
        values, labels=labels, autopct="%1.1f%%",
        colors=pie_colors, startangle=90,
        textprops={"fontsize": 12},
    )
    for t in autotexts:
        t.set_fontweight("bold")
        t.set_color("white")
    ax2.set_title("SnowNLP 情感类别占比", fontsize=13, fontweight="bold")

    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"  ✅ SnowNLP 情感分布图已保存: {save_path}")
    plt.close()


def plot_lda_topics_horizontal(
    lda_results: dict,
    save_path: Optional[str] = None,
):
    """
    LDA 各主题关键词水平条形图
    """
    topics = lda_results["topics"]
    n_topics = len(topics)
    n_words = min(10, len(topics[0]))

    fig, axes = plt.subplots(1, n_topics, figsize=(4 * n_topics, 5.5))

    topic_colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6",
                    "#1abc9c", "#e67e22", "#34495e"]

    for i in range(n_topics):
        ax = axes[i] if n_topics > 1 else axes
        words = [w for w, _ in topics[i][:n_words]][::-1]
        weights = [w for _, w in topics[i][:n_words]][::-1]

        ax.barh(range(len(words)), weights, color=topic_colors[i % len(topic_colors)],
               alpha=0.8, edgecolor="white", height=0.6)
        ax.set_yticks(range(len(words)))
        ax.set_yticklabels(words, fontsize=9)
        ax.set_xlabel("权重", fontsize=9)
        ax.set_title(f"主题 {i+1}", fontsize=12, fontweight="bold", color=topic_colors[i])
        ax.grid(axis="x", alpha=0.2)

    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"  ✅ LDA 主题关键词图已保存: {save_path}")
    plt.close()


def plot_lda_topic_wordcloud(
    lda_results: dict,
    save_path_pattern: str = None,
):
    """
    LDA 每个主题生成独立词云

    参数:
        save_path_pattern: 如 "output/figures/sentiment/lda_topic_{}.png"
    """
    topics = lda_results["topics"]

    for topic_id, words in topics.items():
        # 构建词云数据字典
        word_freq = {w: max(s, 0.1) for w, s in words}

        wc = WordCloud(
            font_path="C:/Windows/Fonts/simhei.ttf",
            width=800, height=500,
            background_color="white",
            max_words=50,
            max_font_size=120,
            collocations=False,
        ).generate_from_frequencies(word_freq)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        ax.set_title(f"LDA 主题 {topic_id+1}", fontsize=16, fontweight="bold", pad=15)

        plt.tight_layout()
        if save_path_pattern:
            path = save_path_pattern.format(topic_id + 1)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            plt.savefig(path, dpi=200, bbox_inches="tight")
            print(f"  ✅ LDA 主题 {topic_id+1} 词云已保存: {path}")
        plt.close()


def plot_lda_dominant_distribution(
    lda_results: dict,
    df_labels: pd.Series,
    save_path: Optional[str] = None,
):
    """
    各主题的情感分布堆叠条形图
    """
    topic_dist = lda_results["topic_dist"]
    dominant = topic_dist.idxmax(axis=1)

    # 主题编号映射
    topic_map = {f"主题{i+1}_权重": i+1 for i in range(len(lda_results["topics"]))}
    dominant_topic_num = dominant.map(topic_map)

    # 交叉表：主题 × 情感
    cross = pd.crosstab(dominant_topic_num, df_labels, normalize="index")

    fig, ax = plt.subplots(figsize=(10, 5.5))

    topics_sorted = sorted(cross.index)
    labels = [f"主题 {t}" for t in topics_sorted]
    colors = {"正面": "#2ecc71", "中性": "#95a5a6", "负面": "#e74c3c"}
    sentiment_order = ["正面", "中性", "负面"]

    bottom = np.zeros(len(topics_sorted))
    for sentiment in sentiment_order:
        if sentiment in cross.columns:
            values = cross[sentiment].values
            bars = ax.bar(labels, values, bottom=bottom, label=sentiment,
                         color=colors[sentiment], alpha=0.85, edgecolor="white",
                         width=0.5)
            bottom += values

    ax.set_ylabel("占比", fontsize=11)
    ax.set_title("各主题情感分布", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", alpha=0.2)

    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"  ✅ 主题情感分布图已保存: {save_path}")
    plt.close()


def plot_word_frequency(
    word_freq: pd.DataFrame,
    top_n: int = 30,
    save_path: Optional[str] = None,
):
    """
    词频条形图
    """
    top = word_freq.head(top_n).copy()

    fig, ax = plt.subplots(figsize=(10, 8))

    top = top.sort_values("frequency", ascending=True)
    colors = plt.cm.Blues(np.linspace(0.4, 0.85, len(top)))

    ax.barh(range(len(top)), top["frequency"].values, color=colors, edgecolor="white")
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top["word"].values, fontsize=9)
    ax.set_xlabel("频次", fontsize=11)
    ax.set_title(f"高频词 TOP {top_n}", fontsize=14, fontweight="bold")
    ax.grid(axis="x", alpha=0.2)

    # 标注数值
    for i, v in enumerate(top["frequency"].values):
        ax.text(v + max(top["frequency"]) * 0.005, i, str(v), va="center", fontsize=7)

    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"  ✅ 词频图已保存: {save_path}")
    plt.close()


def plot_platform_sentiment(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
):
    """
    各平台 SnowNLP 情感对比
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # 左图：各平台平均情感分
    platform_scores = df.groupby("platform")["snownlp_score"].agg(["mean", "std", "count"])
    platforms = platform_scores.index.tolist()
    means = platform_scores["mean"].values
    stds = platform_scores["std"].values

    colors_plat = {"抖音": "#ff6b6b", "快手": "#feca57"}
    bar_colors = [colors_plat.get(p, "#95a5a6") for p in platforms]

    bars = ax1.bar(platforms, means, yerr=stds, capsize=8, color=bar_colors,
                  alpha=0.8, edgecolor="white", width=0.4)
    for bar, m in zip(bars, means):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f"{m:.3f}", ha="center", fontsize=10, fontweight="bold")
    ax1.axhline(y=0.5, color="red", linestyle="dashed", alpha=0.5, label="阈值0.5")
    ax1.set_ylabel("平均情感分值", fontsize=11)
    ax1.set_title("各平台平均情感分值", fontsize=13, fontweight="bold")
    ax1.legend(fontsize=9)
    ax1.set_ylim(0, 1)
    ax1.grid(axis="y", alpha=0.2)

    # 右图：各平台情感类别堆叠
    cross = pd.crosstab(df["platform"], df["snownlp_label"], normalize="index")
    sentiment_colors = {"正面": "#2ecc71", "中性": "#95a5a6", "负面": "#e74c3c"}
    order = ["正面", "中性", "负面"]

    bottom = np.zeros(len(cross.index))
    for s in order:
        if s in cross.columns:
            vals = cross[s].values
            ax2.bar(cross.index, vals, bottom=bottom, label=s,
                   color=sentiment_colors[s], alpha=0.85, edgecolor="white", width=0.4)
            bottom += vals

    ax2.set_ylabel("占比", fontsize=11)
    ax2.set_title("各平台情感构成", fontsize=13, fontweight="bold")
    ax2.legend(fontsize=9)
    ax2.set_ylim(0, 1.05)
    ax2.grid(axis="y", alpha=0.2)

    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"  ✅ 平台情感对比图已保存: {save_path}")
    plt.close()
