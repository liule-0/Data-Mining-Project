"""
============================================================
综合可视化地图 — 老龄化人口 · 医疗机构 · 养老机构 · 便民服务
============================================================
功能:
  生成一个交互式Folium地图，包含4个可切换的图层:
  1. 🟥 老龄化热力层（区县Choropleth）
  2. 🏥 医疗机构层（Point Markers）
  3. 🏡 养老机构层（Point Markers）
  4. 🛒 便民服务层（Point Markers）

  底图使用高德地图瓦片（中文标注，适配重庆），支持切换为
  高德卫星图和OpenStreetMap。

用法:
  from src.visualization.combined_map import create_combined_map
  create_combined_map(output_path="output/figures/heatmap/combined_map.html")
============================================================
"""

import os
import json
import random
import math
import pandas as pd
import numpy as np
import folium
from folium import plugins
from folium.plugins import MarkerCluster, HeatMap
from typing import Optional
from shapely.geometry import shape, mapping, MultiPolygon

from src.utils.config_loader import get_config


# ==================== 2. 省级边界计算 ====================

def _compute_province_boundary(geojson: dict) -> dict:
    """
    对 GeoJSON 中所有区县做几何合并（union），生成重庆市省级轮廓。

    返回:
        单个 Feature 的 GeoJSON dict，properties 含 {"name": "重庆市"}
    """
    from shapely.ops import unary_union

    polygons = []
    for feat in geojson["features"]:
        polygons.append(shape(feat["geometry"]))

    # 合并所有区县几何 => 重庆市整体轮廓
    merged = unary_union(polygons)

    # 简化轮廓（减少顶点数，提升地图性能）
    merged_simple = merged.simplify(tolerance=0.001, preserve_topology=True)

    boundary_feature = {
        "type": "Feature",
        "properties": {"name": "重庆市"},
        "geometry": mapping(merged_simple),
    }
    return {"type": "FeatureCollection", "features": [boundary_feature]}


# ==================== 3. POI 数据生成 ====================

# 三级甲等医院名称模板
_TOP_HOSPITALS = [
    "重庆医科大学附属{name}医院", "重庆市{name}人民医院",
    "重庆市{name}中心医院", "{name}区人民医院",
    "重庆大学附属{name}医院",
]

# 社区卫生服务中心模板
_COMMUNITY_CLINICS = [
    "{name}街道社区卫生服务中心", "{name}镇卫生院",
    "{name}社区健康管理中心", "{name}片区卫生服务站",
]

# 养老机构名称模板
_NURSING_HOMES = [
    "{name}区养老服务中心", "{name}夕阳红敬老院",
    "{name}老年公寓", "{name}康养中心",
    "{name}社区日间照料中心", "{name}智慧养老服务站",
]

# 便民服务名称模板
_CONVENIENCE_SERVICES = [
    "{name}社区便民服务中心", "{name}老年食堂",
    "{name}社区活动中心", "{name}便民药店",
    "{name}法律援助站", "{name}社保服务点",
]

# 重庆地名修饰词
_DISTRICT_MODIFIERS = {
    "渝中区": "解放碑", "江北区": "观音桥", "沙坪坝区": "三峡广场",
    "九龙坡区": "杨家坪", "南岸区": "南坪", "渝北区": "新牌坊",
    "巴南区": "鱼洞", "北碚区": "天生", "万州区": "高笋塘",
    "涪陵区": "荔枝", "长寿区": "凤城", "江津区": "几江",
}


def _random_point_in_district(lat: float, lon: float, radius: float = 0.08) -> tuple:
    """在区县中心点附近随机偏移，模拟真实POI分布"""
    dx = random.uniform(-radius, radius)
    dy = random.uniform(-radius, radius)
    return (lat + dx, lon + dy)


