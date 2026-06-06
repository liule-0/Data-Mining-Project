"""生成医疗压力数据查询HTML"""
import json

# 读取数据
with open('output/healthcare_data.json', 'r', encoding='utf-8') as f:
    records = json.load(f)

data_json = json.dumps(records, ensure_ascii=False)

# 区域分类映射
district_region = {
    "渝中区": "中心城区", "江北区": "中心城区", "南岸区": "中心城区",
    "九龙坡区": "中心城区", "沙坪坝区": "中心城区", "大渡口区": "中心城区",
    "渝北区": "中心城区", "巴南区": "中心城区", "北碚区": "中心城区",
    "涪陵区": "主城新区", "长寿区": "主城新区", "江津区": "主城新区",
    "合川区": "主城新区", "永川区": "主城新区", "南川区": "主城新区",
    "綦江区": "主城新区", "大足区": "主城新区", "璧山区": "主城新区",
    "铜梁区": "主城新区", "潼南区": "主城新区", "荣昌区": "主城新区",
    "万州区": "渝东北", "开州区": "渝东北", "梁平区": "渝东北",
    "城口县": "渝东北", "丰都县": "渝东北", "垫江县": "渝东北",
    "忠县": "渝东北", "云阳县": "渝东北", "奉节县": "渝东北",
    "巫山县": "渝东北", "巫溪县": "渝东北",
    "黔江区": "渝东南", "武隆区": "渝东南", "石柱县": "渝东南",
    "秀山县": "渝东南", "酉阳县": "渝东南", "彭水县": "渝东南",
}

districts = sorted(set(r["区县"] for r in records))

