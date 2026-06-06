"""
舆情情感分析模块
对短视频平台评论进行情感分析、主题挖掘与词频统计
"""

import pandas as pd
import numpy as np
from collections import Counter
from typing import List, Tuple, Dict

import jieba
import jionlp as jio


# ======================== 情感分析 ========================

# 加载 jionlp 情感词典（词 → 情感分值，负值为负面，正值为正面）
_SENTIMENT_LEXICON = None


def _get_lexicon():
    global _SENTIMENT_LEXICON
    if _SENTIMENT_LEXICON is None:
        _SENTIMENT_LEXICON = jio.sentiment_words_loader()
    return _SENTIMENT_LEXICON


def analyze_sentiment(text: str) -> float:
    """
    对单条文本进行基于情感词典的规则情感分析

    返回:
        float: 0~1 的情感得分，>0.55 为正面，<0.45 为负面
    """
    try:
        lexicon = _get_lexicon()
        words = jieba.lcut(str(text))
        scores = [lexicon.get(w, 0) for w in words if w in lexicon]
        if not scores:
            return 0.5
        avg_score = sum(scores) / len(scores)
        # 将 [-2, 2] 区间的原始情感分值映射到 [0, 1]
        normalized = (avg_score + 2) / 4
        return max(0.0, min(1.0, normalized))
    except Exception:
        return 0.5


def batch_sentiment_analysis(df: pd.DataFrame, text_col: str = "content") -> pd.DataFrame:
    """
    批量情感分析

    返回:
        DataFrame: 增加 sentiment_score 和 sentiment_label 列
    """
    df = df.copy()
    scores = df[text_col].apply(analyze_sentiment)
    df["sentiment_score"] = scores
    df["sentiment_label"] = scores.apply(
        lambda x: "正面" if x > 0.55 else ("负面" if x < 0.45 else "中性")
    )
    return df


def sentiment_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算情感分布统计
    """
    dist = df["sentiment_label"].value_counts(normalize=True).round(4) * 100
    dist = dist.reset_index()
    dist.columns = ["情感类别", "占比(%)"]
    return dist


def sentiment_by_platform(df: pd.DataFrame) -> pd.DataFrame:
    """
    按平台统计情感分布
    """
    return (
        df.groupby(["platform", "sentiment_label"])
        .size()
        .unstack(fill_value=0)
    )


def platform_sentiment_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算各平台正负面评论比例
    """
    result = {}
    for platform in df["platform"].unique():
        sub = df[df["platform"] == platform]
        total = len(sub)
        result[platform] = {
            "正面占比": len(sub[sub["sentiment_label"] == "正面"]) / total * 100,
            "中性占比": len(sub[sub["sentiment_label"] == "中性"]) / total * 100,
            "负面占比": len(sub[sub["sentiment_label"] == "负面"]) / total * 100,
        }
    return pd.DataFrame(result).T.round(2)


# ======================== 主题提取 ========================


def extract_topics(texts: List[str], top_n: int = 30) -> List[Tuple[str, int]]:
    """
    提取高频关键词（基于 TF 统计, 去停用词）

    返回:
        List[Tuple[str, int]]: (词语, 频次) 列表
    """
    # 基础停用词表
    stopwords = set(
        "的 了 在 是 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你 "
        "会 着 没有 看 好 自己 这 他 她 它 们 那 这个 那个 什么 怎么 如何 "
        "为什么 因为 所以 但是 而且 虽然 如果 可以 应该 能 能够 会 可能 "
        "已经 还 又 再 才 就 都 只 被 把 让 对 从 在 到 于 与 和 或 跟 "
        "比 向 为 由 以 及 等 之 所 吧 吗 呀 啊 哦 嗯 哈 啦".split()
    )

    word_count = Counter()
    for text in texts:
        words = jieba.lcut(str(text))
        for word in words:
            word = word.strip()
            if len(word) >= 2 and word not in stopwords:
                word_count[word] += 1

    return word_count.most_common(top_n)


def extract_topics_by_sentiment(
    df: pd.DataFrame, sentiment: str, top_n: int = 20
) -> List[Tuple[str, int]]:
    """
    提取特定情感类别中的高频关键词
    """
    texts = df[df["sentiment_label"] == sentiment]["content"].tolist()
    return extract_topics(texts, top_n)


def keyword_cloud_data(
    df: pd.DataFrame, top_n: int = 100
) -> pd.DataFrame:
    """
    生成词云所需的数据（词语, 频次）
    """
    all_texts = df["content"].dropna().tolist()
    topics = extract_topics(all_texts, top_n)
    return pd.DataFrame(topics, columns=["word", "frequency"])


# ======================== 负面焦点分析 ========================


def negative_focus_analysis(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """
    负面评论高频主题提取

    返回:
        DataFrame: 负面评论核心关键词及其频次
    """
    negative_texts = df[df["sentiment_label"] == "负面"]["content"].tolist()
    topics = extract_topics(negative_texts, top_n)
    return pd.DataFrame(topics, columns=["关键词", "出现频次"])
