"""
模拟数据生成器
为重庆市38个区县生成接近真实分布的人口、医疗、舆情模拟数据，
使项目可在无真实数据时端到端运行验证。
"""

import os
import json
import random
import pandas as pd
import numpy as np
from typing import Optional
from src.utils.config_loader import get_config
from src.data.data_preprocessor import region_classify

# 随机种子
random.seed(42)
np.random.seed(42)

# ===================== 重庆市38个区县 =====================

ALL_DISTRICTS = [
    "万州区", "涪陵区", "渝中区", "大渡口区", "江北区", "沙坪坝区",
    "九龙坡区", "南岸区", "北碚区", "綦江区", "大足区", "渝北区",
    "巴南区", "黔江区", "长寿区", "江津区", "合川区", "永川区",
    "南川区", "璧山区", "铜梁区", "潼南区", "荣昌区", "开州区",
    "梁平区", "武隆区", "城口县", "丰都县", "垫江县", "忠县",
    "云阳县", "奉节县", "巫山县", "巫溪县", "石柱县", "秀山县",
    "酉阳县", "彭水县",
]

YEARS = list(range(2016, 2025))

# ===================== 1. 人口模拟数据 =====================

def _base_aging_rate(district: str) -> float:
    """根据区县类型返回基础老龄化率（模拟2024年值）"""
    region = region_classify(district)
    if region == "中心城区":
        # 中心城区 18%-22%
        return random.uniform(0.18, 0.22)
    elif region == "主城新区":
        # 主城新区 22%-28%
        return random.uniform(0.22, 0.28)
    elif region == "渝东北":
        # 渝东北 30%-35%
        return random.uniform(0.30, 0.35)
    elif region == "渝东南":
        # 渝东南 28%-34%
        return random.uniform(0.28, 0.34)
    else:
        return random.uniform(0.22, 0.28)


def _base_population(district: str) -> int:
    """根据区县模拟常住人口（万人）"""
    region = region_classify(district)
    if region == "中心城区":
        return int(random.uniform(60, 220))       # 渝北区最大
    elif region == "主城新区":
        return int(random.uniform(50, 150))
    elif region == "渝东北":
        return int(random.uniform(20, 170))       # 万州区最大
    elif region == "渝东南":
        return int(random.uniform(15, 55))
    else:
        return int(random.uniform(30, 80))


def generate_population_data() -> pd.DataFrame:
    """
    生成 2016-2024 年人口模拟数据

    生成逻辑：
        - 2024年老龄化率按区域类型分布（中心城区低，远郊高）
        - 2016年老龄化率 = 2024年值 - 趋势增量（约 3-7 百分点）
        - 人口逐年微增或微减
    """
    records = []
    for district in ALL_DISTRICTS:
        rate_2024 = _base_aging_rate(district)
        pop_2024 = _base_population(district) * 10000  # 转为人

        for i, year in enumerate(YEARS):
            # 老龄化率线性内插：2016最低，2024最高
            progress = i / (len(YEARS) - 1)  # 0 ~ 1
            rate = rate_2024 - (1 - progress) * random.uniform(0.03, 0.07)

            # 人口随时间小幅波动
            pop = pop_2024 * (1 + random.uniform(-0.02, 0.01) * (len(YEARS) - 1 - i))

            # 衍生各年龄段人口
            elderly_pop = int(pop * rate)
            working_pop = int(pop * random.uniform(0.50, 0.60))
            youth_pop = pop - elderly_pop - working_pop

            records.append({
                "区县": district,
                "年份": year,
                "常住人口": int(pop),
                "户籍人口": int(pop * random.uniform(0.85, 1.05)),
                "65岁及以上人口": elderly_pop,
                "15-64岁人口": int(working_pop),
                "0-14岁人口": int(youth_pop),
            })

    return pd.DataFrame(records)


# ===================== 2. 医疗模拟数据 =====================