html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>重庆市医疗压力数据查询系统</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: #f0f4f8; color: #1a202c; }}
.header {{ background: linear-gradient(135deg, #1a365d 0%, #2b6cb0 100%); color: white; padding: 24px 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
.header h1 {{ font-size: 24px; font-weight: 600; margin-bottom: 4px; }}
.header p {{ font-size: 14px; opacity: 0.85; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
.query-panel {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }}
.query-panel h2 {{ font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #2d3748; }}
.query-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }}
.query-item {{ display: flex; flex-direction: column; }}
.query-item label {{ font-size: 13px; font-weight: 600; color: #4a5568; margin-bottom: 6px; }}
.query-item select, .query-item input {{ padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px; background: #f7fafc; outline: none; transition: border-color 0.2s; }}
.query-item select:focus, .query-item input:focus {{ border-color: #3182ce; box-shadow: 0 0 0 3px rgba(49,130,206,0.15); }}
.query-item input[type="number"] {{ width: 100%; }}
.query-actions {{ display: flex; gap: 12px; margin-top: 20px; flex-wrap: wrap; }}
.btn {{ padding: 10px 24px; border: none; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; }}
.btn-primary {{ background: #3182ce; color: white; }}
.btn-primary:hover {{ background: #2c5282; }}
.btn-success {{ background: #38a169; color: white; }}
.btn-success:hover {{ background: #276749; }}
.btn-outline {{ background: white; color: #4a5568; border: 1px solid #e2e8f0; }}
.btn-outline:hover {{ background: #f7fafc; }}
.stats-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px; }}
.stat-card {{ background: white; border-radius: 10px; padding: 16px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.06); border-left: 4px solid #3182ce; }}
.stat-card .label {{ font-size: 12px; color: #718096; margin-bottom: 4px; }}
.stat-card .value {{ font-size: 22px; font-weight: 700; color: #2d3748; }}
.stat-card .sub {{ font-size: 12px; color: #a0aec0; margin-top: 2px; }}
.table-container {{ overflow-x: auto; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
thead {{ background: #2d3748; color: white; }}
th {{ padding: 12px 14px; text-align: left; font-weight: 600; white-space: nowrap; cursor: pointer; user-select: none; }}
th:hover {{ background: #4a5568; }}
th .sort-icon {{ margin-left: 4px; font-size: 10px; }}
td {{ padding: 10px 14px; border-bottom: 1px solid #e2e8f0; }}
tr:hover {{ background: #ebf8ff; }}
tr:nth-child(even) {{ background: #f7fafc; }}
tr:nth-child(even):hover {{ background: #ebf8ff; }}
.region-badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
.region-中心城区 {{ background: #ebf8ff; color: #2b6cb0; }}
.region-主城新区 {{ background: #f0fff4; color: #276749; }}
.region-渝东北 {{ background: #fffaf0; color: #c05621; }}
.region-渝东南 {{ background: #faf5ff; color: #6b46c1; }}
.chart-container {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }}
.chart-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
@media (max-width: 900px) {{ .chart-grid {{ grid-template-columns: 1fr; }} }}
.chart-box {{ position: relative; height: 350px; }}
.export-bar {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-top: 12px; }}
#recordCount {{ font-size: 13px; color: #718096; margin-left: auto; }}
.tabs {{ display: flex; gap: 0; margin-bottom: 16px; border-bottom: 2px solid #e2e8f0; }}
.tab {{ padding: 10px 24px; cursor: pointer; font-size: 14px; font-weight: 600; color: #718096; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.2s; }}
.tab.active {{ color: #3182ce; border-bottom-color: #3182ce; }}
.tab:hover {{ color: #2c5282; }}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; }}
.footer {{ text-align: center; padding: 20px; color: #a0aec0; font-size: 12px; }}
</style>
</head>
<body>

<div class="header">
  <h1>重庆市医疗压力数据查询系统</h1>
  <p>重庆市人口老龄化与医疗压力数据挖掘项目 · 2016-2024年各区县住院数据</p>
</div>

<div class="container">
  <!-- 查询面板 -->
  <div class="query-panel">
    <h2>查询条件</h2>
    <div class="query-grid">
      <div class="query-item">
        <label>区县</label>
        <select id="districtFilter">
          <option value="">全部区县</option>
        </select>
      </div>
      <div class="query-item">
        <label>区域类型</label>
        <select id="regionFilter">
          <option value="">全部区域</option>
          <option value="中心城区">中心城区</option>
          <option value="主城新区">主城新区</option>
          <option value="渝东北">渝东北</option>
          <option value="渝东南">渝东南</option>
        </select>
      </div>
      <div class="query-item">
        <label>起始年份</label>
        <select id="yearFrom">
          <option value="2016">2016</option>
          <option value="2017">2017</option>
          <option value="2018">2018</option>
          <option value="2019">2019</option>
          <option value="2020">2020</option>
          <option value="2021">2021</option>
          <option value="2022">2022</option>
          <option value="2023">2023</option>
          <option value="2024">2024</option>
        </select>
      </div>
      <div class="query-item">
        <label>结束年份</label>
        <select id="yearTo">
          <option value="2016">2016</option>
          <option value="2017">2017</option>
          <option value="2018">2018</option>
          <option value="2019">2019</option>
          <option value="2020">2020</option>
          <option value="2021">2021</option>
          <option value="2022">2022</option>
          <option value="2023">2023</option>
          <option value="2024" selected>2024</option>
        </select>
      </div>
      <div class="query-item">
        <label>最小总住院人次</label>
        <input type="number" id="minAdmissions" placeholder="0" min="0">
      </div>
      <div class="query-item">
        <label>排序方式</label>
        <select id="sortBy">
          <option value="年份">年份</option>
          <option value="总住院人次">总住院人次</option>
          <option value="老年住院人次">老年住院人次</option>
          <option value="老年住院占比">老年住院占比</option>
        </select>
      </div>
      <div class="query-item">
        <label>排序方向</label>
        <select id="sortDir">
          <option value="desc">降序</option>
          <option value="asc">升序</option>
        </select>
      </div>
    </div>
    <div class="query-actions">
      <button class="btn btn-primary" onclick="doQuery()">查询</button>
      <button class="btn btn-outline" onclick="resetQuery()">重置</button>
      <button class="btn btn-success" onclick="exportCSV()">导出CSV</button>
    </div>
  </div>

  <!-- 统计卡片 -->
  <div class="stats-grid" id="statsCards"></div>

  <!-- 标签切换 -->
  <div class="tabs">
    <div class="tab active" onclick="switchTab('table', this)">数据表格</div>
    <div class="tab" onclick="switchTab('chart', this)">趋势图表</div>
  </div>

  <!-- 数据表格 -->
  <div id="tab-table" class="tab-content active">
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th onclick="sortTable('区县')">区县 <span class="sort-icon">↕</span></th>
            <th onclick="sortTable('区域')">区域 <span class="sort-icon">↕</span></th>
            <th onclick="sortTable('年份')">年份 <span class="sort-icon">↕</span></th>
            <th onclick="sortTable('总住院人次')">总住院人次 <span class="sort-icon">↕</span></th>
            <th onclick="sortTable('老年住院人次')">老年住院人次 <span class="sort-icon">↕</span></th>
            <th onclick="sortTable('老年住院占比')">老年住院占比 <span class="sort-icon">↕</span></th>
            <th>心衰</th>
            <th>高血压</th>
            <th>糖尿病</th>
            <th>慢阻肺</th>
            <th>脑卒中</th>
          </tr>
        </thead>
        <tbody id="resultBody"></tbody>
      </table>
    </div>
    <div class="export-bar">
      <span id="recordCount">共 0 条记录</span>
    </div>
  </div>

  <!-- 图表 -->
  <div id="tab-chart" class="tab-content">
    <div class="chart-grid">
      <div class="chart-container">
        <h3 style="margin-bottom:12px;font-size:15px;color:#2d3748;">老年住院占比趋势</h3>
        <div class="chart-box"><canvas id="elderlyRatioChart"></canvas></div>
      </div>
      <div class="chart-container">
        <h3 style="margin-bottom:12px;font-size:15px;color:#2d3748;">慢性病住院量趋势</h3>
        <div class="chart-box"><canvas id="diseaseChart"></canvas></div>
      </div>
      <div class="chart-container">
        <h3 style="margin-bottom:12px;font-size:15px;color:#2d3748;">各区县总住院人次对比</h3>
        <div class="chart-box"><canvas id="districtChart"></canvas></div>
      </div>
      <div class="chart-container">
        <h3 style="margin-bottom:12px;font-size:15px;color:#2d3748;">各区域老年住院占比对比</h3>
        <div class="chart-box"><canvas id="regionChart"></canvas></div>
      </div>
    </div>
  </div>

  <div class="footer">
    重庆人口老龄化与医疗压力数据挖掘 &copy; 2026
  </div>
</div>

<script>
// ========== 数据 ==========
const RAW_DATA = {data_json};

// 区域映射
const REGION_MAP = {json.dumps(district_region, ensure_ascii=False)};

// 补充区域信息
const DATA = RAW_DATA.map(d => ({{...d, 区域: REGION_MAP[d["区县"]] || "其他", 老年住院占比: d["老年住院人次"] / d["总住院人次"]}}));

const DISTRICTS = {json.dumps(districts, ensure_ascii=False)};
const DISEASE_KEYS = ["心衰_住院量", "高血压_住院量", "糖尿病_住院量", "慢性阻塞性肺疾病_住院量", "脑卒中_住院量"];
const DISEASE_NAMES = ["心衰", "高血压", "糖尿病", "慢阻肺", "脑卒中"];
const YEARS = [2016,2017,2018,2019,2020,2021,2022,2023,2024];

let currentData = [];
let chartInstances = {{}};
let sortState = {{key: null, dir: 'desc'}};

// 初始化区县下拉
DISTRICTS.forEach(d => {{
  const opt = document.createElement('option');
  opt.value = d; opt.textContent = d;
  document.getElementById('districtFilter').appendChild(opt);
}});

// ========== 查询 ==========
function doQuery() {{
  const district = document.getElementById('districtFilter').value;
  const region = document.getElementById('regionFilter').value;
  const yFrom = parseInt(document.getElementById('yearFrom').value);
  const yTo = parseInt(document.getElementById('yearTo').value);
  const minAdm = parseInt(document.getElementById('minAdmissions').value) || 0;
  const sortKey = document.getElementById('sortBy').value;
  const sortDir = document.getElementById('sortDir').value;

  currentData = DATA.filter(d => {{
    if (district && d["区县"] !== district) return false;
    if (region && d["区域"] !== region) return false;
    if (d["年份"] < yFrom || d["年份"] > yTo) return false;
    if (d["总住院人次"] < minAdm) return false;
    return true;
  }});

  // 排序
  if (sortKey === "年份") {{
    currentData.sort((a, b) => sortDir === 'desc' ? b["年份"] - a["年份"] : a["年份"] - b["年份"]);
  }} else if (sortKey === "老年住院占比") {{
    currentData.sort((a, b) => sortDir === 'desc' ? b["老年住院占比"] - a["老年住院占比"] : a["老年住院占比"] - b["老年住院占比"]);
  }} else {{
    currentData.sort((a, b) => sortDir === 'desc' ? b[sortKey] - a[sortKey] : a[sortKey] - b[sortKey]);
  }}

  renderTable();
  renderStats();
  renderCharts();
}}

function resetQuery() {{
  document.getElementById('districtFilter').value = '';
  document.getElementById('regionFilter').value = '';
  document.getElementById('yearFrom').value = '2016';
  document.getElementById('yearTo').value = '2024';
  document.getElementById('minAdmissions').value = '';
  document.getElementById('sortBy').value = '年份';
  document.getElementById('sortDir').value = 'desc';
  doQuery();
}}

// ========== 表格渲染 ==========
function renderTable() {{
  const tbody = document.getElementById('resultBody');
  tbody.innerHTML = currentData.map(d => `
    <tr>
      <td><strong>${{d["区县"]}}</strong></td>
      <td><span class="region-badge region-${{d["区域"]}}">${{d["区域"]}}</span></td>
      <td>${{d["年份"]}}</td>
      <td>${{d["总住院人次"].toLocaleString()}}</td>
      <td>${{d["老年住院人次"].toLocaleString()}}</td>
      <td>${{(d["老年住院占比"]*100).toFixed(1)}}%</td>
      <td>${{d["心衰_住院量"].toLocaleString()}}</td>
      <td>${{d["高血压_住院量"].toLocaleString()}}</td>
      <td>${{d["糖尿病_住院量"].toLocaleString()}}</td>
      <td>${{d["慢性阻塞性肺疾病_住院量"].toLocaleString()}}</td>
      <td>${{d["脑卒中_住院量"].toLocaleString()}}</td>
    </tr>
  `).join('');
  document.getElementById('recordCount').textContent = `共 ${{currentData.length}} 条记录`;
}}

// ========== 统计卡片 ==========
function renderStats() {{
  if (currentData.length === 0) {{ document.getElementById('statsCards').innerHTML = '<div style="color:#718096;padding:20px;">无匹配数据</div>'; return; }}
  const totalAdm = currentData.reduce((s, d) => s + d["总住院人次"], 0);
  const totalElderly = currentData.reduce((s, d) => s + d["老年住院人次"], 0);
  const avgRatio = currentData.reduce((s, d) => s + d["老年住院占比"], 0) / currentData.length;
  const totalHeart = currentData.reduce((s, d) => s + d["心衰_住院量"], 0);
  const totalHBP = currentData.reduce((s, d) => s + d["高血压_住院量"], 0);
  const totalDM = currentData.reduce((s, d) => s + d["糖尿病_住院量"], 0);
  const distinctDistricts = new Set(currentData.map(d => d["区县"])).size;
  document.getElementById('statsCards').innerHTML = `
    <div class="stat-card" style="border-left-color:#3182ce;">
      <div class="label">总住院人次</div>
      <div class="value">${{totalAdm.toLocaleString()}}</div>
      <div class="sub">覆盖 ${{distinctDistricts}} 个区县</div>
    </div>
    <div class="stat-card" style="border-left-color:#e53e3e;">
      <div class="label">老年住院人次</div>
      <div class="value">${{totalElderly.toLocaleString()}}</div>
      <div class="sub">占总住院 ${{(totalElderly/totalAdm*100).toFixed(1)}}%</div>
    </div>
    <div class="stat-card" style="border-left-color:#38a169;">
      <div class="label">平均老年住院占比</div>
      <div class="value">${{(avgRatio*100).toFixed(1)}}%</div>
      <div class="sub">${{currentData.length}} 条记录</div>
    </div>
    <div class="stat-card" style="border-left-color:#d69e2e;">
      <div class="label">心衰住院量</div>
      <div class="value">${{totalHeart.toLocaleString()}}</div>
      <div class="sub">2016→2024 增长显著</div>
    </div>
    <div class="stat-card" style="border-left-color:#805ad5;">
      <div class="label">高血压住院量</div>
      <div class="value">${{totalHBP.toLocaleString()}}</div>
      <div class="sub">最常见的慢性病</div>
    </div>
    <div class="stat-card" style="border-left-color:#dd6b20;">
      <div class="label">糖尿病住院量</div>
      <div class="value">${{totalDM.toLocaleString()}}</div>
      <div class="sub">增长迅速</div>
    </div>
  `;
}}

// ========== 排序 ==========
function sortTable(key) {{
  if (sortState.key === key) {{
    sortState.dir = sortState.dir === 'desc' ? 'asc' : 'desc';
  }} else {{
    sortState.key = key;
    sortState.dir = 'desc';
  }}
  document.getElementById('sortBy').value = key;
  document.getElementById('sortDir').value = sortState.dir;
  doQuery();
}}

// ========== 图表 ==========
function renderCharts() {{
  if (currentData.length === 0) return;
  renderElderlyRatioChart();
  renderDiseaseChart();
  renderDistrictChart();
  renderRegionChart();
}}

function renderElderlyRatioChart() {{
  const ctx = document.getElementById('elderlyRatioChart').getContext('2d');
  if (chartInstances.elderly) chartInstances.elderly.destroy();

  // 按年份分组计算平均老年住院占比
  const yearData = {{}};
  currentData.forEach(d => {{
    if (!yearData[d["年份"]]) yearData[d["年份"]] = [];
    yearData[d["年份"]].push(d["老年住院占比"]);
  }});

  const labels = Object.keys(yearData).sort();
  const ratios = labels.map(y => yearData[y].reduce((a,b) => a+b, 0) / yearData[y].length);

  chartInstances.elderly = new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: labels.map(y => y + '年'),
      datasets: [{{
        label: '老年住院占比',
        data: ratios.map(r => (r*100).toFixed(1)),
        borderColor: '#e53e3e',
        backgroundColor: 'rgba(229,62,62,0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 5,
        pointBackgroundColor: '#e53e3e',
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ tooltip: {{ callbacks: {{ label: ctx => ctx.parsed.y + '%' }} }} }},
      scales: {{ y: {{ beginAtZero: false, ticks: {{ callback: v => v + '%' }} }} }}
    }}
  }});
}}

function renderDiseaseChart() {{
  const ctx = document.getElementById('diseaseChart').getContext('2d');
  if (chartInstances.disease) chartInstances.disease.destroy();

  const yearData = {{}};
  currentData.forEach(d => {{
    if (!yearData[d["年份"]]) yearData[d["年份"]] = {{}};
    DISEASE_KEYS.forEach((k, i) => {{
      if (!yearData[d["年份"]][k]) yearData[d["年份"]][k] = 0;
      yearData[d["年份"]][k] += d[k];
    }});
  }});

  const labels = Object.keys(yearData).sort();
  const colors = ['#e53e3e', '#d69e2e', '#38a169', '#3182ce', '#805ad5'];

  chartInstances.disease = new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: labels.map(y => y + '年'),
      datasets: DISEASE_KEYS.map((k, i) => ({{
        label: DISEASE_NAMES[i],
        data: labels.map(y => (yearData[y][k] || 0)),
        borderColor: colors[i],
        backgroundColor: colors[i] + '22',
        fill: false,
        tension: 0.3,
        pointRadius: 3,
      }}))
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{ y: {{ beginAtZero: true }} }}
    }}
  }});
}}

function renderDistrictChart() {{
  const ctx = document.getElementById('districtChart').getContext('2d');
  if (chartInstances.district) chartInstances.district.destroy();

  // 按区县汇总总住院人次
  const distData = {{}};
  currentData.forEach(d => {{
    if (!distData[d["区县"]]) distData[d["区县"]] = 0;
    distData[d["区县"]] += d["总住院人次"];
  }});

  const labels = Object.keys(distData);
  const vals = labels.map(l => distData[l]);

  chartInstances.district = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: labels,
      datasets: [{{
        label: '总住院人次',
        data: vals,
        backgroundColor: 'rgba(49,130,206,0.7)',
        borderColor: '#3182ce',
        borderWidth: 1,
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {{ legend: {{ display: false }} }},
      scales: {{ x: {{ beginAtZero: true }} }}
    }}
  }});
}}

function renderRegionChart() {{
  const ctx = document.getElementById('regionChart').getContext('2d');
  if (chartInstances.region) chartInstances.region.destroy();

  const regionData = {{}};
  currentData.forEach(d => {{
    if (!regionData[d["区域"]]) regionData[d["区域"]] = {{sum: 0, count: 0}};
    regionData[d["区域"]].sum += d["老年住院占比"];
    regionData[d["区域"]].count += 1;
  }});

  const labels = Object.keys(regionData);
  const ratios = labels.map(l => (regionData[l].sum / regionData[l].count * 100).toFixed(1));
  const colors = {{
    '中心城区': 'rgba(49,130,206,0.7)',
    '主城新区': 'rgba(56,161,105,0.7)',
    '渝东北': 'rgba(214,158,46,0.7)',
    '渝东南': 'rgba(128,90,213,0.7)',
  }};

  chartInstances.region = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: labels,
      datasets: [{{
        label: '老年住院占比(%)',
        data: ratios,
        backgroundColor: labels.map(l => colors[l] || 'rgba(160,174,192,0.7)'),
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{ y: {{ beginAtZero: false, ticks: {{ callback: v => v + '%' }} }} }}
    }}
  }});
}}

// ========== 标签切换 ==========
function switchTab(name, el) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
  if (name === 'chart') setTimeout(renderCharts, 100);
}}

// ========== 导出CSV ==========
function exportCSV() {{
  if (currentData.length === 0) {{ alert('没有数据可导出'); return; }}
  const headers = ['区县','区域','年份','总住院人次','老年住院人次','老年住院占比','心衰','高血压','糖尿病','慢阻肺','脑卒中'];
  const rows = currentData.map(d => [
    d["区县"], d["区域"], d["年份"], d["总住院人次"], d["老年住院人次"],
    (d["老年住院占比"]*100).toFixed(2) + '%',
    d["心衰_住院量"], d["高血压_住院量"], d["糖尿病_住院量"],
    d["慢性阻塞性肺疾病_住院量"], d["脑卒中_住院量"]
  ]);
  const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\\n');
  const blob = new Blob(['\\ufeff' + csv], {{type: 'text/csv;charset=utf-8;'}});
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = '医疗压力数据查询结果.csv';
  link.click();
}}

// ========== 初始化 ==========
doQuery();
</script>
</body>
</html>"""

# 写入文件
output_path = "output/医疗压力数据查询系统.html"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"HTML文件已生成: {output_path}")
print(f"文件大小: {len(html_content.encode('utf-8'))} 字节")
