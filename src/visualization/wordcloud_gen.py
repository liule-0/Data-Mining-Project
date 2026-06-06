"""
词云生成模块
基于评论关键词生成中文词云
"""

import os
import pandas as pd
from wordcloud import WordCloud
import matplotlib
matplotlib.rc("font", family="Microsoft YaHei")
import matplotlib.pyplot as plt
from typing import Optional


def generate_wordcloud(
    word_freq_df: pd.DataFrame,
    save_path: Optional[str] = None,
    title: str = "评论关键词词云",
    width: int = 800,
    height: int = 600,
    max_words: int = 100,
    background_color: str = "white",
    colormap: str = "viridis",
):
    """
    根据词频生成词云

    参数:
        word_freq_df: 包含 "word" 和 "frequency" 两列的 DataFrame
        save_path: 保存路径
        title: 图表标题
    """
    word_dict = dict(zip(word_freq_df["word"], word_freq_df["frequency"]))

    wc = WordCloud(
        font_path="C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
        width=width,
        height=height,
        max_words=max_words,
        background_color=background_color,
        colormap=colormap,
        random_state=42,
        prefer_horizontal=0.7,
    ).generate_from_frequencies(word_dict)

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"词云已保存: {save_path}")

    return fig
