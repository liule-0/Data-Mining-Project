"""
============================================================
维度三：短视频舆情主题与情感（文本挖掘）
============================================================
分析功能:
  1. 情感分析：使用 SnowNLP 计算每条评论情感分值（0~1）
     以 0.5 为阈值划分正面/负面
  2. 词频统计 + 词云图（WordCloud）
  3. 主题建模：LDA（5 个主题，iterations=500）

方法:
  - SnowNLP: 基于朴素贝叶斯的短文本情感分类
  - LDA: sklearn.decomposition.LatentDirichletAllocation
  - 词云: wordcloud.WordCloud
============================================================
"""

import pandas as pd
import numpy as np
from collections import Counter
from typing import List, Tuple, Optional

import jieba
import jieba.analyse


# ==================== SnowNLP 情感分析 ====================

def analyze_sentiment_snownlp(text: str) -> float:
    """
    使用 SnowNLP 进行情感分析

    返回:
        float: 0~1 的情感分值，越接近 1 越正面
    """
    try:
        from snownlp import SnowNLP
        s = SnowNLP(str(text))
        return round(s.sentiments, 4)
    except Exception:
        return 0.5


def batch_sentiment_snownlp(df: pd.DataFrame, text_col: str = "content") -> pd.DataFrame:
    """
    批量 SnowNLP 情感分析

    返回:
        DataFrame 新增列:
            - snownlp_score: SnowNLP 情感分值
            - snownlp_label: 正面/负面/中性（阈值 0.5）
    """
    df = df.copy()
    print("  🧠 正在使用 SnowNLP 进行情感分析...")

    # 分批处理显示进度
    scores = []
    total = len(df)
    batch_size = max(1, total // 20)
    for i, text in enumerate(df[text_col]):
        scores.append(analyze_sentiment_snownlp(text))
        if (i + 1) % batch_size == 0:
            print(f"    进度: {i+1}/{total} ({100*(i+1)//total}%)")

    df["snownlp_score"] = scores
    # 以 0.5 为阈值
    df["snownlp_label"] = df["snownlp_score"].apply(
        lambda x: "正面" if x > 0.5 else ("负面" if x < 0.5 else "中性")
    )
    print(f"  ✅ SnowNLP 分析完成！")
    return df


# ==================== LDA 主题建模 ====================

# 基础停用词表（中文高频无意义词）
STOPWORDS = set(
    "的 了 在 是 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你 "
    "会 着 没有 看 好 自己 这 他 她 它 们 那 这个 那个 什么 怎么 如何 "
    "为什么 因为 所以 但是 而且 虽然 如果 可以 应该 能 能够 会 可能 "
    "已经 还 又 再 才 就 都 只 被 把 让 对 从 在 到 于 与 和 或 跟 "
    "比 向 为 由 以 及 等 之 所 吧 吗 呀 啊 哦 嗯 哈 啦 嘛 哎 哟 "
    "的 地 得 着 了 过 不 也 很 太 多 少 是 有 没 够 做 给 来 去 "
    "几 两 些 点 些 多 少 大 小 真 好 坏 新 老 高 低 长 短 远 近 "
    "快 慢 早 晚 先 后 刚 才 就 便 还 再 又 也 都 只 仅 光 单 纯"
    "吧 啊 啦 呀 呢 吗 嘛 嗯 哦 哈 呵 嗨 喂 哟 哎 哼 呸 咯 噜 咚"
    "就是 还是 或是 但是 可是 然而 不过 只是 反正 无论 不管 如果"
    "虽然 因为 所以 于是 然后 接着 最后 终于 开始 起来 下来 上来"
    "出去 进去 过来 回去 起来 开来".split()
)


def preprocess_text(text: str) -> str:
    """
    中文文本预处理：分词、去停用词、过滤短词
    """
    words = jieba.lcut(str(text))
    filtered = [w.strip() for w in words
                if len(w.strip()) >= 2 and w.strip() not in STOPWORDS]
    return " ".join(filtered)


def run_lda_topic_modeling(
    df: pd.DataFrame,
    text_col: str = "content",
    n_topics: int = 5,
    n_iter: int = 500,
    n_top_words: int = 15,
) -> dict:
    """
    LDA 主题建模（使用 sklearn）

    参数:
        n_topics: 主题数量（默认 5）
        n_iter: 迭代次数（默认 500）
        n_top_words: 每个主题显示的关键词数

    返回:
        dict: {
            "model": LDA 模型,
            "vectorizer": CountVectorizer,
            "dtm": 文档-词项矩阵,
            "topics": {主题编号: [(词, 权重), ...]},
            "topic_dist": DataFrame 各文档主题分布,
            "corpus_size": 有效文档数
        }
    """
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.decomposition import LatentDirichletAllocation

    print(f"  📝 正在预处理文本（分词/去停用词）...")
    texts = df[text_col].dropna().tolist()
    processed = [preprocess_text(t) for t in texts]
    # 过滤空文档
    valid_docs = [(t, p) for t, p in zip(texts, processed) if p.strip()]
    print(f"     有效文档: {len(valid_docs)}/{len(texts)}")

    processed_texts = [p for _, p in valid_docs]

    # 构建文档-词项矩阵
    print(f"  🔧 正在构建词项矩阵...")
    vectorizer = CountVectorizer(max_features=2000, min_df=3, max_df=0.85)
    dtm = vectorizer.fit_transform(processed_texts)
    print(f"     词项矩阵: {dtm.shape[0]} 文档 × {dtm.shape[1]} 词项")

    # 训练 LDA
    print(f"  🧠 正在训练 LDA 模型（{n_topics}主题, {n_iter}迭代）...")
    lda = LatentDirichletAllocation(
        n_components=n_topics,
        max_iter=n_iter,
        random_state=42,
        learning_method="batch",
        n_jobs=-1,
    )
    lda.fit(dtm)
    print(f"  ✅ LDA 训练完成！")

    # 提取每个主题的关键词
    feature_names = vectorizer.get_feature_names_out()

    topics = {}
    for topic_idx, topic_weights in enumerate(lda.components_):
        top_word_indices = topic_weights.argsort()[:-n_top_words - 1:-1]
        top_words = [(feature_names[i], round(topic_weights[i], 2))
                     for i in top_word_indices]
        topics[topic_idx] = top_words

    # 文档主题分布
    topic_dist = lda.transform(dtm)
    topic_df = pd.DataFrame(
        topic_dist,
        columns=[f"主题{i+1}_权重" for i in range(n_topics)]
    )

    result = {
        "model": lda,
        "vectorizer": vectorizer,
        "dtm": dtm,
        "topics": topics,
        "topic_dist": topic_df,
        "corpus_size": len(valid_docs),
        "valid_texts": [t for t, _ in valid_docs],
    }
    return result


def get_dominant_topic(topic_dist: pd.DataFrame) -> pd.DataFrame:
    """
    提取每个文档的主导主题
    """
    topic_cols = topic_dist.columns
    dominant = topic_dist.idxmax(axis=1)
    weight = topic_dist.max(axis=1)
    result = pd.DataFrame({
        "主导主题": dominant,
        "主题权重": weight,
    })
    result["主题编号"] = result["主导主题"].str.extract(r"(\d+)").astype(int)
    return result


# ==================== 词频分析 ====================

def word_frequency_analysis(
    texts: List[str],
    top_n: int = 100,
) -> pd.DataFrame:
    """
    词频统计

    返回:
        DataFrame: word, frequency, 排名
    """
    word_count = Counter()
    for text in texts:
        words = jieba.lcut(str(text))
        for w in words:
            w = w.strip()
            if len(w) >= 2 and w not in STOPWORDS:
                word_count[w] += 1

    result = pd.DataFrame(
        word_count.most_common(top_n),
        columns=["word", "frequency"]
    )
    result["rank"] = range(1, len(result) + 1)
    return result


# ==================== 汇总报告 ====================

def full_sentiment_topic_report(df: pd.DataFrame) -> dict:
    """
    运行维度三所有分析，返回汇总结果
    """
    results = {}

    # 1. SnowNLP 情感分析（覆盖原有情感列）
    df = batch_sentiment_snownlp(df)
    results["df"] = df

    # 2. 情感分布
    dist = df["snownlp_label"].value_counts(normalize=True).round(4) * 100
    results["sentiment_dist"] = dist
    print(f"\n  📌 SnowNLP 情感分布:")
    for label, pct in dist.items():
        bar = "█" * int(pct / 3)
        print(f"     {label:4s}: {pct:.1f}% {bar}")

    # 3. 词频统计
    texts = df["content"].dropna().tolist()
    results["word_freq"] = word_frequency_analysis(texts, top_n=100)
    print(f"\n  📌 高频词 TOP 20:")
    for _, row in results["word_freq"].head(20).iterrows():
        print(f"     {row['word']:8s}: {row['frequency']}次")

    # 4. LDA 主题建模
    try:
        lda_results = run_lda_topic_modeling(
            df, n_topics=5, n_iter=500, n_top_words=15
        )
        results["lda"] = lda_results
        print(f"\n  📌 LDA 主题模型（5个主题, 500次迭代）:")
        for topic_id, words in lda_results["topics"].items():
            word_str = ", ".join([f"{w}({s:.1f})" for w, s in words[:8]])
            print(f"     主题{topic_id+1}: {word_str}")
    except Exception as e:
        print(f"\n  ⚠️ LDA 建模失败: {e}")
        results["lda"] = None

    return results