def _base_hospitalizations(district: str) -> int:
    """根据区县模拟年住院总人次"""
    region = region_classify(district)
    if region == "中心城区":
        return int(random.uniform(80000, 300000))
    elif region == "主城新区":
        return int(random.uniform(40000, 120000))
    elif region == "渝东北":
        return int(random.uniform(30000, 100000))
    elif region == "渝东南":
        return int(random.uniform(15000, 50000))
    return int(random.uniform(20000, 80000))


def generate_healthcare_data() -> pd.DataFrame:
    """
    生成 2016-2024 年医疗住院模拟数据

    生成逻辑：
        - 老年住院占比从2016到2024上升约5.5百分点
        - 心衰等慢病增长超10倍
        - 其他慢病增长2-8倍
    """
    chronic_diseases = ["心衰", "高血压", "糖尿病", "慢性阻塞性肺疾病", "脑卒中"]
    # 各慢病2016年的基础住院量（占住院总人次比例）
    base_rates = {"心衰": 0.008, "高血压": 0.035, "糖尿病": 0.025,
                  "慢性阻塞性肺疾病": 0.015, "脑卒中": 0.020}
    # 各慢病增长倍数（2016→2024）
    growth_factors = {"心衰": 10.5, "高血压": 3.2, "糖尿病": 4.5,
                      "慢性阻塞性肺疾病": 5.0, "脑卒中": 2.8}

    records = []
    for district in ALL_DISTRICTS:
        total_base = _base_hospitalizations(district)
        for i, year in enumerate(YEARS):
            progress = i / (len(YEARS) - 1)  # 0 ~ 1

            # 总住院人次年增 2%-5%
            total_admissions = int(total_base * (1 + progress * random.uniform(0.08, 0.20)))

            # 老年住院占比：2016年约35%，2024年约40.5%（上升5.5百分点）
            elderly_ratio = 0.35 + progress * 0.055
            elderly_admissions = int(total_admissions * elderly_ratio)

            # 各慢病住院量
            disease_data = {}
            for disease in chronic_diseases:
                base_count = int(total_base * base_rates[disease])
                factor = 1 + progress * (growth_factors[disease] - 1)
                disease_data[f"{disease}_住院量"] = int(base_count * factor)

            records.append({
                "区县": district,
                "年份": year,
                "总住院人次": total_admissions,
                "老年住院人次": elderly_admissions,
                **disease_data,
            })

    return pd.DataFrame(records)


# ===================== 3. 舆情模拟数据 =====================

POSITIVE_TEMPLATES = [
    "老年人是社会的财富，应该多关心他们",
    "社区养老服务越来越好了，点赞",
    "尊老爱幼是传统美德，大家都要学习",
    "老年生活也可以很精彩，活到老学到老",
    "退休后参加老年大学，感觉生活充实多了",
    "感谢政府对老年人的关怀和照顾",
    "老年人经验丰富，是年轻人的好老师",
    "小区新安装了老年健身器材，方便多了",
    "老年志愿者真了不起，值得尊敬",
    "养老金年年涨，生活有保障",
    "社区食堂对老年人优惠，真的很贴心",
    "老年人也要与时俱进，学会用智能手机",
    "老年舞蹈队跳得真好看，充满活力",
    "陪着父母去旅游，他们开心极了",
    "老年公交卡真方便，出行无忧",
]

NEGATIVE_TEMPLATES = [
    "叫120等了40分钟才到，急救反应太慢了",
    "直播坑老人买保健品，太可恶了",
    "养老院条件太差了，费用还死贵",
    "去大医院排队排到心塞，老年人体力吃不消",
    "老年人在家摔倒没人知道怎么办",
    "农村老人看病太难了，要走几十里路",
    "养老金根本不够用，物价涨得太快",
    "社区没有老年活动场所，天天在家发呆",
    "骗子专门盯着老年人骗，防不胜防",
    "医院对老年人没有专门的照顾窗口",
    "子女都在外地打工，老人独居太可怜",
    "老年痴呆走失了警察也找不到",
    "很多公园没有无障碍通道，轮椅过不去",
    "买药太贵了，慢性病吃药一年花好几万",
    "直播带货卖假货给老人，没人管管吗",
]