def _generate_poi_data(
    districts: list,
    centroids: dict,
    population_data: pd.DataFrame,
    seed: int = 42,
) -> dict:
    """
    基于人口和老龄化数据生成模拟POI

    返回:
        {
            "医疗机构": [{"区县":..., "名称":..., "lat":..., "lon":..., "类型":..., "床位数":..., "标签":...}, ...],
            "养老机构": [...],
            "便民服务": [...],
        }
    """
    random.seed(seed)
    np.random.seed(seed)

    # 聚合人口数据（2024年）
    pop_2024 = population_data[population_data["年份"] == 2024].copy()
    pop_map = pop_2024.set_index("区县").to_dict("index")

    pois = {"医疗机构": [], "养老机构": [], "便民服务": []}

    for district in districts:
        info = pop_map.get(district, {})
        pop = info.get("常住人口", 50) / 1e4  # 万人
        elderly = info.get("65岁及以上人口", 10) / 1e4
        aging_rate = elderly / max(pop, 1)  # 老龄化率

        lat, lon = centroids.get(district, (29.5, 107.5))

        # --- 根据人口规模确定 POI 数量 ---
        num_hospitals = max(1, int(pop / 30))            # 每30万人1家大型医院
        num_clinics = max(2, int(pop / 10))               # 每10万人1家社区诊所
        num_nursing = max(1, int(elderly / 3))            # 每3万老人1家养老机构
        num_convenience = max(2, int(pop / 8))            # 每8万人1个便民点

        # ----- 医疗机构 -----
        for i in range(num_hospitals):
            pt = _random_point_in_district(lat, lon, 0.06)
            modifier = _DISTRICT_MODIFIERS.get(district, district.replace("区", "").replace("县", ""))
            name_template = random.choice(_TOP_HOSPITALS)
            name = name_template.format(name=modifier if random.random() > 0.3 else district.replace("区","").replace("县",""))
            beds = int(np.random.lognormal(mean=5.5, sigma=0.5))  # ~200-600床
            pois["医疗机构"].append({
                "区县": district, "名称": name,
                "lat": pt[0], "lon": pt[1],
                "类型": "综合医院" if i == 0 else "专科医院",
                "床位数": min(beds, 2000),
                "标签": f"🏥 {name} ({beds}床)",
            })

        # 社区诊所
        for i in range(num_clinics):
            pt = _random_point_in_district(lat, lon, 0.10)
            modifier = random.choice(["双龙", "龙洲湾", "陈家桥", "西永", "鱼嘴", "水土", "李家沱", "小龙坎"])
            name = random.choice(_COMMUNITY_CLINICS).format(name=modifier)
            pois["医疗机构"].append({
                "区县": district, "名称": name,
                "lat": pt[0], "lon": pt[1],
                "类型": "社区卫生服务中心",
                "床位数": random.randint(10, 80),
                "标签": f"🩺 {name}",
            })

        # ----- 养老机构 -----
        for i in range(num_nursing):
            pt = _random_point_in_district(lat, lon, 0.08)
            modifier = _DISTRICT_MODIFIERS.get(district, district.replace("区", "").replace("县", ""))
            name = random.choice(_NURSING_HOMES).format(
                name=modifier if random.random() > 0.4 else district
            )
            capacity = int(np.random.lognormal(mean=4.0, sigma=0.6))  # ~20-200床
            pois["养老机构"].append({
                "区县": district, "名称": name,
                "lat": pt[0], "lon": pt[1],
                "床位数": min(capacity, 500),
                "收费标准": random.choice(["2000-4000元/月", "3000-6000元/月", "5000-10000元/月"]),
                "标签": f"🏡 {name} ({capacity}床)",
            })

        # ----- 便民服务 -----
        for i in range(num_convenience):
            pt = _random_point_in_district(lat, lon, 0.12)
            modifier = random.choice([
                "金华", "龙华", "凤天", "天星", "红岩",
                "春晖", "跃进", "石井", "陈家", "大坪",
            ])
            name = random.choice(_CONVENIENCE_SERVICES).format(name=modifier)
            service_type = random.choice(["社保", "养老助餐", "法律援助", "药店", "活动中心"])
            pois["便民服务"].append({
                "区县": district, "名称": name,
                "lat": pt[0], "lon": pt[1],
                "服务类型": service_type,
                "标签": f"📌 {name}",
            })

    # 汇总统计
    for key, items in pois.items():
        print(f"  ✅ 生成 {key}: {len(items)} 个")

    return pois


# ==================== 4. 地图颜色工具 ====================

_AGING_COLORS = {
    0.18: "#ffffcc",
    0.22: "#c2e699",
    0.26: "#78c679",
    0.30: "#31a354",
    0.34: "#006837",
}

_HEALTHCARE_COLORS = {
    "综合医院": "#e74c3c",
    "专科医院": "#e67e22",
    "社区卫生服务中心": "#3498db",
}

_NURSING_COLOR = "#9b59b6"
_CONVENIENCE_COLORS = {
    "社保": "#1abc9c",
    "养老助餐": "#f39c12",
    "法律援助": "#2ecc71",
    "药店": "#e91e63",
    "活动中心": "#00bcd4",
}

