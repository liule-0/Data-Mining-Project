"""
交互式老龄化热力图模块
基于 Folium + GeoPandas 生成重庆市各区县老龄化率的交互式热力图
"""

import os
import json
import pandas as pd
import folium
from folium import FeatureGroup
from folium.plugins import HeatMap
from branca.colormap import LinearColormap
from typing import Optional

# 尝试导入 geopandas，若不可用则使用纯 JSON 方式
try:
    import geopandas as gpd
    _HAS_GEOPANDAS = True
except ImportError:
    _HAS_GEOPANDAS = False


def _load_geojson(geo_path: str) -> dict:
    """加载 GeoJSON 文件"""
    with open(geo_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _merge_data_to_geojson(geojson: dict, data_df: pd.DataFrame,
                            value_col: str) -> dict:
    """将区县数据合并到 GeoJSON 的 properties 中"""
    data_map = data_df.set_index("区县")[value_col].to_dict()
    for feature in geojson["features"]:
        district = feature["properties"].get("区县", "")
        feature["properties"][value_col] = float(data_map.get(district, 0))
    return geojson


def create_aging_heatmap(
    geo_df,
    value_col: str = "老龄化率",
    year: int = 2024,
    output_path: Optional[str] = None,
    title: str = "重庆市各区县老龄化率分布",
) -> folium.Map:
    """
    创建重庆市老龄化率的交互式 Choropleth 热力图

    参数:
        geo_df: 包含区县几何边界和老龄化率数据的 GeoDataFrame 或普通 DataFrame
        value_col: 要可视化的列名
        year: 年份（用于标题标注）
        output_path: 若提供则保存为 HTML 文件
        title: 地图标题

    返回:
        folium.Map 对象
    """
    # 颜色映射：从绿到红（低老龄化→高老龄化）
    colormap = LinearColormap(
        colors=["#00b300", "#ffff00", "#ff9900", "#ff0000", "#990000"],
        vmin=geo_df[value_col].min(),
        vmax=geo_df[value_col].max(),
        caption=f"{year}年老龄化率",
    )

    # 创建地图
    m = folium.Map(
        location=[29.5, 107.5],  # 重庆市中心坐标
        zoom_start=8,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    # 添加标题
    title_html = f"""
    <div style="position: fixed; top: 10px; left: 50px; width: 320px; height: 50px;
                background-color: white; border-radius: 8px; padding: 10px;
                z-index: 9999; font-size: 16px; font-weight: bold;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
        {title}（{year}年）
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    # 获取 GeoJSON 数据
    if _HAS_GEOPANDAS and hasattr(geo_df, "__geo_interface__"):
        geojson_data = geo_df.__geo_interface__
        data_source = geo_df
    else:
        # 通过 DataFrame 方式：geo_df 是合并了老龄化率数据的 DataFrame
        from src.utils.config_loader import get_config
        config = get_config()
        geo_path = os.path.join(config["paths"]["root"],
                                config["data_sources"]["geo"][0]["file"])
        geojson_data = _load_geojson(geo_path)
        geojson_data = _merge_data_to_geojson(geojson_data, geo_df, value_col)
        data_source = geo_df

    # 添加 Choropleth 图层
    choropleth = folium.Choropleth(
        geo_data=geojson_data,
        data=data_source if _HAS_GEOPANDAS else geo_df,
        columns=["区县", value_col],
        key_on="feature.properties.区县",
        fill_color="RdYlGn_r",  # 红色高=老龄化高，绿色低
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name=f"{year}年老龄化率",
        highlight=True,
        smooth_factor=0.5,
    ).add_to(m)

    # 添加悬停提示
    folium.GeoJson(
        geojson_data,
        name="各区县详情",
        style_function=lambda x: {
            "fillColor": "transparent",
            "color": "transparent",
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["区县", value_col],
            aliases=["区县", "老龄化率"],
            localize=True,
            sticky=False,
            labels=True,
            style="""
                background-color: white;
                border: 1px solid black;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
            """,
        ),
        highlight_function=lambda x: {
            "weight": 2,
            "color": "black",
        },
    ).add_to(m)

    # 添加图例
    colormap.add_to(m)

    # 保存
    if output_path:
        m.save(output_path)
        print(f"热力图已保存至: {output_path}")

    return m


def create_aging_change_map(
    geo_df,
    change_col: str = "老龄化增幅",
    period: str = "2016-2024",
    output_path: Optional[str] = None,
) -> folium.Map:
    """
    创建老龄化率变化幅度的交互式地图
    """
    # 获取 GeoJSON
    if _HAS_GEOPANDAS and hasattr(geo_df, "__geo_interface__"):
        geojson_data = geo_df.__geo_interface__
    else:
        from src.utils.config_loader import get_config
        config = get_config()
        geo_path = os.path.join(config["paths"]["root"],
                                config["data_sources"]["geo"][0]["file"])
        geojson_data = _load_geojson(geo_path)
        geojson_data = _merge_data_to_geojson(geojson_data, geo_df, change_col)

    m = folium.Map(
        location=[29.5, 107.5],
        zoom_start=8,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    # 双向颜色映射（蓝色=减缓，红色=加速）
    max_val = max(abs(geo_df[change_col].min()), abs(geo_df[change_col].max()))
    colormap = LinearColormap(
        colors=["#0066ff", "#ffffff", "#ff0000"],
        vmin=-max_val,
        vmax=max_val,
        caption=f"{period}老龄化率变化（百分点）",
    )

    folium.Choropleth(
        geo_data=geojson_data,
        data=geo_df,
        columns=["区县", change_col],
        key_on="feature.properties.区县",
        fill_color="RdBu_r",
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name=f"{period}老龄化变化",
        highlight=True,
    ).add_to(m)

    folium.GeoJson(
        geojson_data,
        name="变化详情",
        style_function=lambda x: {"fillColor": "transparent", "color": "transparent"},
        tooltip=folium.GeoJsonTooltip(
            fields=["区县", change_col],
            aliases=["区县", "变化(百分点)"],
            localize=True,
            sticky=False,
            labels=True,
        ),
    ).add_to(m)

    colormap.add_to(m)

    if output_path:
        m.save(output_path)
        print(f"变化热力图已保存至: {output_path}")

    return m