NEUTRAL_TEMPLATES = [
    "老龄化是社会发展的必然趋势",
    "重庆的老龄化程度在全国处于什么水平",
    "不知道未来养老政策会怎么调整",
    "听说日本老龄化更严重，可以学习经验",
    "延迟退休政策对老年人有什么影响",
    "养老模式到底是居家好还是去养老院好",
    "每个家庭都会面临养老问题",
    "人口结构变化会影响经济发展",
    "老年产业应该是个新风口",
    "养老基金还够不够用啊",
]


def generate_sentiment_data(total_comments: int = 3500) -> pd.DataFrame:
    """
    生成短视频评论模拟数据

    生成逻辑：
        - 正面 58%，中性 22%，负面 20%
        - 抖音/快手各约一半
        - 负面评论集中于急救响应、"直播坑老"
    """
    # 语气词/修饰词池（用于增加文本多样性）
    MODIFIERS = [
        "真的", "确实", "实在", "简直", "非常", "特别",
        "太", "有点", "有些", "感觉", "希望", "建议",
    ]
    SUFFIXES = ["", "", "", "", "！", "。", "…", "😔", "👍", "🙏", "🤔", "💪"]

    records = []
    platforms = ["douyin", "kuaishou"]

    for i in range(total_comments):
        platform = random.choice(platforms)

        # 情感分配
        r = random.random()
        if r < 0.58:
            label = "正面"
            template = random.choice(POSITIVE_TEMPLATES)
            score = random.uniform(0.55, 0.95)
        elif r < 0.80:
            label = "中性"
            template = random.choice(NEUTRAL_TEMPLATES)
            score = random.uniform(0.25, 0.55)
        else:
            label = "负面"
            template = random.choice(NEGATIVE_TEMPLATES)
            score = random.uniform(0.01, 0.20)

        # 增加文本多样性：随机插入修饰词或后缀
        content = template
        if random.random() < 0.4:
            modifier = random.choice(MODIFIERS)
            content = modifier + content
        suffix = random.choice(SUFFIXES)
        if suffix:
            content += suffix

        records.append({
            "id": i + 1,
            "platform": platform,
            "content": content,
            "sentiment_score": round(score, 4),
            "sentiment_label": label,
            "likes": int(np.random.pareto(2) * 10) + 1,
            "time": pd.Timestamp(f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}"),
        })

    return pd.DataFrame(records)


# ===================== 4. 重庆 GeoJSON 模拟 =====================

# 重庆市各区县近似中心坐标（经纬度）
DISTRICT_COORDS = {
    "渝中区": [29.55, 106.57], "大渡口区": [29.48, 106.48],
    "江北区": [29.60, 106.57], "沙坪坝区": [29.54, 106.45],
    "九龙坡区": [29.50, 106.51], "南岸区": [29.52, 106.57],
    "北碚区": [29.80, 106.40], "綦江区": [29.03, 106.65],
    "大足区": [29.70, 105.72], "渝北区": [29.72, 106.63],
    "巴南区": [29.38, 106.54], "黔江区": [29.53, 108.77],
    "长寿区": [29.83, 107.07], "江津区": [29.29, 106.26],
    "合川区": [30.00, 106.27], "永川区": [29.36, 105.89],
    "南川区": [29.16, 107.10], "璧山区": [29.59, 106.23],
    "铜梁区": [29.84, 106.06], "潼南区": [30.19, 105.84],
    "荣昌区": [29.40, 105.60], "开州区": [31.18, 108.41],
    "梁平区": [30.67, 107.79], "武隆区": [29.33, 107.75],
    "城口县": [31.95, 108.66], "丰都县": [29.86, 107.73],
    "垫江县": [30.33, 107.34], "忠县": [30.29, 108.04],
    "云阳县": [30.93, 108.70], "奉节县": [31.02, 109.46],
    "巫山县": [31.08, 109.88], "巫溪县": [31.40, 109.63],
    "石柱县": [29.99, 108.11], "秀山县": [28.45, 109.01],
    "酉阳县": [28.84, 108.77], "彭水县": [29.29, 108.17],
    "涪陵区": [29.71, 107.39], "万州区": [30.81, 108.38],
}


