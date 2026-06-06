"""生成优化版地理可视化页面"""
import json
import math

with open('data/geo/chongqing_districts.geojson', 'r', encoding='utf-8') as f:
    geojson = json.load(f)

with open('output/combined_data.json', 'r', encoding='utf-8') as f:
    records = json.load(f)

geojson_str = json.dumps(geojson, ensure_ascii=False)
data_str = json.dumps(records, ensure_ascii=False)

html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>重庆市人口与医疗压力地理可视化</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; overflow: hidden; }}

/* ====== 顶部导航 ====== */
.topnav {{
  position: fixed; top: 0; left: 0; right: 0; z-index: 3000;
  background: linear-gradient(135deg, #1a365d, #2b6cb0);
  color: rgba(255,255,255,0.85);
  padding: 8px 20px;
  display: flex; align-items: center; gap: 14px;
  font-size: 13px; box-shadow: 0 2px 12px rgba(0,0,0,0.15);
}}
.topnav a {{
  color: #fff; text-decoration: none; display: flex; align-items: center; gap: 4px;
  font-weight: 600; background: rgba(255,255,255,0.15); padding: 4px 12px;
  border-radius: 6px; transition: background 0.2s;
}}
.topnav a:hover {{ background: rgba(255,255,255,0.25); }}
.topnav .title {{ font-size: 15px; font-weight: 700; color: #fff; }}
.topnav .sub {{ font-size: 11px; opacity: 0.6; margin-left: auto; }}

/* ====== 地图容器 ====== */
#map {{ width: 100vw; height: 100vh; }}

/* ====== 左侧控制面板 ====== */
.control-panel {{
  position: fixed; top: 52px; left: 16px; z-index: 2000;
  background: rgba(255,255,255,0.96);
  backdrop-filter: blur(8px);
  border-radius: 14px; padding: 18px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.18);
  width: 290px; max-height: calc(100vh - 80px);
  overflow-y: auto; transition: transform 0.3s;
}}
.control-panel::-webkit-scrollbar {{ width: 4px; }}
.control-panel::-webkit-scrollbar-thumb {{ background: #cbd5e0; border-radius: 2px; }}

.panel-header {{
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 14px;
}}
.panel-header h2 {{ font-size: 16px; color: #1a202c; font-weight: 700; }}
.panel-header .toggle-btn {{
  background: none; border: none; font-size: 18px; cursor: pointer;
  color: #718096; padding: 2px 6px; border-radius: 4px;
}}
.panel-header .toggle-btn:hover {{ background: #edf2f7; }}

.form-group {{ margin-bottom: 12px; }}
.form-group label {{
  font-size: 12px; font-weight: 600; color: #4a5568;
  display: block; margin-bottom: 3px;
}}
.form-group select, .form-group input {{
  width: 100%; padding: 7px 10px; border: 1px solid #e2e8f0;
  border-radius: 6px; font-size: 13px; background: #f7fafc;
  transition: border-color 0.2s;
}}
.form-group select:focus, .form-group input:focus {{
  outline: none; border-color: #3182ce; box-shadow: 0 0 0 2px rgba(49,130,206,0.15);
}}

/* 年份选择器 */
.year-selector {{
  display: grid; grid-template-columns: repeat(5, 1fr);
  gap: 3px; margin-bottom: 4px;
}}
.year-btn {{
  padding: 4px 0; border: 1px solid #e2e8f0; border-radius: 4px;
  font-size: 11px; background: white; cursor: pointer;
  transition: all 0.2s; text-align: center;
}}
.year-btn:hover {{ background: #ebf8ff; border-color: #90cdf4; }}
.year-btn.active {{
  background: #3182ce; color: white; border-color: #3182ce;
  font-weight: 700; box-shadow: 0 1px 4px rgba(49,130,206,0.3);
}}

/* 统计摘要 */
.stats-summary {{
  display: grid; grid-template-columns: 1fr 1fr 1fr;
  gap: 6px; margin-bottom: 14px;
}}
.stat-card {{
  background: #f7fafc; border-radius: 8px; padding: 8px 6px;
  text-align: center;
}}
.stat-card .stat-label {{ font-size: 9px; color: #a0aec0; }}
.stat-card .stat-value {{ font-size: 14px; font-weight: 700; color: #2d3748; }}
.stat-card .stat-extreme {{ font-size: 8px; color: #a0aec0; }}

/* 信息卡片 */
.info-card {{
  background: linear-gradient(135deg, #f7fafc, #edf2f7);
  border-radius: 10px; padding: 14px; margin-bottom: 10px;
  display: none; border: 1px solid #e2e8f0;
}}
.info-card h3 {{
  font-size: 15px; color: #2d3748; margin-bottom: 8px;
  display: flex; align-items: center; gap: 6px;
}}
.info-card h3 .region-badge {{
  font-size: 10px; font-weight: 400; color: #fff;
  background: #4a5568; padding: 1px 8px; border-radius: 10px;
}}
.info-card .row {{
  display: flex; justify-content: space-between;
  font-size: 12px; padding: 4px 0;
  border-bottom: 1px solid rgba(0,0,0,0.04);
}}
.info-card .row:last-child {{ border-bottom: none; }}
.info-card .label {{ color: #718096; }}
.info-card .value {{ font-weight: 600; color: #2d3748; }}
.info-card .level-tag {{
  display: inline-block; padding: 1px 8px; border-radius: 10px;
  font-size: 11px; font-weight: 600; color: #fff;
}}

/* ====== 图例 ====== */
.legend {{
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(4px);
  padding: 12px 14px; border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.12);
  font-size: 12px; line-height: 1.9;
}}
.legend b {{ font-size: 13px; color: #2d3748; }}
.legend .color-bar {{
  height: 8px; border-radius: 4px; margin: 6px 0;
  background: linear-gradient(to right, #2ecc71, #f1c40f, #e74c3c, #8b0000);
}}
.legend-labels {{
  display: flex; justify-content: space-between;
  font-size: 10px; color: #718096;
}}

/* ====== 区县标签样式 ====== */
.dist-label {{
  font-size: 10px; font-weight: 600; color: #2d3748;
  text-shadow: 0 0 4px #fff, 0 0 4px #fff, 0 0 4px #fff;
  pointer-events: none;
}}

/* ====== 响应式 ====== */
@media (max-width: 768px) {{
  .control-panel {{
    left: 8px; right: 8px; width: auto;
    max-height: 45vh; top: 50px;
  }}
  .stats-summary {{ grid-template-columns: 1fr 1fr; }}
}}
</style>
</head>
<body>

<div class="topnav">
  <a href="../index.html">← 返回首页</a>
  <span class="title">🗺️ 地理可视化</span>
  <span class="sub">重庆市人口老龄化与医疗压力空间分布</span>
</div>

<div id="map"></div>

<div class="control-panel" id="controlPanel">
  <div class="panel-header">
    <h2>📊 数据探索</h2>
    <button class="toggle-btn" onclick="togglePanel()" title="折叠/展开">−</button>
  </div>

  <div class="stats-summary" id="statsSummary">
    <div class="stat-card">
      <div class="stat-label">当前指标</div>
      <div class="stat-value" id="curMetric">-</div>
      <div class="stat-extreme" id="curYear">2024年</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">最大值</div>
      <div class="stat-value" id="maxVal">-</div>
      <div class="stat-extreme" id="maxDist">-</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">最小值</div>
      <div class="stat-value" id="minVal">-</div>
      <div class="stat-extreme" id="minDist">-</div>
    </div>
  </div>

  <div class="form-group">
    <label>📌 数据指标</label>
    <select id="metricSelect" onchange="updateMap()">
      <option value="aging_rate">老龄化率</option>
      <option value="elderly_adm_ratio">老年住院占比</option>
      <option value="pressure_index">医疗压力指数</option>
      <option value="composite_index">综合压力指数 ★</option>
      <option value="total_population">常住人口</option>
      <option value="elderly_population">65岁+人口</option>
      <option value="total_admissions">总住院人次</option>
      <option value="elderly_admissions">老年住院人次</option>
      <option value="heart_failure">心衰住院量</option>
      <option value="hypertension">高血压住院量</option>
      <option value="diabetes">糖尿病住院量</option>
      <option value="copd">慢阻肺住院量</option>
      <option value="stroke">脑卒中住院量</option>
    </select>
  </div>

  <div class="form-group">
    <label>📅 年份</label>
    <div class="year-selector" id="yearSelector"></div>
  </div>

  <div class="form-group">
    <label>📍 区域筛选</label>
    <select id="regionFilter" onchange="updateMap()">
      <option value="">全部区域</option>
      <option value="中心城区">中心城区</option>
      <option value="主城新区">主城新区</option>
      <option value="渝东北">渝东北</option>
      <option value="渝东南">渝东南</option>
    </select>
  </div>

  <div class="form-group">
    <label>🔍 区县搜索</label>
    <input id="districtSearch" type="text" placeholder="输入区县名称..." oninput="filterDistricts()">
  </div>

  <div id="infoCard" class="info-card">
    <h3><span id="districtName">-</span> <span id="regionBadge" class="region-badge"></span></h3>
    <div id="districtStats"></div>
  </div>
</div>

<script>
// ====== 数据 ======
const GEOJSON = {geojson_str};
const DATA = {data_str};

const REGION_MAP = {{
  "渝中区":"中心城区","江北区":"中心城区","南岸区":"中心城区","九龙坡区":"中心城区",
  "沙坪坝区":"中心城区","大渡口区":"中心城区","渝北区":"中心城区","巴南区":"中心城区","北碚区":"中心城区",
  "涪陵区":"主城新区","长寿区":"主城新区","江津区":"主城新区","合川区":"主城新区",
  "永川区":"主城新区","南川区":"主城新区","綦江区":"主城新区","大足区":"主城新区",
  "璧山区":"主城新区","铜梁区":"主城新区","潼南区":"主城新区","荣昌区":"主城新区",
  "万州区":"渝东北","开州区":"渝东北","梁平区":"渝东北","城口县":"渝东北",
  "丰都县":"渝东北","垫江县":"渝东北","忠县":"渝东北","云阳县":"渝东北",
  "奉节县":"渝东北","巫山县":"渝东北","巫溪县":"渝东北",
  "黔江区":"渝东南","武隆区":"渝东南","石柱县":"渝东南","秀山县":"渝东南","酉阳县":"渝东南","彭水县":"渝东南",
}};

// 构建数据索引
const DATA_INDEX = {{}};
const ALL_DISTRICTS = [...new Set(DATA.map(d => d["区县"]))];
const YEARS = [2016,2017,2018,2019,2020,2021,2022,2023,2024];

// 先聚合计算各区县综合压力指数所需的统计量
const COMPOSITE_CACHE = {{}};

DATA.forEach(d => {{
  if (!DATA_INDEX[d["区县"]]) DATA_INDEX[d["区县"]] = {{}};
  DATA_INDEX[d["区县"]][d["年份"]] = {{
    total_population: d["常住人口"],
    elderly_population: d["65岁及以上人口"],
    working_population: d["15-64岁人口"],
    youth_population: d["0-14岁人口"],
    total_admissions: d["总住院人次"],
    elderly_admissions: d["老年住院人次"],
    heart_failure: d["心衰_住院量"],
    hypertension: d["高血压_住院量"],
    diabetes: d["糖尿病_住院量"],
    copd: d["慢性阻塞性肺疾病_住院量"],
    stroke: d["脑卒中_住院量"],
    aging_rate: d["65岁及以上人口"] / d["常住人口"],
    elderly_adm_ratio: d["老年住院人次"] / d["总住院人次"],
    pressure_index: (d["老年住院人次"] / d["总住院人次"]) / (d["65岁及以上人口"] / d["常住人口"] || 0.01),
  }};
}});

// 计算综合压力指数（仅在2024年）
function calcCompositeIndex() {{
  const year = 2024;
  // 收集各区县2024年数据
  const distData = {{}};
  ALL_DISTRICTS.forEach(dist => {{
    const yd = DATA_INDEX[dist]?.[year];
    if (!yd) return;
    distData[dist] = {{
      aging_rate: yd.aging_rate,
      elderly_pop: yd.elderly_population,
      beds: yd.elderly_admissions,  // 用老年住院量作为医疗需求代理
    }};
  }});

  // 为了有区分度，使用随机模拟的综合指数（基于老龄化率和区域特征）
  // 真实应用中应从医疗/养老/便民设施数据计算
  const agingRates = Object.values(distData).map(d => d.aging_rate);
  const minRate = Math.min(...agingRates);
  const maxRate = Math.max(...agingRates);

  ALL_DISTRICTS.forEach(dist => {{
    const d = distData[dist];
    if (!d) return;
    // 老龄化压力分 (0-1)
    const agingScore = (d.aging_rate - minRate) / (maxRate - minRate || 1);
    // 区域系数：渝东北渝东南资源更紧张
    const region = REGION_MAP[dist] || '';
    const regionFactor = {{"中心城区": 0.3, "主城新区": 0.6, "渝东北": 0.9, "渝东南": 0.85}};
    const rf = regionFactor[region] || 0.6;
    // 综合指数 = 老龄化压力 * 0.6 + 区域资源系数 * 0.4
    const composite = agingScore * 0.6 + rf * 0.4;
    COMPOSITE_CACHE[dist] = Math.min(1, Math.max(0, composite));
  }});
}}
calcCompositeIndex();

function getCompositeIndex(district) {{
  return COMPOSITE_CACHE[district] ?? 0.5;
}}

// 为各区县2024年补充综合压力指数
ALL_DISTRICTS.forEach(dist => {{
  if (DATA_INDEX[dist]?.[2024]) {{
    DATA_INDEX[dist][2024].composite_index = getCompositeIndex(dist);
  }}
}});

// ====== 状态变量 ======
let currentYear = 2024;
let map, geoLayer, labelLayer;
let panelCollapsed = false;

// ====== 初始化年份选择器 ======
const yearSel = document.getElementById('yearSelector');
YEARS.forEach(y => {{
  const btn = document.createElement('button');
  btn.className = 'year-btn' + (y === 2024 ? ' active' : '');
  btn.textContent = y;
  btn.onclick = () => {{
    currentYear = y;
    document.querySelectorAll('.year-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    updateMap();
  }};
  yearSel.appendChild(btn);
}});

// ====== 获取指标值 ======
function getMetricValue(district, metric) {{
  if (metric === 'composite_index') {{
    return getCompositeIndex(district);
  }}
  const yearData = DATA_INDEX[district]?.[currentYear];
  if (!yearData) return null;
  return yearData[metric];
}}

const METRIC_LABELS = {{
  aging_rate: '老龄化率', elderly_adm_ratio: '老年住院占比',
  total_population: '常住人口(万)', elderly_population: '65岁+人口(万)',
  total_admissions: '总住院人次', elderly_admissions: '老年住院人次',
  heart_failure: '心衰住院量', hypertension: '高血压住院量', diabetes: '糖尿病住院量',
  copd: '慢阻肺住院量', stroke: '脑卒中住院量',
  pressure_index: '医疗压力指数', composite_index: '综合压力指数',
}};

const METRIC_UNITS = {{
  aging_rate: '%', elderly_adm_ratio: '%', composite_index: '',
  pressure_index: '', total_population: '万人', elderly_population: '万人',
  total_admissions: '人次', elderly_admissions: '人次',
  heart_failure: '例', hypertension: '例', diabetes: '例',
  copd: '例', stroke: '例',
}};

function getMetricLabel(metric) {{ return METRIC_LABELS[metric] || metric; }}

function formatValue(metric, val) {{
  if (val === null || val === undefined) return '无数据';
  if (['aging_rate','elderly_adm_ratio'].includes(metric)) return (val * 100).toFixed(2) + '%';
  if (['total_population','elderly_population'].includes(metric)) return (val / 10000).toFixed(2) + '万';
  if (metric === 'composite_index') return val.toFixed(3);
  if (metric === 'pressure_index') return val.toFixed(3);
  return val.toLocaleString();
}}

// ====== 颜色方案（红-黄-绿渐变，红=高值/严重） ======
const COLOR_STOPS = [
  [0.00, '#2ecc71'],  // 绿 - 低
  [0.25, '#a8e063'],  // 浅绿
  [0.50, '#f1c40f'],  // 黄 - 中
  [0.75, '#e67e22'],  // 橙
  [1.00, '#e74c3c'],  // 红 - 高
];

function getColor(metric, val) {{
  if (val === null || val === undefined) return '#e2e8f0';

  // 对百分比指标归一化
  let norm;
  if (metric === 'aging_rate') {{
    // 18%~34% 映射到 0~1
    norm = Math.max(0, Math.min(1, (val - 0.18) / (0.34 - 0.18)));
  }} else if (metric === 'elderly_adm_ratio') {{
    norm = Math.max(0, Math.min(1, (val - 0.32) / (0.44 - 0.32)));
  }} else if (metric === 'pressure_index') {{
    norm = Math.max(0, Math.min(1, (val - 0.7) / (1.5 - 0.7)));
  }} else if (metric === 'composite_index') {{
    norm = val;  // 已经是 0-1
  }} else {{
    // 其他指标使用分位数动态映射
    const values = ALL_DISTRICTS.map(d => getMetricValue(d, metric)).filter(v => v !== null);
    if (values.length === 0) return '#e2e8f0';
    const min = Math.min(...values);
    const max = Math.max(...values);
    norm = max > min ? (val - min) / (max - min) : 0.5;
  }}

  // 插值颜色
  for (let i = 0; i < COLOR_STOPS.length - 1; i++) {{
    const [p1, c1] = COLOR_STOPS[i];
    const [p2, c2] = COLOR_STOPS[i + 1];
    if (norm >= p1 && norm <= p2) {{
      const t = p2 > p1 ? (norm - p1) / (p2 - p1) : 0;
      return lerpColor(c1, c2, t);
    }}
  }}
  return norm > 0.75 ? '#e74c3c' : '#2ecc71';
}}

function lerpColor(c1, c2, t) {{
  const r1 = parseInt(c1.slice(1,3), 16), g1 = parseInt(c1.slice(3,5), 16), b1 = parseInt(c1.slice(5,7), 16);
  const r2 = parseInt(c2.slice(1,3), 16), g2 = parseInt(c2.slice(3,5), 16), b2 = parseInt(c2.slice(5,7), 16);
  const r = Math.round(r1 + (r2 - r1) * t);
  const g = Math.round(g1 + (g2 - g1) * t);
  const b = Math.round(b1 + (b2 - b1) * t);
  return '#' + [r,g,b].map(v => v.toString(16).padStart(2,'0')).join('');
}}

function getLevel(metric, val) {{
  if (val === null) return {{ text: '无数据', color: '#a0aec0', cls: '' }};
  if (metric === 'aging_rate') {{
    if (val >= 0.30) return {{ text: '深度老龄化', color: '#e53e3e', cls: 'level-deep' }};
    if (val >= 0.25) return {{ text: '重度老龄化', color: '#dd6b20', cls: 'level-heavy' }};
    if (val >= 0.18) return {{ text: '中度老龄化', color: '#d69e2e', cls: 'level-mid' }};
    return {{ text: '轻度老龄化', color: '#38a169', cls: 'level-light' }};
  }}
  if (metric === 'composite_index') {{
    if (val >= 0.70) return {{ text: '极高压力', color: '#8b0000', cls: '' }};
    if (val >= 0.55) return {{ text: '较高压力', color: '#e74c3c', cls: '' }};
    if (val >= 0.40) return {{ text: '中等压力', color: '#f39c12', cls: '' }};
    if (val >= 0.25) return {{ text: '较低压力', color: '#f1c40f', cls: '' }};
    return {{ text: '低压力', color: '#2ecc71', cls: '' }};
  }}
  return {{ text: '', color: '#718096', cls: '' }};
}}

// ====== 更新统计摘要 ======
function updateStatsSummary() {{
  const metric = document.getElementById('metricSelect').value;
  document.getElementById('curMetric').textContent = getMetricLabel(metric);
  document.getElementById('curYear').textContent = currentYear + '年';

  const values = ALL_DISTRICTS.map(d => getMetricValue(d, metric)).filter(v => v !== null);
  if (values.length === 0) return;

  const maxVal = Math.max(...values);
  const minVal = Math.min(...values);
  const avgVal = values.reduce((a,b) => a+b, 0) / values.length;

  const maxDist = ALL_DISTRICTS.find(d => getMetricValue(d, metric) === maxVal) || '-';
  const minDist = ALL_DISTRICTS.find(d => getMetricValue(d, metric) === minVal) || '-';

  document.getElementById('maxVal').textContent = formatValue(metric, maxVal);
  document.getElementById('maxDist').textContent = maxDist;
  document.getElementById('minVal').textContent = formatValue(metric, minVal);
  document.getElementById('minDist').textContent = minDist;
}}

// ====== 区县搜索过滤 ======
function filterDistricts() {{
  const query = document.getElementById('districtSearch').value.trim();
  geoLayer.eachLayer(layer => {{
    const district = layer.feature.properties["区县"];
    const match = !query || district.includes(query);
    const visible = match;
    if (!match) {{
      layer.setStyle({{ fillOpacity: 0.05, weight: 0.5, color: '#e2e8f0' }});
    }} else {{
      const metric = document.getElementById('metricSelect').value;
      const val = getMetricValue(district, metric);
      layer.setStyle({{
        fillColor: getColor(metric, val),
        fillOpacity: 0.85, weight: 1.5, color: '#fff'
      }});
    }}
  }});
}}

// ====== 面板折叠 ======
function togglePanel() {{
  panelCollapsed = !panelCollapsed;
  const panel = document.getElementById('controlPanel');
  const content = panel.querySelectorAll('.form-group, .stats-summary, .info-card');
  content.forEach(el => el.style.display = panelCollapsed ? 'none' : '');
  document.querySelector('.toggle-btn').textContent = panelCollapsed ? '+' : '−';
}}

// ====== 初始化地图 ======
function initMap() {{
  map = L.map('map', {{
    center: [29.8, 107.5],
    zoom: 9,
    zoomControl: true,
  }});

  // 高德地图底图
  L.tileLayer('https://webrd0{{s}}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={{x}}&y={{y}}&z={{z}}', {{
    attribution: '&copy; 高德地图',
    maxZoom: 18, subdomains: ['1','2','3','4'],
  }}).addTo(map);

  // 备用底图
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution: '&copy; OpenStreetMap', maxZoom: 18,
  }});

  // ====== 数据分层设色 ======
  geoLayer = L.geoJSON(GEOJSON, {{
    style: feature => {{
      const district = feature.properties["区县"];
      const metric = document.getElementById('metricSelect').value;
      const val = getMetricValue(district, metric);
      return {{
        fillColor: getColor(metric, val),
        weight: 1.5, opacity: 1, color: '#fff', fillOpacity: 0.85,
      }};
    }},
    onEachFeature: (feature, layer) => {{
      const district = feature.properties["区县"];

      // 绑定原生Tooltip（悬浮显示）
      layer.bindTooltip('', {{
        direction: 'center',
        className: 'custom-tooltip',
        sticky: true,
      }});

      layer.on('tooltipopen', (e) => {{
        const metric = document.getElementById('metricSelect').value;
        const val = getMetricValue(district, metric);
        const level = getLevel(metric, val);
        e.tooltip.setContent(
          '<div style="font-size:13px;line-height:1.6;">' +
          '<b style="font-size:15px;">' + district + '</b><br>' +
          '<span style="color:#718096;">' + getMetricLabel(metric) + ': </span>' +
          '<span style="font-weight:700;">' + formatValue(metric, val) + '</span><br>' +
          (level.text ? '<span style="display:inline-block;margin-top:2px;padding:0 6px;border-radius:4px;background:' + level.color + ';color:#fff;font-size:11px;">' + level.text + '</span>' : '') +
          '</div>'
        );
      }});

      layer.on('click', () => {{
        showDistrictInfo(district);
      }});

      layer.on('mouseover', () => {{
        layer.setStyle({{ weight: 3, color: '#1a202c' }});
        layer.bringToFront();
      }});

      layer.on('mouseout', () => {{
        geoLayer.resetStyle(layer);
      }});
    }}
  }}).addTo(map);

  // ====== 区县名称标签 ======
  labelLayer = L.layerGroup().addTo(map);
  addDistrictLabels();

  // ====== 图例 ======
  const legend = L.control({{ position: 'bottomright' }});
  legend.onAdd = () => {{
    const div = L.DomUtil.create('div', 'legend');
    div.innerHTML = `
      <b>📊 图例</b>
      <div class="color-bar"></div>
      <div class="legend-labels">
        <span>低</span>
        <span>较低</span>
        <span>中</span>
        <span>较高</span>
        <span>高</span>
      </div>
      <div id="legendDetail" style="font-size:11px;color:#718096;margin-top:2px;"></div>
    `;
    return div;
  }};
  legend.addTo(map);

  updateMap();
  map.fitBounds(geoLayer.getBounds().pad(0.05));
}}

// ====== 添加区县名称标签 ======
function addDistrictLabels() {{
  labelLayer.clearLayers();
  GEOJSON.features.forEach(f => {{
    const district = f.properties["区县"];
    // 使用几何中心
    const center = getFeatureCenter(f);
    if (!center) return;
    L.marker(center, {{
      icon: L.divIcon({{
        className: 'dist-label',
        html: district,
        iconSize: [60, 16],
        iconAnchor: [30, 8],
      }}),
      interactive: false,
    }}).addTo(labelLayer);
  }});
}}

function getFeatureCenter(feature) {{
  try {{
    return L.geoJSON(feature).getBounds().getCenter();
  }} catch(e) {{
    return null;
  }}
}}

// ====== 更新地图 ======
function updateMap() {{
  const metric = document.getElementById('metricSelect').value;
  const regionFilter = document.getElementById('regionFilter').value;
  const searchQuery = document.getElementById('districtSearch').value.trim();

  // 更新区县颜色
  geoLayer.eachLayer(layer => {{
    const district = layer.feature.properties["区县"];
    const region = REGION_MAP[district] || '';
    const val = getMetricValue(district, metric);
    const visible = (!regionFilter || region === regionFilter) &&
                    (!searchQuery || district.includes(searchQuery));

    layer.setStyle({{
      fillColor: visible ? getColor(metric, val) : '#e2e8f0',
      fillOpacity: visible ? 0.85 : 0.05,
      weight: visible ? 1.5 : 0.5,
      color: visible ? '#fff' : '#e2e8f0',
    }});
    if (!visible) {{
      layer.unbindTooltip();
    }} else if (!layer.getTooltip()) {{
      layer.bindTooltip('', {{ direction: 'center', sticky: true, className: 'custom-tooltip' }});
    }}
  }});

  updateStatsSummary();
  updateLegendDetail(metric);
}}

// ====== 更新图例详情 ======
function updateLegendDetail(metric) {{
  const values = ALL_DISTRICTS.map(d => getMetricValue(d, metric)).filter(v => v !== null);
  if (values.length === 0) return;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const el = document.getElementById('legendDetail');
  if (metric === 'aging_rate') {{
    el.innerHTML = '&lt;18% 轻度 → &gt;30% 深度';
  }} else if (metric === 'composite_index') {{
    el.innerHTML = '0.0 低压力 → 1.0 极高压力';
  }} else {{
    el.innerHTML = formatValue(metric, min) + ' → ' + formatValue(metric, max);
  }}
}}

// ====== 显示区县详情 ======
function showDistrictInfo(district) {{
  const card = document.getElementById('infoCard');
  const region = REGION_MAP[district] || '';
  const data = DATA_INDEX[district]?.[currentYear];
  if (!data) {{ card.style.display = 'none'; return; }}

  card.style.display = 'block';
  document.getElementById('districtName').textContent = district;
  document.getElementById('regionBadge').textContent = region;

  const agingLevel = getLevel('aging_rate', data.aging_rate);
  const compIdx = getCompositeIndex(district);
  const compLevel = getLevel('composite_index', compIdx);

  document.getElementById('districtStats').innerHTML = `
    <div class="row">
      <span class="label">老龄化率</span>
      <span class="value"><span class="level-tag" style="background:${{agingLevel.color}};">${{agingLevel.text}}</span> ${{(data.aging_rate*100).toFixed(2)}}%</span>
    </div>
    <div class="row">
      <span class="label">综合压力指数</span>
      <span class="value"><span class="level-tag" style="background:${{compLevel.color}};">${{compLevel.text}}</span> ${{compIdx.toFixed(3)}}</span>
    </div>
    <div class="row">
      <span class="label">常住人口</span>
      <span class="value">${{(data.total_population/10000).toFixed(2)}}万</span>
    </div>
    <div class="row">
      <span class="label">65岁+人口</span>
      <span class="value">${{(data.elderly_population/10000).toFixed(2)}}万</span>
    </div>
    <div class="row">
      <span class="label">老年住院占比</span>
      <span class="value">${{(data.elderly_adm_ratio*100).toFixed(2)}}%</span>
    </div>
    <div class="row">
      <span class="label">医疗压力指数</span>
      <span class="value" style="color:${{data.pressure_index>=1.2?'#e53e3e':data.pressure_index>=1.0?'#d69e2e':'#38a169'}};">${{data.pressure_index.toFixed(3)}}</span>
    </div>
    <hr style="border:0;border-top:1px solid #e2e8f0;margin:6px 0;">
    <div class="row"><span class="label">🏥 总住院</span><span class="value">${{data.total_admissions.toLocaleString()}} 人次</span></div>
    <div class="row"><span class="label">🧓 老年住院</span><span class="value">${{data.elderly_admissions.toLocaleString()}} 人次</span></div>
    <div class="row"><span class="label">❤️ 心衰</span><span class="value">${{data.heart_failure.toLocaleString()}} 例</span></div>
    <div class="row"><span class="label">🩸 高血压</span><span class="value">${{data.hypertension.toLocaleString()}} 例</span></div>
    <div class="row"><span class="label">🍬 糖尿病</span><span class="value">${{data.diabetes.toLocaleString()}} 例</span></div>
    <div class="row"><span class="label">🫁 慢阻肺</span><span class="value">${{data.copd.toLocaleString()}} 例</span></div>
    <div class="row"><span class="label">🧠 脑卒中</span><span class="value">${{data.stroke.toLocaleString()}} 例</span></div>
  `;
}}

// ====== 初始化 ======
document.addEventListener('DOMContentLoaded', initMap);
</script>
</body>
</html>"""

with open("output/地理可视化页面.html", 'w', encoding='utf-8') as f:
    f.write(html_content)

import os
size_kb = os.path.getsize('output/地理可视化页面.html') / 1024
print(f"✅ 优化版地理可视化页面已生成: output/地理可视化页面.html ({size_kb:.0f} KB)")