def _aging_to_color(rate: float) -> str:
    """老龄化率 → 颜色映射"""
    if rate < 0.18:
        return "#ffffcc"
    elif rate < 0.22:
        return "#c2e699"
    elif rate < 0.26:
        return "#78c679"
    elif rate < 0.30:
        return "#31a354"
    else:
        return "#006837"


# ==================== 5. 主地图生成函数 ====================


def create_combined_map(
    output_path: Optional[str] = None,
    aging_year: int = 2024,
    show_poi_labels: bool = True,
):
    """
    生成综合地图：老龄化热力 + 医疗机构 + 养老机构 + 便民服务

    参数:
        output_path: HTML输出路径
        aging_year: 老龄化数据显示年份
        show_poi_labels: 是否显示POI名称标签
    """
    config = get_config()
    root = config["paths"]["root"]

    # ===== 加载数据 =====
    geo_path = os.path.join(root, config["data_sources"]["geo"][0]["file"])
    with open(geo_path, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    with open(os.path.join(root, "data/geo/district_centroids.json"), "r",
              encoding="utf-8") as f:
        centroids_data = json.load(f)

    centroids = dict(zip(centroids_data["区县"],
                         zip(centroids_data["lat"], centroids_data["lon"])))
    districts = centroids_data["区县"]

    # 加载人口数据
    from src.data.data_loader import load_population_data
    from src.data.data_preprocessor import clean_population_data, compute_aging_rate

    df_pop = load_population_data()
    df_pop = clean_population_data(df_pop)
    df_pop = compute_aging_rate(df_pop)

    # 计算各区县老龄化率
    pivot = df_pop.pivot_table(index="区县", columns="年份", values="老龄化率",
                                aggfunc="mean")
    aging_map = pivot[aging_year].to_dict()

    # ===== 生成POI数据 =====
    print("\n📌 生成兴趣点(POI)数据...")
    pois = _generate_poi_data(districts, centroids, df_pop, seed=42)

    # ===== 创建地图（高德底图，适配重庆） =====
    print("\n🗺️ 构建综合地图（高德底图 + 多图层）...")

    # 高德地图瓦片URL — 中文标注、路网详细，最适合重庆
    GAODE_TILES = (
        "https://webrd0{s}.is.autonavi.com/appmaptile"
        "?lang=zh_cn&size=1&scale=1&style=8"
        "&x={x}&y={y}&z={z}"
    )
    GAODE_SATELLITE = (
        "https://webst0{s}.is.autonavi.com/appmaptile"
        "?style=6&x={x}&y={y}&z={z}"
    )
    GAODE_SUBDOMAINS = ["1", "2", "3", "4"]

    # 地图中心（重庆）
    m = folium.Map(
        location=[29.8, 107.5],
        zoom_start=9,
        tiles=GAODE_TILES,
        attr='&copy; 高德地图 AutoNavi',
        control_scale=True,
    )

    # ---- 添加底图切换图层 ----
    # 高德卫星影像
    folium.TileLayer(
        tiles=GAODE_SATELLITE,
        name="🛰️ 高德卫星图",
        attr='&copy; 高德地图 AutoNavi',
        overlay=False,
        control=True,
    ).add_to(m)
    # OpenStreetMap 作为备用
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="🌍 OpenStreetMap",
        attr='OpenStreetMap contributors',
        overlay=False,
        control=True,
    ).add_to(m)

    # ---- 添加全屏控件 ----
    plugins.Fullscreen().add_to(m)

    # ---- 添加图层控制 ----
    layer_hospitals = folium.FeatureGroup(name="🏥 医疗机构", show=False)
    layer_nursing = folium.FeatureGroup(name="🏡 养老机构", show=False)
    layer_convenience = folium.FeatureGroup(name="🛒 便民服务", show=False)

    # ===== Layer 1: 老龄化热力 (Choropleth - 需直接添加到Map) =====
    print("  📊 绘制老龄化热力层...")

    # 合并老龄化率到GeoJSON
    for feature in geojson["features"]:
        district = feature["properties"]["区县"]
        rate = aging_map.get(district, 0)
        feature["properties"]["老龄化率"] = round(rate, 4)
        feature["properties"]["老龄化率标签"] = f"{rate:.1%}"

    folium.Choropleth(
        geo_data=geojson,
        name="🟥 老龄化热力",
        data=list(aging_map.items()),
        columns=["区县", "老龄化率"],
        key_on="feature.properties.区县",
        fill_color="YlGn",
        fill_opacity=0.7,
        line_opacity=0.15,        # 边界线淡色，由下面的独立边界层负责
        legend_name=f"{aging_year}年老龄化率",
        bins=[0.15, 0.18, 0.22, 0.26, 0.30, 0.34, 0.38],
        smooth_factor=1.0,
        highlight=True,
        overlay=True,
        show=True,
    ).add_to(m)

    # ===== 计算省级轮廓（合并所有区县几何 => 重庆市整体边界） =====
    print("  🇨🇳 计算重庆市级行政轮廓...")
    province_geojson = _compute_province_boundary(geojson)

    # ---- Layer 1a: 省级轮廓（重庆市整体，加粗深色描边） ----
    folium.GeoJson(
        province_geojson,
        name="🇨🇳 省级轮廓（重庆市）",
        style_function=lambda x: {
            "fillColor": "transparent",
            "color": "#1a1a2e",
            "weight": 4.5,
            "opacity": 1.0,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["name"],
            aliases=["行政区域："],
            localize=True,
            sticky=True,
        ),
    ).add_to(m)

    # ---- Layer 1b: 区县边界（浅灰色细线） ----
    folium.GeoJson(
        geojson,
        name="📍 区县边界",
        style_function=lambda x: {
            "fillColor": "transparent",
            "color": "#7f8c8d",
            "weight": 1.5,
            "opacity": 0.7,
        },
        highlight_function=lambda x: {
            "weight": 3.0,
            "color": "#e74c3c",
            "opacity": 1.0,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["区县", "老龄化率标签"],
            aliases=["区县：", "老龄化率："],
            localize=True,
            sticky=True,
        ),
        popup=folium.GeoJsonPopup(
            fields=["区县", "老龄化率标签"],
            aliases=["区县：", "老龄化率："],
        ),
    ).add_to(m)

    # 添加区县名称标签（DivIcon，保持始终可见）
    for feature in geojson["features"]:
        district = feature["properties"]["区县"]
        rate = aging_map.get(district, 0)
        lat, lon = centroids.get(district, (29.5, 107.5))
        level = ("轻度" if rate < 0.18 else
                 "中度" if rate < 0.25 else
                 "重度" if rate < 0.30 else "深度")
        popup_text = f"""
        <b>{district}</b><br>
        老龄化率: {rate:.1%}<br>
        老龄化等级: <span style="color:{"green" if rate<0.18 else "orange" if rate<0.25 else "red" if rate<0.30 else "darkred"}">{level}</span>
        """
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px;font-weight:bold;color:#333;'
                     f'background:rgba(255,255,255,0.7);padding:1px 4px;'
                     f'border-radius:3px;border:1px solid #ccc;">{district}</div>'
            ),
            popup=folium.Popup(popup_text, max_width=250),
        ).add_to(m)

    # ===== Layer 2: 医疗机构 =====
    print("  🏥 绘制医疗机构层...")
    cluster_hosp = MarkerCluster(name="医疗机构").add_to(layer_hospitals)

    for poi in pois["医疗机构"]:
        color = _HEALTHCARE_COLORS.get(poi["类型"], "#e74c3c")
        popup_html = f"""
        <b>{poi['名称']}</b><br>
        类型: {poi['类型']}<br>
        床位数: {poi['床位数']} 张<br>
        区县: {poi['区县']}
        """
        folium.Marker(
            location=[poi["lat"], poi["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=poi.get("标签") if show_poi_labels else poi["名称"],
            icon=folium.Icon(
                color="red" if poi["类型"] == "综合医院" else
                      "orange" if poi["类型"] == "专科医院" else "blue",
                icon="plus-square" if poi["类型"] == "综合医院" else
                     "plus" if poi["类型"] == "专科医院" else "medkit",
                prefix="fa",
            ),
        ).add_to(cluster_hosp)

    # ===== Layer 3: 养老机构 =====
    print("  🏡 绘制养老机构层...")
    cluster_nurse = MarkerCluster(name="养老机构").add_to(layer_nursing)

    for poi in pois["养老机构"]:
        popup_html = f"""
        <b>{poi['名称']}</b><br>
        床位数: {poi['床位数']} 张<br>
        收费标准: {poi['收费标准']}<br>
        区县: {poi['区县']}
        """
        folium.Marker(
            location=[poi["lat"], poi["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=poi.get("标签") if show_poi_labels else poi["名称"],
            icon=folium.Icon(color="purple", icon="home", prefix="fa"),
        ).add_to(cluster_nurse)

    # ===== Layer 4: 便民服务 =====
    print("  🛒 绘制便民服务层...")
    cluster_conv = MarkerCluster(name="便民服务").add_to(layer_convenience)

    icon_map = {"社保": "credit-card", "养老助餐": "cutlery",
                "法律援助": "gavel", "药店": "heartbeat", "活动中心": "group"}

    for poi in pois["便民服务"]:
        icon_name = icon_map.get(poi["服务类型"], "info-circle")
        popup_html = f"""
        <b>{poi['名称']}</b><br>
        服务类型: {poi['服务类型']}<br>
        区县: {poi['区县']}
        """
        folium.Marker(
            location=[poi["lat"], poi["lon"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=poi.get("标签") if show_poi_labels else poi["名称"],
            icon=folium.Icon(
                color="green" if poi["服务类型"] == "养老助餐" else
                      "blue" if poi["服务类型"] == "社保" else
                      "lightblue" if poi["服务类型"] == "活动中心" else
                      "lightgreen" if poi["服务类型"] == "法律援助" else "pink",
                icon=icon_name,
                prefix="fa",
            ),
        ).add_to(cluster_conv)

    # ===== 添加图层到地图 =====
    layer_hospitals.add_to(m)
    layer_nursing.add_to(m)
    layer_convenience.add_to(m)
    folium.LayerControl(collapsed=False, position="topright").add_to(m)

    # ===== 添加图例 =====
    legend_html = """
    <div style="position:fixed; bottom:30px; left:30px; z-index:1000;
                background:white; padding:12px; border-radius:8px;
                box-shadow: 0 0 12px rgba(0,0,0,0.15);
                font-size:13px; max-width:220px;">
        <b>📍 图例</b><br>
        <span style="color:#e74c3c;">●</span> 综合医院<br>
        <span style="color:#e67e22;">●</span> 专科医院<br>
        <span style="color:#3498db;">●</span> 社区卫生中心<br>
        <span style="color:#9b59b6;">●</span> 养老机构<br>
        <span style="color:#1abc9c;">●</span> 社保服务<br>
        <span style="color:#f39c12;">●</span> 老年食堂<br>
        <hr style="margin:4px 0;">
        <span style="background:#006837;color:white;padding:0 4px;">&gt;30%</span> 深度老龄化<br>
        <span style="background:#31a354;color:white;padding:0 4px;">26-30%</span> 重度<br>
        <span style="background:#78c679;padding:0 4px;">22-26%</span> 中度<br>
        <span style="background:#c2e699;padding:0 4px;">18-22%</span> 轻度<br>
        <span style="background:#ffffcc;padding:0 4px;">&lt;18%</span> 未老龄化
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # ===== 保存 =====
    if output_path is None:
        fig_dir = config["paths"]["output_figures"]
        output_path = os.path.join(fig_dir, "heatmap", "combined_map.html")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    m.save(output_path)

    # ===== 输出统计 =====
    print(f"\n{'='*60}")
    print(f"✅ 综合地图已生成！")
    print(f"{'='*60}")
    print(f"  路径: {output_path}")
    total = sum(len(v) for v in pois.values())
    print(f"  底图: 高德地图(默认) / 高德卫星 / OpenStreetMap 可切换")
    print(f"  总POI数量: {total} 个")
    print(f"    ├ 🏥 医疗机构: {len(pois['医疗机构'])} 个")
    print(f"    ├ 🏡 养老机构: {len(pois['养老机构'])} 个")
    print(f"    └ 🛒 便民服务: {len(pois['便民服务'])} 个")
    print(f"  图层: 省级轮廓 + 区县边界 + 老龄化热力 + 医疗机构 + 养老机构 + 便民服务")

    return output_path


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    import argparse
    parser = argparse.ArgumentParser(description="生成综合可视化地图")
    parser.add_argument("--output", "-o",
                        default="output/figures/heatmap/combined_map.html",
                        help="输出HTML路径")
    parser.add_argument("--year", type=int, default=2024,
                        help="老龄化数据年份")
    parser.add_argument("--no-labels", action="store_true",
                        help="不显示POI名称标签")
    args = parser.parse_args()

    create_combined_map(
        output_path=args.output,
        aging_year=args.year,
        show_poi_labels=not args.no_labels,
    )