def _generate_square_polygon(center_lat: float, center_lng: float,
                              size: float = 0.15) -> dict:
    """以中心坐标生成一个近似方形多边形（替代真实边界）"""
    half = size / 2
    coords = [
        [center_lng - half, center_lat - half],
        [center_lng + half, center_lat - half],
        [center_lng + half, center_lat + half],
        [center_lng - half, center_lat + half],
        [center_lng - half, center_lat - half],
    ]
    return {"type": "Polygon", "coordinates": [coords]}


def generate_geojson(output_path: Optional[str] = None) -> dict:
    """
    生成重庆市38个区县的 GeoJSON（近似多边形）
    若未提供路径，返回 dict；否则写入文件
    """
    features = []
    for district in ALL_DISTRICTS:
        coords = DISTRICT_COORDS.get(district, [29.5, 107.5])

        # 不同区域使用不同大小的多边形（模拟区县面积差异）
        region = region_classify(district)
        size_map = {"中心城区": 0.08, "主城新区": 0.14, "渝东北": 0.18, "渝东南": 0.16}
        size = size_map.get(region, 0.12)

        features.append({
            "type": "Feature",
            "properties": {"区县": district, "区域": region},
            "geometry": _generate_square_polygon(coords[0], coords[1], size),
        })

    geojson = {"type": "FeatureCollection", "features": features}

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        print(f"GeoJSON 已保存: {output_path}")

    return geojson


# ===================== 5. 一键生成所有模拟数据 =====================

def generate_all_sample_data(force: bool = False):
    """
    生成所有模拟数据并写入 data/raw/ 和 data/geo/

    参数:
        force: 是否覆盖已存在的文件
    """
    config = get_config()
    root = config["paths"]["root"]

    def should_write(path):
        if force:
            return True
        return not os.path.exists(path)

    # --- 人口数据 ---
    pop_path = os.path.join(root, "data/raw/population/cq_population_2016_2024.xlsx")
    if should_write(pop_path):
        df_pop = generate_population_data()
        os.makedirs(os.path.dirname(pop_path), exist_ok=True)
        df_pop.to_excel(pop_path, index=False, engine="openpyxl")
        print(f"✅ 人口模拟数据已生成: {pop_path} ({len(df_pop)} 行)")
    else:
        print(f"⏭️  人口数据已存在: {pop_path}")

    # --- 医疗数据 ---
    med_path = os.path.join(root, "data/raw/healthcare/cq_hospitalization_2016_2024.xlsx")
    if should_write(med_path):
        df_med = generate_healthcare_data()
        os.makedirs(os.path.dirname(med_path), exist_ok=True)
        df_med.to_excel(med_path, index=False, engine="openpyxl")
        print(f"✅ 医疗模拟数据已生成: {med_path} ({len(df_med)} 行)")
    else:
        print(f"⏭️  医疗数据已存在: {med_path}")

    # --- 舆情数据 ---
    for platform in ["douyin", "kuaishou"]:
        sent_path = os.path.join(root, f"data/raw/sentiment/{platform}_comments.csv")
        if should_write(sent_path):
            total = 2000 if platform == "douyin" else 1500
            df_sent = generate_sentiment_data(total)
            df_sent["platform"] = platform
            os.makedirs(os.path.dirname(sent_path), exist_ok=True)
            df_sent.to_csv(sent_path, index=False, encoding="utf-8-sig")
            print(f"✅ {platform} 评论模拟数据已生成: {sent_path} ({len(df_sent)} 条)")
        else:
            print(f"⏭️  {platform} 数据已存在: {sent_path}")

    # --- GeoJSON ---
    geo_path = os.path.join(root, "data/geo/chongqing_districts.geojson")
    if should_write(geo_path):
        generate_geojson(geo_path)
    else:
        print(f"⏭️  GeoJSON 已存在: {geo_path}")

    print("\n🎉 所有模拟数据生成完毕！")


if __name__ == "__main__":
    generate_all_sample_data(force=True)
