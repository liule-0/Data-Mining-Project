"""
============================================================
总和地图 — 老龄化严重程度 × 医疗资源 × 便民服务 综合指数
============================================================
功能:
  将三大维度合成为一个"综合压力指数"地图：
  1. 🟥 老龄化严重程度（老龄化率越高，压力越大）
  2. 🏥 医疗资源紧张度（人均床位数越少，压力越大）
  3. 🏡 养老资源紧张度（人均养老床位数越少，压力越大）
  4. 🛒 便民服务缺口度（人均服务点越少，压力越大）

  综合压力指数越高，表示该区县面临的老龄化挑战越严峻、
  配套资源越不足。

用法:
  from src.visualization.synthesized_map import create_synthesized_map
  create_synthesized_map(output_path="output/figures/heatmap/synthesized_map.html")
============================================================
"""

import os
import json
import math
import pandas as pd
import numpy as np
import folium
from folium import plugins
from typing import Optional, Dict, List, Tuple

from src.utils.config_loader import get_config


# ==================== 1. 数据加载 ====================

def _load_poi_data(data_dir: str) -> Dict[str, List[dict]]:
    """
    加载已有的 POI JSON 数据文件

    返回:
        {"医疗机构": [...], "养老机构": [...], "便民服务": [...]}
    """
    files = {
        "医疗机构": "medical_inst_data.json",
        "养老机构": "elderly_care_data.json",
        "便民服务": "service_data.json",
    }
    result = {}
    for key, filename in files.items():
        path = os.path.join(data_dir, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                result[key] = json.load(f)
            print(f"  ✅ 加载 {key}: {len(result[key])} 条")
        else:
            print(f"  ⚠️ 未找到 {key} 数据: {path}")
            result[key] = []
    return result


def _load_aging_data() -> pd.DataFrame:
    """从人口数据加载各区县老龄化率（2024年）"""
    from src.data.data_loader import load_population_data
    from src.data.data_preprocessor import clean_population_data, compute_aging_rate

    df = load_population_data()
    df = clean_population_data(df)
    df = compute_aging_rate(df)

    # 取2024年数据
    df_2024 = df[df["年份"] == 2024].copy()
    return df_2024[["区县", "常住人口", "65岁及以上人口", "老龄化率"]]


# ==================== 2. 综合指数计算 ====================

def _compute_composite_index(
    aging_data: pd.DataFrame,
    poi_data: Dict[str, List[dict]],
    weights: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    """
    计算各区县综合压力指数

    参数:
        aging_data: 老龄化数据（含区县、常住人口、65岁及以上人口、老龄化率）
        poi_data: POI数据字典
        weights: 各维度权重，默认:
            - 老龄化压力: 0.40
            - 医疗资源缺口: 0.25
            - 养老资源缺口: 0.20
            - 便民服务缺口: 0.15

    返回:
        DataFrame: 各区县综合指数及各维度明细
    """
    if weights is None:
        weights = {
            "老龄化压力": 0.40,
            "医疗资源缺口": 0.25,
            "养老资源缺口": 0.20,
            "便民服务缺口": 0.15,
        }

    # 按区县聚合POI
    def _count_by_district(items: List[dict]) -> Dict[str, int]:
        counts = {}
        for item in items:
            dist = item.get("区县", "")
            counts[dist] = counts.get(dist, 0) + 1
        return counts

    # 按区县聚合资源量（床位数）
    def _sum_beds_by_district(items: List[dict], bed_field: str = "床位数") -> Dict[str, int]:
        sums = {}
        for item in items:
            dist = item.get("区县", "")
            beds = item.get(bed_field, 0) or 0
            sums[dist] = sums.get(dist, 0) + beds
        return sums

    med_count = _count_by_district(poi_data.get("医疗机构", []))
    med_beds = _sum_beds_by_district(poi_data.get("医疗机构", []), "床位数")
    eld_count = _count_by_district(poi_data.get("养老机构", []))
    eld_beds = _sum_beds_by_district(poi_data.get("养老机构", []), "床位数")
    svc_count = _count_by_district(poi_data.get("便民服务", []))

    # 构建各维度原始值
    records = []
    for _, row in aging_data.iterrows():
        district = row["区县"]
        elderly_pop = row["65岁及以上人口"]  # 人
        aging_rate = row["老龄化率"]

        # 原始资源密度（每千名老人）
        med_beds_per_1k = (med_beds.get(district, 0) / max(elderly_pop, 1)) * 1000
        eld_beds_per_1k = (eld_beds.get(district, 0) / max(elderly_pop, 1)) * 1000
        svc_per_1k = (svc_count.get(district, 0) / max(elderly_pop, 1)) * 1000

        records.append({
            "区县": district,
            "老龄化率": aging_rate,
            "老年人口": elderly_pop,
            "医疗机构数": med_count.get(district, 0),
            "医疗床位数": med_beds.get(district, 0),
            "医疗床位数_每千老人": round(med_beds_per_1k, 1),
            "养老机构数": eld_count.get(district, 0),
            "养老床位数": eld_beds.get(district, 0),
            "养老床位数_每千老人": round(eld_beds_per_1k, 1),
            "便民服务点数": svc_count.get(district, 0),
            "便民服务点_每千老人": round(svc_per_1k, 1),
        })

    df = pd.DataFrame(records)

    # ---- 归一化各维度到 [0, 1] ----
    # 老龄化压力：直接使用老龄化率（越高越严重）
    min_rate, max_rate = df["老龄化率"].min(), df["老龄化率"].max()
    df["老龄化压力分"] = (df["老龄化率"] - min_rate) / max(max_rate - min_rate, 1e-6)

    # 医疗资源缺口：床位数越少，缺口越大（取反归一化）
    min_beds, max_beds = df["医疗床位数_每千老人"].min(), df["医疗床位数_每千老人"].max()
    df["医疗资源缺口分"] = 1 - (df["医疗床位数_每千老人"] - min_beds) / max(max_beds - min_beds, 1e-6)

    # 养老资源缺口：养老床位数越少，缺口越大
    min_eld_beds, max_eld_beds = df["养老床位数_每千老人"].min(), df["养老床位数_每千老人"].max()
    df["养老资源缺口分"] = 1 - (df["养老床位数_每千老人"] - min_eld_beds) / max(max_eld_beds - min_eld_beds, 1e-6)

    # 便民服务缺口：服务点越少，缺口越大
    min_svc, max_svc = df["便民服务点_每千老人"].min(), df["便民服务点_每千老人"].max()
    df["便民服务缺口分"] = 1 - (df["便民服务点_每千老人"] - min_svc) / max(max_svc - min_svc, 1e-6)

    # ---- 综合压力指数 ----
    df["综合压力指数"] = (
        weights["老龄化压力"] * df["老龄化压力分"]
        + weights["医疗资源缺口"] * df["医疗资源缺口分"]
        + weights["养老资源缺口"] * df["养老资源缺口分"]
        + weights["便民服务缺口"] * df["便民服务缺口分"]
    )

    # 等级划分
    def _level(score: float) -> str:
        if score >= 0.70:
            return "🔴 极高压力"
        elif score >= 0.55:
            return "🟠 较高压力"
        elif score >= 0.40:
            return "🟡 中等压力"
        elif score >= 0.25:
            return "🟢 较低压力"
        else:
            return "🔵 低压力"

    df["压力等级"] = df["综合压力指数"].apply(_level)

    # 排序
    df = df.sort_values("综合压力指数", ascending=False).reset_index(drop=True)

    return df


# ==================== 3. 地图颜色工具 ====================

def _composite_to_color(score: float) -> str:
    """综合压力指数 → 颜色（红绿渐变）"""
    if score >= 0.70:
        return "#8b0000"  # 暗红
    elif score >= 0.55:
        return "#e74c3c"  # 红
    elif score >= 0.40:
        return "#f39c12"  # 橙
    elif score >= 0.25:
        return "#f1c40f"  # 黄
    else:
        return "#2ecc71"  # 绿


# ==================== 4. 主生成函数 ====================

def create_synthesized_map(
    output_path: Optional[str] = None,
    aging_year: int = 2024,
    weights: Optional[Dict[str, float]] = None,
):
    """
    生成总和地图：老龄化 × 医疗 × 养老 × 便民 综合压力指数

    参数:
        output_path: HTML输出路径
        aging_year: 老龄化数据年份
        weights: 各维度权重
    """
    if weights is None:
        weights = {
            "老龄化压力": 0.40,
            "医疗资源缺口": 0.25,
            "养老资源缺口": 0.20,
            "便民服务缺口": 0.15,
        }

    config = get_config()
    root = config["paths"]["root"]
    data_dir = os.path.join(root, config["paths"]["output_figures"], "..")
    # 使用 output/ 目录下的 JSON 数据
    output_dir = os.path.join(root, "output")

    print("=" * 60)
    print("🗺️ 合成总和地图 — 老龄化×医疗×便民 综合压力指数")
    print("=" * 60)

    # ===== 1. 加载数据 =====
    print("\n📦 加载数据...")

    # 老龄化数据
    aging_data = _load_aging_data()
    print(f"  ✅ 老龄化数据: {len(aging_data)} 个区县")
    print(f"     老龄化率范围: {aging_data['老龄化率'].min():.1%} ~ {aging_data['老龄化率'].max():.1%}")

    # POI 数据
    poi_data = _load_poi_data(output_dir)

    # GeoJSON
    geo_path = os.path.join(root, config["data_sources"]["geo"][0]["file"])
    with open(geo_path, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    # 区县中心点
    centroids_path = os.path.join(root, "data/geo/district_centroids.json")
    with open(centroids_path, "r", encoding="utf-8") as f:
        centroids_data = json.load(f)
    centroids = dict(zip(centroids_data["区县"],
                         zip(centroids_data["lat"], centroids_data["lon"])))
    districts = centroids_data["区县"]

    # ===== 2. 计算综合指数 =====
    print("\n🧮 计算综合压力指数...")
    df_index = _compute_composite_index(aging_data, poi_data, weights)

    # 创建区县→综合指数映射
    index_map = df_index.set_index("区县").to_dict("index")

    # 打印排名
    print(f"\n  📊 综合压力指数 TOP 10（压力最大区县）:")
    for i, (_, row) in enumerate(df_index.head(10).iterrows()):
        print(f"     {i+1}. {row['区县']}: {row['综合压力指数']:.3f} ({row['压力等级']})")

    print(f"\n  📊 综合压力指数 BOTTOM 5（压力最小区县）:")
    for i, (_, row) in enumerate(df_index.tail(5).iterrows()):
        print(f"     {len(df_index)-4+i}. {row['区县']}: {row['综合压力指数']:.3f} ({row['压力等级']})")

    # ===== 3. 构建地图（高德底图） =====
    print("\n🗺️ 构建总和地图...")

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

    m = folium.Map(
        location=[29.8, 107.5],
        zoom_start=9,
        tiles=GAODE_TILES,
        attr='&copy; 高德地图 AutoNavi',
        control_scale=True,
    )

    # 底图切换
    folium.TileLayer(
        tiles=GAODE_SATELLITE,
        name="🛰️ 高德卫星图",
        attr='&copy; 高德地图 AutoNavi',
        overlay=False, control=True,
    ).add_to(m)
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="🌍 OpenStreetMap",
        attr='OpenStreetMap contributors',
        overlay=False, control=True,
    ).add_to(m)

    plugins.Fullscreen().add_to(m)

    # ===== 4. 合并综合指数到 GeoJSON =====
    for feature in geojson["features"]:
        district = feature["properties"]["区县"]
        idx = index_map.get(district, {})
        feature["properties"]["综合压力指数"] = round(idx.get("综合压力指数", 0), 4)
        feature["properties"]["压力等级"] = idx.get("压力等级", "未知")
        feature["properties"]["老龄化率标签"] = f"{idx.get('老龄化率', 0):.1%}"
        feature["properties"]["医疗床位数_每千老人"] = idx.get("医疗床位数_每千老人", 0)
        feature["properties"]["养老床位数_每千老人"] = idx.get("养老床位数_每千老人", 0)
        feature["properties"]["便民服务点_每千老人"] = idx.get("便民服务点_每千老人", 0)

    # ===== 5. Choropleth 综合压力指数 =====
    # 为 Choropleth 准备扁平数据: list of (区县, 综合压力指数) 元组
    choropleth_data = [(dist, info["综合压力指数"]) for dist, info in index_map.items()]
    folium.Choropleth(
        geo_data=geojson,
        name="📊 综合压力指数",
        data=choropleth_data,
        columns=["区县", "综合压力指数"],
        key_on="feature.properties.区县",
        fill_color="RdYlGn_r",  # 红-黄-绿反转（红=高压力，绿=低压力）
        fill_opacity=0.75,
        line_opacity=0.15,
        legend_name=f"综合压力指数（{aging_year}年）",
        bins=[0, 0.15, 0.30, 0.45, 0.60, 0.75, 1.0],
        smooth_factor=1.0,
        highlight=True,
        overlay=True,
        show=True,
    ).add_to(m)

    # ===== 6. 省级轮廓 =====
    from shapely.geometry import shape, mapping
    from shapely.ops import unary_union

    polygons = [shape(f["geometry"]) for f in geojson["features"]]
    merged = unary_union(polygons).simplify(tolerance=0.001, preserve_topology=True)
    province_feature = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"name": "重庆市"},
            "geometry": mapping(merged),
        }],
    }
    folium.GeoJson(
        province_feature,
        name="🇨🇳 重庆市轮廓",
        style_function=lambda x: {
            "fillColor": "transparent",
            "color": "#1a1a2e",
            "weight": 4.5,
            "opacity": 1.0,
        },
        tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["行政区域："]),
    ).add_to(m)

    # ===== 7. 区县边界 + 交互提示 =====
    folium.GeoJson(
        geojson,
        name="📍 区县详情",
        style_function=lambda x: {
            "fillColor": "transparent",
            "color": "#7f8c8d",
            "weight": 1.2,
            "opacity": 0.6,
        },
        highlight_function=lambda x: {
            "weight": 3.0, "color": "#e74c3c", "opacity": 1.0,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "区县", "综合压力指数", "压力等级",
                "老龄化率标签", "医疗床位数_每千老人",
                "养老床位数_每千老人", "便民服务点_每千老人",
            ],
            aliases=[
                "区县：", "综合压力指数：", "压力等级：",
                "老龄化率：", "医疗床位/千老人：",
                "养老床位/千老人：", "便民服务点/千老人：",
            ],
            localize=True,
            sticky=True,
            style="""
                background: white;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            """,
        ),
        popup=folium.GeoJsonPopup(
            fields=[
                "区县", "综合压力指数", "压力等级",
                "老龄化率标签", "医疗床位数_每千老人",
                "养老床位数_每千老人", "便民服务点_每千老人",
            ],
            aliases=[
                "区县：", "综合压力指数：", "压力等级：",
                "老龄化率：", "医疗床位/千老人：",
                "养老床位/千老人：", "便民服务点/千老人：",
            ],
        ),
    ).add_to(m)

    # ===== 8. 区县名称标签 =====
    for feature in geojson["features"]:
        district = feature["properties"]["区县"]
        idx = index_map.get(district, {})
        score = idx.get("综合压力指数", 0)
        lat, lon = centroids.get(district, (29.5, 107.5))

        level_color = (
            "#8b0000" if score >= 0.70 else
            "#e74c3c" if score >= 0.55 else
            "#f39c12" if score >= 0.40 else
            "#f1c40f" if score >= 0.25 else
            "#2ecc71"
        )

        breakdown = (
            f"老龄化: {idx.get('老龄化率', 0):.1%} | "
            f"医疗床位: {idx.get('医疗床位数_每千老人', 0):.0f}/千老人 | "
            f"养老床位: {idx.get('养老床位数_每千老人', 0):.0f}/千老人 | "
            f"便民点: {idx.get('便民服务点_每千老人', 0):.1f}/千老人"
        )

        popup_html = f"""
        <div style="min-width:280px;font-family:'Microsoft YaHei',sans-serif;">
            <h4 style="margin:0 0 8px;color:#2d3748;border-bottom:2px solid {level_color};padding-bottom:4px;">
                {district}
            </h4>
            <table style="width:100%;font-size:13px;border-collapse:collapse;">
                <tr>
                    <td style="padding:4px 0;color:#718096;">综合压力指数</td>
                    <td style="padding:4px 0;font-weight:700;text-align:right;color:{level_color};">
                        {score:.3f}
                    </td>
                </tr>
                <tr>
                    <td style="padding:4px 0;color:#718096;">压力等级</td>
                    <td style="padding:4px 0;font-weight:600;text-align:right;">
                        {idx.get('压力等级', '未知')}
                    </td>
                </tr>
                <tr>
                    <td style="padding:4px 0;color:#718096;">老龄化率</td>
                    <td style="padding:4px 0;text-align:right;">{idx.get('老龄化率', 0):.1%}</td>
                </tr>
                <tr>
                    <td style="padding:4px 0;color:#718096;">医疗床位/千老人</td>
                    <td style="padding:4px 0;text-align:right;">{idx.get('医疗床位数_每千老人', 0):.0f}</td>
                </tr>
                <tr>
                    <td style="padding:4px 0;color:#718096;">养老床位/千老人</td>
                    <td style="padding:4px 0;text-align:right;">{idx.get('养老床位数_每千老人', 0):.0f}</td>
                </tr>
                <tr>
                    <td style="padding:4px 0;color:#718096;">便民服务点/千老人</td>
                    <td style="padding:4px 0;text-align:right;">{idx.get('便民服务点_每千老人', 0):.1f}</td>
                </tr>
            </table>
            <hr style="margin:6px 0;border:none;border-top:1px solid #edf2f7;">
            <div style="font-size:11px;color:#a0aec0;">
                老龄化压力×{weights.get('老龄化压力', 0):.0%} +
                医疗缺口×{weights.get('医疗资源缺口', 0):.0%} +
                养老缺口×{weights.get('养老资源缺口', 0):.0%} +
                便民缺口×{weights.get('便民服务缺口', 0):.0%}
            </div>
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px;font-weight:bold;color:#333;'
                     f'background:rgba(255,255,255,0.85);padding:1px 5px;'
                     f'border-radius:3px;border:2px solid {level_color};">'
                     f'{district}</div>'
            ),
            popup=folium.Popup(popup_html, max_width=350),
        ).add_to(m)

    # ===== 9. 图例 =====
    legend_html = """
    <div style="position:fixed; bottom:30px; left:30px; z-index:1000;
                background:white; padding:14px 16px; border-radius:10px;
                box-shadow: 0 0 16px rgba(0,0,0,0.15);
                font-size:13px; max-width:230px; font-family:'Microsoft YaHei',sans-serif;">
        <b>📊 综合压力指数图例</b><br>
        <span style="display:inline-block;width:14px;height:14px;background:#8b0000;border-radius:2px;vertical-align:middle;"></span>
        &nbsp; 0.70~1.00 极高压力<br>
        <span style="display:inline-block;width:14px;height:14px;background:#e74c3c;border-radius:2px;vertical-align:middle;"></span>
        &nbsp; 0.55~0.70 较高压力<br>
        <span style="display:inline-block;width:14px;height:14px;background:#f39c12;border-radius:2px;vertical-align:middle;"></span>
        &nbsp; 0.40~0.55 中等压力<br>
        <span style="display:inline-block;width:14px;height:14px;background:#f1c40f;border-radius:2px;vertical-align:middle;"></span>
        &nbsp; 0.25~0.40 较低压力<br>
        <span style="display:inline-block;width:14px;height:14px;background:#2ecc71;border-radius:2px;vertical-align:middle;"></span>
        &nbsp; 0.00~0.25 低压力<br>
        <hr style="margin:6px 0;border:none;border-top:1px solid #edf2f7;">
        <div style="font-size:11px;color:#718096;">
            综合压力 = 老龄化×40% + 医疗缺口×25%<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; + 养老缺口×20% + 便民缺口×15%
        </div>
        <div style="font-size:10px;color:#a0aec0;margin-top:4px;">
            指数越高 → 老龄化越严重，配套资源越不足
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # ===== 10. 图层控制 =====
    folium.LayerControl(collapsed=False, position="topright").add_to(m)

    # ===== 11. 保存 =====
    if output_path is None:
        fig_dir = config["paths"]["output_figures"]
        output_path = os.path.join(fig_dir, "heatmap", "synthesized_map.html")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    m.save(output_path)

    # ===== 输出统计 =====
    print(f"\n{'='*60}")
    print(f"✅ 总和地图已生成！")
    print(f"{'='*60}")
    print(f"  路径: {output_path}")
    print(f"  底图: 高德地图(默认) / 高德卫星 / OpenStreetMap")
    print(f"  区县: {len(df_index)} 个")
    print(f"  权重: 老龄化{weights['老龄化压力']:.0%} + "
          f"医疗缺口{weights['医疗资源缺口']:.0%} + "
          f"养老缺口{weights['养老资源缺口']:.0%} + "
          f"便民缺口{weights['便民服务缺口']:.0%}")
    print(f"\n  📊 压力最大 TOP 5:")
    for _, row in df_index.head(5).iterrows():
        print(f"     {row['区县']}: {row['综合压力指数']:.3f} | "
              f"老龄化{row['老龄化率']:.1%} | "
              f"医疗{row['医疗床位数_每千老人']:.0f}床/千老人 | "
              f"养老{row['养老床位数_每千老人']:.0f}床/千老人")
    print(f"\n  📊 压力最小 TOP 5:")
    for _, row in df_index.tail(5).iterrows():
        print(f"     {row['区县']}: {row['综合压力指数']:.3f} | "
              f"老龄化{row['老龄化率']:.1%} | "
              f"医疗{row['医疗床位数_每千老人']:.0f}床/千老人 | "
              f"养老{row['养老床位数_每千老人']:.0f}床/千老人")

    return output_path, df_index


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    import argparse
    parser = argparse.ArgumentParser(description="生成合成总和地图")
    parser.add_argument("--output", "-o",
                        default="output/figures/heatmap/synthesized_map.html",
                        help="输出HTML路径")
    parser.add_argument("--year", type=int, default=2024,
                        help="老龄化数据年份")
    args = parser.parse_args()

    create_synthesized_map(output_path=args.output, aging_year=args.year)
