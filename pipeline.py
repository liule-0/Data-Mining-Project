"""
============================================================
主流程脚本 — 重庆人口老龄化与医疗压力数据挖掘
============================================================
运行方式:
    python pipeline.py --step all            # 全流程
    python pipeline.py --step population     # 仅人口分析
    python pipeline.py --step healthcare     # 仅医疗分析
    python pipeline.py --step healthcare-evolution  # 医疗压力演变（维度二）
    python pipeline.py --step sentiment      # 仅舆情分析（原jionlp）
    python pipeline.py --step sentiment-topic  # 舆情主题情感挖掘（SnowNLP+LDA+词云）
    python pipeline.py --step spatial        # 仅空间分布分析（一区两群/城乡/抚养比）
    python pipeline.py --step heatmap        # 仅热力图
    python pipeline.py --step map            # 仅综合地图（老龄化+医疗+养老+便民）
    python pipeline.py --step synthesized    # 仅合成总和地图（老龄化×医疗×便民 综合压力指数）
    python pipeline.py --step report         # 仅报告
    python pipeline.py --demo                # 生成模拟数据并全流程运行
============================================================
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np

from src.utils.config_loader import get_config, ensure_dirs


# ======================== 人口结构分析 ========================

def run_population_analysis(save_figures: bool = True):
    """📊 人口结构分析：趋势、区域对比、增速排名"""
    from src.data.data_loader import load_population_data
    from src.data.data_preprocessor import clean_population_data, compute_aging_rate, region_classify
    from src.analysis.population_analysis import aging_rate_trend, regional_aging_comparison, aging_speed_analysis
    from src.visualization.charts import plot_aging_trend, plot_aging_regional_comparison

    config = get_config()
    fig_dir = config["paths"]["output_figures"]
    tab_dir = config["paths"]["output_tables"]

    print("=" * 60)
    print("📊 [1/5] 人口结构分析")
    print("=" * 60)

    # 加载并清洗
    df = load_population_data()
    df = clean_population_data(df)
    df = compute_aging_rate(df)
    print(f"  数据加载完成: {len(df)} 行, {df['区县'].nunique()} 个区县")

    # 1. 老龄化率趋势
    trend = aging_rate_trend(df)
    print(f"\n  ▶ 各区县老龄化率趋势（部分）:")
    print(trend.head(5).to_string())

    if save_figures:
        os.makedirs(f"{fig_dir}/population", exist_ok=True)
        plot_aging_trend(trend, save_path=f"{fig_dir}/population/aging_trend.png")

    # 2. 区域对比
    df["区域"] = df["区县"].apply(region_classify)
    regional = regional_aging_comparison(df)
    print(f"\n  ▶ 四大区域老龄化对比:")
    print(regional.to_string())

    if save_figures:
        plot_aging_regional_comparison(regional,
            save_path=f"{fig_dir}/population/aging_region_comparison.png")

    # 3. 增速排名
    speed = aging_speed_analysis(df)
    print(f"\n  ▶ 老龄化增速 TOP 10:")
    print(speed.head(10).to_string())

    os.makedirs(tab_dir, exist_ok=True)
    speed.to_csv(f"{tab_dir}/aging_speed_ranking.csv", encoding="utf-8-sig")
    print(f"\n  ✅ 增速排名已保存: {tab_dir}/aging_speed_ranking.csv")

    # 4. 核心指标输出
    print(f"\n  🔑 核心发现:")
    print(f"     2024年全市平均老龄化率: {trend[2024].mean():.1%}")
    print(f"     老龄化率最高区县: {trend[2024].idxmax()} ({trend[2024].max():.1%})")
    print(f"     老龄化率最低区县: {trend[2024].idxmin()} ({trend[2024].min():.1%})")

    return df


# ======================== 医疗压力分析 ========================

def run_healthcare_analysis(save_figures: bool = True):
    """🏥 医疗压力分析：老年住院趋势、慢病增长、疾病谱演变"""
    from src.data.data_loader import load_healthcare_data
    from src.data.data_preprocessor import clean_healthcare_data
    from src.analysis.healthcare_analysis import (
        elderly_hospitalization_trend, chronic_disease_trend,
        disease_structure_change,
    )
    from src.visualization.charts import (
        plot_elderly_hospitalization_trend, plot_chronic_disease_growth,
    )

    config = get_config()
    fig_dir = config["paths"]["output_figures"]
    tab_dir = config["paths"]["output_tables"]

    print("=" * 60)
    print("🏥 [2/5] 医疗压力分析")
    print("=" * 60)

    df = load_healthcare_data()
    df = clean_healthcare_data(df)
    print(f"  数据加载完成: {len(df)} 行")

    # 1. 老年住院占比趋势
    elderly_trend = elderly_hospitalization_trend(df)
    print(f"\n  ▶ 老年住院占比年度趋势:")
    print(elderly_trend.to_string())

    rise = (elderly_trend.loc[2024, "mean"] - elderly_trend.loc[2016, "mean"]) * 100
    print(f"   ⏫ 2016-2024 上升: {rise:.1f} 百分点")

    if save_figures:
        os.makedirs(f"{fig_dir}/healthcare", exist_ok=True)
        plot_elderly_hospitalization_trend(elderly_trend,
            save_path=f"{fig_dir}/healthcare/elderly_hospitalization_trend.png")

    # 2. 慢病住院量变化
    chronic = chronic_disease_trend(df)
    print(f"\n  ▶ 主要慢病住院量变化:")
    print(chronic[[c for c in chronic.columns if "增长倍数" in c]].to_string())

    if save_figures:
        plot_chronic_disease_growth(chronic,
            save_path=f"{fig_dir}/healthcare/chronic_disease_growth.png")

    # 3. 疾病谱演变
    change = disease_structure_change(df, 2016, 2024)
    print(f"\n  ▶ 疾病谱变化 TOP 5:")
    print(change.head(5).to_string())

    change.to_csv(f"{tab_dir}/disease_structure_change.csv", encoding="utf-8-sig")

    return df


# ======================== 医疗压力演变趋势 ========================

def run_healthcare_evolution():
    """📈 维度二：医疗压力演变趋势（时间序列+疾病谱分析）"""
    from src.data.data_loader import load_healthcare_data
    from src.data.data_preprocessor import clean_healthcare_data
    from src.analysis.healthcare_evolution import full_healthcare_evolution_report
    from src.visualization.healthcare_evolution_charts import (
        plot_elderly_hospitalization_with_growth,
        plot_disease_spectrum_stacked_area,
        plot_disease_growth_multi_line,
        plot_hospitalization_growth_comparison,
    )

    config = get_config()
    fig_dir = config["paths"]["output_figures"]
    tab_dir = config["paths"]["output_tables"]
    evo_dir = f"{fig_dir}/healthcare_evolution"
    os.makedirs(evo_dir, exist_ok=True)

    print("=" * 60)
    print("📈 [维度二] 医疗压力演变趋势")
    print("=" * 60)

    df = load_healthcare_data()
    df = clean_healthcare_data(df)
    print(f"  数据加载完成: {len(df)} 行, {df['区县'].nunique()} 个区县")

    # 1. 全量分析报告
    results = full_healthcare_evolution_report(df)

    # 2. 老年住院占比趋势+年增长率
    plot_elderly_hospitalization_with_growth(df, save_path=f"{evo_dir}/elderly_hosp_trend.png")

    # 3. 疾病谱堆叠面积图
    plot_disease_spectrum_stacked_area(df, save_path=f"{evo_dir}/disease_spectrum.png")

    # 4. 慢病增长倍数折线图
    plot_disease_growth_multi_line(df, save_path=f"{evo_dir}/disease_growth.png")

    # 5. 住院增长率对比图
    plot_hospitalization_growth_comparison(df, save_path=f"{evo_dir}/hosp_growth_comparison.png")

    # 6. 保存数据表
    results["elderly_trend"].to_csv(f"{tab_dir}/elderly_hosp_trend.csv", encoding="utf-8-sig")
    results["spectrum"].to_csv(f"{tab_dir}/disease_spectrum.csv", encoding="utf-8-sig")

    print(f"\n  ✅ 所有医疗演变图表已保存至 {evo_dir}/")
    print(f"  ✅ 数据表已保存至 {tab_dir}/")

    return results


# ======================== 舆情情感分析 ========================

def run_sentiment_analysis(save_figures: bool = True):
    """💬 舆情情感分析：情感分布、负面焦点、词云"""
    from src.data.data_loader import load_sentiment_data
    from src.data.data_preprocessor import clean_sentiment_data
    from src.analysis.sentiment_analysis import (
        batch_sentiment_analysis, sentiment_distribution,
        platform_sentiment_ratio, negative_focus_analysis,
        keyword_cloud_data,
    )
    from src.visualization.charts import plot_sentiment_distribution, plot_negative_keywords
    from src.visualization.wordcloud_gen import generate_wordcloud

    config = get_config()
    fig_dir = config["paths"]["output_figures"]
    tab_dir = config["paths"]["output_tables"]

    print("=" * 60)
    print("💬 [3/5] 舆情情感分析")
    print("=" * 60)

    df = load_sentiment_data()
    df = clean_sentiment_data(df)
    print(f"  评论数据加载完成: {len(df)} 条")

    # 批量情感分析
    df = batch_sentiment_analysis(df)
    print(f"  情感分析完成")

    # 1. 情感分布
    dist = sentiment_distribution(df)
    print(f"\n  ▶ 情感分布:")
    print(dist.to_string())

    if save_figures:
        os.makedirs(f"{fig_dir}/sentiment", exist_ok=True)
        plot_sentiment_distribution(df,
            save_path=f"{fig_dir}/sentiment/sentiment_distribution.png")

    # 2. 平台对比
    ratio = platform_sentiment_ratio(df)
    print(f"\n  ▶ 各平台情感比例:")
    print(ratio.to_string())

    ratio.to_csv(f"{tab_dir}/platform_sentiment_ratio.csv", encoding="utf-8-sig")

    # 3. 负面焦点
    negative = negative_focus_analysis(df, top_n=15)
    print(f"\n  ▶ 负面评论高频关键词 TOP 15:")
    print(negative.to_string())

    if save_figures:
        plot_negative_keywords(negative,
            save_path=f"{fig_dir}/sentiment/negative_keywords.png")

    # 4. 词云
    cloud_data = keyword_cloud_data(df, top_n=100)
    if save_figures:
        generate_wordcloud(cloud_data,
            save_path=f"{fig_dir}/sentiment/wordcloud_all.png",
            title="老龄化话题评论关键词词云")

    positive_ratio = dist[dist["情感类别"] == "正面"]["占比(%)"].values[0]
    print(f"\n  🔑 核心发现:")
    print(f"     正面评论占比: {positive_ratio:.1f}%")
    print(f"     负面焦点: 急救响应、直播坑老、养老诈骗")

    return df


# ======================== 舆情主题情感挖掘 ========================

def run_sentiment_topic():
    """💬 维度三：短视频舆情主题与情感（SnowNLP + LDA + 词云）"""
    from src.data.data_loader import load_sentiment_data
    from src.data.data_preprocessor import clean_sentiment_data
    from src.analysis.sentiment_topic import full_sentiment_topic_report
    from src.visualization.sentiment_topic_charts import (
        plot_snownlp_distribution, plot_lda_topics_horizontal,
        plot_lda_topic_wordcloud, plot_lda_dominant_distribution,
        plot_word_frequency, plot_platform_sentiment,
    )
    from src.visualization.wordcloud_gen import generate_wordcloud

    config = get_config()
    fig_dir = config["paths"]["output_figures"]
    tab_dir = config["paths"]["output_tables"]
    topic_dir = f"{fig_dir}/sentiment_topic"
    os.makedirs(topic_dir, exist_ok=True)

    print("=" * 60)
    print("💬 [维度三] 短视频舆情主题与情感挖掘")
    print("=" * 60)

    df = load_sentiment_data()
    df = clean_sentiment_data(df)
    print(f"  评论数据加载完成: {len(df)} 条")

    results = full_sentiment_topic_report(df)
    df = results["df"]

    # 1. SnowNLP 情感分布图
    plot_snownlp_distribution(df, save_path=f"{topic_dir}/snownlp_distribution.png")

    # 2. 高频词图
    plot_word_frequency(results["word_freq"], top_n=30,
                        save_path=f"{topic_dir}/word_frequency.png")

    # 3. 词云
    generate_wordcloud(results["word_freq"],
                       save_path=f"{topic_dir}/wordcloud_snownlp.png",
                       title="评论关键词词云")

    # 4. LDA 主题关键词图
    if results["lda"]:
        plot_lda_topics_horizontal(results["lda"],
                                   save_path=f"{topic_dir}/lda_topics.png")
        plot_lda_topic_wordcloud(results["lda"],
                                 save_path_pattern=f"{topic_dir}/lda_topic_{{}}.png")
        plot_lda_dominant_distribution(results["lda"], df["snownlp_label"],
                                       save_path=f"{topic_dir}/lda_sentiment_by_topic.png")

    # 5. 平台对比
    plot_platform_sentiment(df, save_path=f"{topic_dir}/platform_sentiment.png")

    # 6. 保存数据
    results["word_freq"].to_csv(f"{tab_dir}/word_frequency.csv",
                                 index=False, encoding="utf-8-sig")

    print(f"\n  ✅ 所有舆情主题图表已保存至 {topic_dir}/")
    print(f"  ✅ 数据表已保存至 {tab_dir}/")

    return results


# ======================== 交互式热力图 ========================

def run_heatmap(save_figures: bool = True):
    """🗺️ 交互式老龄化热力图（Folium + GeoJSON）"""
    from src.visualization.aging_heatmap import create_aging_heatmap, create_aging_change_map

    config = get_config()
    geo_path = os.path.join(config["paths"]["root"],
                            config["data_sources"]["geo"][0]["file"])
    heatmap_dir = f"{config['paths']['output_figures']}/heatmap"
    os.makedirs(heatmap_dir, exist_ok=True)

    print("=" * 60)
    print("🗺️ [4/5] 交互式老龄化热力图")
    print("=" * 60)

    # 尝试加载地理数据（geopandas或json）
    try:
        import geopandas as gpd
        gdf = gpd.read_file(geo_path, encoding="utf-8")
        print(f"  地理数据加载完成 (GeoPandas): {len(gdf)} 个区县")
        _has_geo = True
    except ImportError:
        import json
        with open(geo_path, "r", encoding="utf-8") as f:
            geo_json = json.load(f)
        districts = [f["properties"]["区县"] for f in geo_json["features"]]
        print(f"  地理数据加载完成 (JSON): {len(districts)} 个区县")
        gdf = None
        _has_geo = False

    # 加载人口数据并计算老龄化率
    from src.data.data_loader import load_population_data
    from src.data.data_preprocessor import clean_population_data, compute_aging_rate
    df_pop = load_population_data()
    df_pop = clean_population_data(df_pop)
    df_pop = compute_aging_rate(df_pop)

    if _has_geo:
        # 合并到地理数据
        for year in [2016, 2020, 2024]:
            year_data = df_pop[df_pop["年份"] == year][["区县", "老龄化率"]]
            gdf = gdf.merge(year_data, on="区县", how="left")
            gdf = gdf.rename(columns={"老龄化率": f"老龄化率_{year}"})

        # 计算增幅
        gdf["老龄化增幅"] = gdf["老龄化率_2024"] - gdf["老龄化率_2016"]
        gdf["老龄化率"] = gdf["老龄化率_2024"]  # 默认显示2024年

        print(f"\n  ▶ 2024年老龄化率范围: {gdf['老龄化率'].min():.1%} ~ {gdf['老龄化率'].max():.1%}")
        print(f"   ▶ 2016-2024增幅范围: {gdf['老龄化增幅'].min():.1%} ~ {gdf['老龄化增幅'].max():.1%}")

        heatmap_data = gdf
    else:
        # 使用普通DataFrame方式
        pivot = df_pop.pivot_table(index="区县", columns="年份", values="老龄化率", aggfunc="mean")
        pivot["老龄化率"] = pivot[2024]
        pivot["老龄化增幅"] = pivot[2024] - pivot[2016]
        heatmap_data = pivot.reset_index()[["区县", "老龄化率", "老龄化增幅"]].copy()

        print(f"\n  ▶ 2024年老龄化率范围: {heatmap_data['老龄化率'].min():.1%} ~ {heatmap_data['老龄化率'].max():.1%}")
        print(f"   ▶ 2016-2024增幅范围: {heatmap_data['老龄化增幅'].min():.1%} ~ {heatmap_data['老龄化增幅'].max():.1%}")

    # 生成2024年热力图
    html_path = f"{heatmap_dir}/aging_heatmap_2024.html"
    create_aging_heatmap(heatmap_data, value_col="老龄化率", year=2024, output_path=html_path)

    # 生成变化图
    change_html = f"{heatmap_dir}/aging_change_2016_2024.html"
    create_aging_change_map(heatmap_data, change_col="老龄化增幅", period="2016-2024", output_path=change_html)

    print(f"\n  ✅ 热力图已生成:")
    print(f"     老龄化分布: {html_path}")
    print(f"     变化幅度:   {change_html}")

    return heatmap_data


# ======================== 综合报告 ========================

def run_report():
    """📄 12页综合数据分析报告生成"""
    from src.visualization.report_generator import build_full_report

    config = get_config()

    print("=" * 60)
    print("📄 [5/5] 12页分析报告生成")
    print("=" * 60)

    fig_dir = config["paths"]["output_figures"]
    report = build_full_report(image_dir=fig_dir)
    output_path = report.generate_html()

    print(f"\n  ✅ 报告已生成:")
    print(f"     {output_path}")

    return output_path


# ======================== 综合地图 ========================

def run_combined_map():
    """🗺️ 综合地图：老龄化热力 + 医疗机构 + 养老机构 + 便民服务"""
    from src.visualization.combined_map import create_combined_map

    config = get_config()

    print("=" * 60)
    print("🗺️ [6/6] 多图层综合地图生成")
    print("=" * 60)

    output_path = os.path.join(
        config["paths"]["output_figures"], "heatmap", "combined_map.html"
    )
    create_combined_map(output_path=output_path, aging_year=2024, show_poi_labels=True)

    print(f"\n  ✅ 综合地图已生成:")
    print(f"     {output_path}")

    return output_path


# ======================== 合成总和地图 ========================

def run_synthesized_map():
    """🗺️ 总和地图：老龄化×医疗资源×便民服务 综合压力指数"""
    from src.visualization.synthesized_map import create_synthesized_map

    config = get_config()

    print("=" * 60)
    print("🗺️ [7/7] 合成总和地图（老龄化+医疗+便民）")
    print("=" * 60)

    output_path = os.path.join(
        config["paths"]["output_figures"], "heatmap", "synthesized_map.html"
    )
    create_synthesized_map(output_path=output_path, aging_year=2024)

    print(f"\n  ✅ 总和地图已生成:")
    print(f"     {output_path}")

    return output_path


# ======================== 空间分布分析 ========================

def run_spatial_analysis():
    """🗺️ 维度一：老龄化空间分布分析（一区两群/城乡对比/抚养比/主城内部）"""
    from src.data.data_loader import load_population_data
    from src.data.data_preprocessor import clean_population_data
    from src.analysis.spatial_analysis import full_spatial_report, compute_aging_rates
    from src.visualization.spatial_charts import (
        plot_aging_ranking, plot_urban_remote_comparison,
        plot_yiqu_comparison, plot_dependency_ratio, plot_urban_internal,
    )

    config = get_config()
    fig_dir = config["paths"]["output_figures"]
    tab_dir = config["paths"]["output_tables"]
    spatial_dir = f"{fig_dir}/spatial"
    os.makedirs(spatial_dir, exist_ok=True)

    print("=" * 60)
    print("🗺️ [维度一] 老龄化空间分布（时空分析）")
    print("=" * 60)

    df = load_population_data()
    df = clean_population_data(df)
    df = compute_aging_rates(df)
    print(f"  数据加载完成: {len(df)} 行, {df['区县'].nunique()} 个区县")

    # 1. 全量分析报告
    results = full_spatial_report(df, year=2024)

    # 2. 各区县排名图
    plot_aging_ranking(df, save_path=f"{spatial_dir}/aging_ranking.png")

    # 3. 城乡对比趋势图
    plot_urban_remote_comparison(df, save_path=f"{spatial_dir}/urban_remote_trend.png")

    # 4. 一区两群对比图
    plot_yiqu_comparison(df, save_path=f"{spatial_dir}/yiqu_comparison.png")

    # 5. 老年抚养比对比图
    plot_dependency_ratio(df, save_path=f"{spatial_dir}/dependency_ratio.png")

    # 6. 主城内部差异图
    plot_urban_internal(df, save_path=f"{spatial_dir}/urban_internal.png")

    # 7. 保存CSV
    results["ranking"].to_csv(f"{tab_dir}/aging_rate_ranking.csv",
                               index=False, encoding="utf-8-sig")
    ui = results["urban_internal"]
    ui.to_csv(f"{tab_dir}/urban_internal_comparison.csv",
              encoding="utf-8-sig")

    print(f"\n  ✅ 所有空间分析图表已保存至 {spatial_dir}/")
    print(f"  ✅ 数据表已保存至 {tab_dir}/")

    return results


# ======================== 网络爬虫步骤 ========================

def run_crawl(
    platform: str = "statistics",
    download_pdfs: bool = False,
    use_fallback: bool = True,
    browser: str = "edge",
):
    """
    🌐 运行网络爬虫采集数据

    参数:
        platform:
            "statistics" - 统计局人口数据（年鉴链接+统计公报）
            "healthcare" - 卫健委医疗数据（年度资料+PDF链接）
            "sentiment"  - 短视频舆情数据（抖音/快手Selenium爬虫）
            "all"        - 全部运行
        download_pdfs: 是否下载PDF年鉴（文件较大，默认否）
        use_fallback: 舆情爬取失败时是否使用模拟数据回退
        browser: "edge" | "chrome"，默认 edge（适配微软驱动）
    """
    config = get_config()
    print("=" * 60)
    print("🌐 [0/5] 网络数据采集")
    print("=" * 60)

    from src.utils.config_loader import ensure_dirs
    ensure_dirs(config)

    # ----- 统计局数据 -----
    if platform in ("all", "statistics"):
        print("\n📊 >> 重庆市统计局数据爬取...")
        from src.crawler.crawl_statistics_bureau import run_crawler as run_stat_crawler
        result = run_stat_crawler(
            download_pdfs=download_pdfs,
            save_links=True,
            save_bulletins=True,
        )
        yearbook_count = len(result.get("yearbooks", []))
        bulletin_count = len(result.get("bulletins", []))
        print(f"    ✅ 统计局: {yearbook_count} 年年鉴链接, {bulletin_count} 篇公报\n")

    # ----- 卫健委数据 -----
    if platform in ("all", "healthcare"):
        print("\n🏥 >> 重庆市卫健委数据爬取...")
        from src.crawler.crawl_health_commission import run_crawler as run_health_crawler
        result = run_health_crawler(download_pdfs=download_pdfs)
        pages = len(result.get("pages", []))
        attachments = len(result.get("attachments", []))
        print(f"    ✅ 卫健委: {pages} 个年度资料页面, {attachments} 个PDF附件\n")

    # ----- 舆情数据 -----
    if platform in ("all", "sentiment"):
        print("\n💬 >> 短视频舆情数据爬取...")
        from src.crawler.crawl_short_video import run_crawler as run_sentiment_crawler
        result = run_sentiment_crawler(
            platform="all",
            headless=True,
            browser=browser,
            use_fallback=use_fallback,
        )
        total = sum(len(v) for v in result.values())
        print(f"    ✅ 舆情: 共获取 {total} 条评论数据\n")

    print("=" * 60)
    print("✅ 网络数据采集完成！")
    print("=" * 60)


# ======================== 主入口 ========================

def main():
    parser = argparse.ArgumentParser(description="重庆人口老龄化与医疗压力数据挖掘")
    parser.add_argument("--step", choices=["all", "population", "healthcare",
                                            "healthcare-evolution", "sentiment", "sentiment-topic", "spatial", "heatmap", "map", "synthesized", "report"],
                        default="all", help="执行步骤（默认: all）")
    parser.add_argument("--demo", action="store_true",
                        help="生成模拟数据并运行全流程")
    parser.add_argument("--crawl", choices=["statistics", "healthcare",
                                             "sentiment", "all"],
                        nargs="?", const="all",
                        help="运行网络爬虫采集数据（可选: statistics/healthcare/sentiment/all）")
    parser.add_argument("--crawl-only", action="store_true",
                        help="仅运行爬虫，不执行分析步骤（等同于 --step无参数）")
    parser.add_argument("--platform", choices=["statistics", "healthcare",
                                                "sentiment", "all"],
                        default="all",
                        help="爬虫目标平台（配合 --crawl 使用，默认 all）")
    parser.add_argument("--download-pdfs", action="store_true",
                        help="下载PDF年鉴附件（文件较大，配合 --crawl 使用）")
    parser.add_argument("--browser", choices=["edge", "chrome"],
                        default="edge",
                        help="Selenium浏览器驱动: edge(微软) 或 chrome（配合 --crawl sentiment 使用）")
    parser.add_argument("--no-fallback", action="store_true",
                        help="舆情爬取失败时不使用模拟数据回退")
    args = parser.parse_args()

    config = get_config()
    ensure_dirs(config)
    print(f"\n🔧 项目: {config['project']['name']}")
    print(f"📁 根目录: {config['paths']['root']}\n")

    # 如果要运行爬虫
    if args.crawl is not None:
        run_crawl(
            platform=args.platform if args.crawl == "all" else args.crawl,
            download_pdfs=args.download_pdfs,
            use_fallback=not args.no_fallback,
            browser=args.browser,
        )
        # 仅爬取不分析
        if args.crawl_only:
            return

    # 如果要生成模拟数据
    if args.demo:
        from src.data.sample_data_generator import generate_all_sample_data
        generate_all_sample_data(force=True)
        print("\n🔄 模拟数据已生成，继续执行全流程分析...\n")
        args.step = "all"

    # 步骤执行
    step_map = {
        "population": lambda: run_population_analysis(),
        "healthcare": lambda: run_healthcare_analysis(),
        "healthcare-evolution": lambda: run_healthcare_evolution(),
        "sentiment": lambda: run_sentiment_analysis(),
        "sentiment-topic": lambda: run_sentiment_topic(),
        "spatial":   lambda: run_spatial_analysis(),
        "heatmap":   lambda: run_heatmap(),
        "map":       lambda: run_combined_map(),
        "synthesized": lambda: run_synthesized_map(),
        "report":    lambda: run_report(),
    }

    if args.step == "all":
        run_spatial_analysis()
        print()
        run_healthcare_evolution()
        print()
        run_sentiment_topic()
        print()
        run_population_analysis()
        print()
        run_healthcare_analysis()
        print()
        run_sentiment_analysis()
        print()
        run_heatmap()
        print()
        run_combined_map()
        print()
        run_synthesized_map()
        print()
        run_report()
        print("\n" + "=" * 60)
        print("🎉 全流程执行完成！所有图表和报告已生成。")
        print("=" * 60)
    else:
        step_map[args.step]()
        print(f"\n✅ 步骤 '{args.step}' 执行完成！")


if __name__ == "__main__":
    main()
