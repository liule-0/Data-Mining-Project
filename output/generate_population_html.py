"""生成人口数据查询HTML页面"""
import json

# 读取数据
with open('output/population_data.json', 'r', encoding='utf-8') as f:
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

html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>重庆市人口数据查询系统</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: #f0f4f8; color: #1a202c; }}
.header {{ background: linear-gradient(135deg, #276749 0%, #38a169 100%); color: white; padding: 24px 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
.header h1 {{ font-size: 24px; font-weight: 600; margin-bottom: 4px; }}
.header p {{ font-size: 14px; opacity: 0.85; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
.query-panel {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }}
.query-panel h2 {{ font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #2d3748; }}
.query-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }}
.query-item {{ display: flex; flex-direction: column; }}
.query-item label {{ font-size: 13px; font-weight: 600; color: #4a5568; margin-bottom: 6px; }}
.query-item select, .query-item input {{ padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px; background: #f7fafc; outline: none; transition: border-color 0.2s; }}
.query-item select:focus, .query-item input:focus {{ border-color: #38a169; box-shadow: 0 0 0 3px rgba(56,161,105,0.15); }}
.query-item input {{ width: 100%; }}
.query-actions {{ display: flex; gap: 12px; margin-top: 20px; flex-wrap: wrap; }}
.btn {{ padding: 10px 24px; border: none; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; }}
.btn-primary {{ background: #38a169; color: white; }}
.btn-primary:hover {{ background: #276749; }}
.btn-success {{ background: #3182ce; color: white; }}
.btn-success:hover {{ background: #2c5282; }}
.btn-outline {{ background: white; color: #4a5568; border: 1px solid #e2e8f0; }}
.btn-outline:hover {{ background: #f7fafc; }}
.stats-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px; }}
.stat-card {{ background: white; border-radius: 10px; padding: 16px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
.stat-card .label {{ font-size: 12px; color: #718096; margin-bottom: 4px; }}
.stat-card .value {{ font-size: 22px; font-weight: 700; color: #2d3748; }}
.stat-card .sub {{ font-size: 12px; color: #a0aec0; margin-top: 2px; }}
.aging-level {{ display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
.level-轻度 {{ background: #c6f6d5; color: #22543d; }}
.level-中度 {{ background: #fefcbf; color: #744210; }}
.level-重度 {{ background: #fed7d7; color: #822727; }}
.level-深度 {{ background: #e2e8f0; color: #1a202c; }}
.table-container {{ overflow-x: auto; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
thead {{ background: #2d3748; color: white; }}
th {{ padding: 12px 14px; text-align: left; font-weight: 600; white-space: nowrap; cursor: pointer; user-select: none; }}
th:hover {{ background: #4a5568; }}
th .sort-icon {{ margin-left: 4px; font-size: 10px; }}
td {{ padding: 10px 14px; border-bottom: 1px solid #e2e8f0; }}
tr:hover {{ background: #f0fff4; }}
tr:nth-child(even) {{ background: #f7fafc; }}
tr:nth-child(even):hover {{ background: #f0fff4; }}
.region-badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
.region-中心城区 {{ background: #ebf8ff; color: #2b6cb0; }}
.region-主城新区 {{ background: #f0fff4; color: #276749; }}
.region-渝东北 {{ background: #fffaf0; color: #c05621; }}
.region-渝东南 {{ background: #faf5ff; color: #6b46c1; }}
.chart-container {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }}
.chart-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
@media (max-width: 900px) {{ .chart-grid {{ grid-template-columns: 1fr; }} }}
.chart-box {{ position: relative; height: 350px; }}
.tabs {{ display: flex; gap: 0; margin-bottom: 16px; border-bottom: 2px solid #e2e8f0; }}
.tab {{ padding: 10px 24px; cursor: pointer; font-size: 14px; font-weight: 600; color: #718096; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.2s; }}
.tab.active {{ color: #38a169; border-bottom-color: #38a169; }}
.tab:hover {{ color: #276749; }}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; }}
.footer {{ text-align: center; padding: 20px; color: #a0aec0; font-size: 12px; }}
</style>
</head>
<body>

<div class="header">
  <h1>重庆市人口数据查询系统</h1>
  <p>重庆市人口老龄化与医疗压力数据挖掘 · 2016-2024年各区县人口结构数据</p>
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
          <option value="2016">2016</option><option value="2017">2017</option>
          <option value="2018">2018</option><option value="2019">2019</option>
          <option value="2020">2020</option><option value="2021">2021</option>
          <option value="2022">2022</option><option value="2023">2023</option>
          <option value="2024">2024</option>
        </select>
      </div>
      <div class="query-item">
        <label>结束年份</label>
        <select id="yearTo">
          <option value="2016">2016</option><option value="2017">2017</option>
          <option value="2018">2018</option><option value="2019">2019</option>
          <option value="2020">2020</option><option value="2021">2021</option>
          <option value="2022">2022</option><option value="2023">2023</option>
          <option value="2024" selected>2024</option>
        </select>
      </div>
      <div class="query-item">
        <label>最小人口(万)</label>
        <input type="number" id="minPop" placeholder="0" min="0">
      </div>
      <div class="query-item">
        <label>老龄化等级</label>
        <select id="agingLevelFilter">
          <option value="">全部</option>
          <option value="轻度">轻度老龄化(&lt;18%)</option>
          <option value="中度">中度老龄化(18-25%)</option>
          <option value="重度">重度老龄化(25-30%)</option>
          <option value="深度">深度老龄化(&gt;30%)</option>
        </select>
      </div>
      <div class="query-item">
        <label>排序方式</label>
        <select id="sortBy">
          <option value="年份">年份</option>
          <option value="常住人口">常住人口</option>
          <option value="老龄化率">老龄化率</option>
          <option value="65岁及以上人口">老年人口</option>
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
            <th onclick="sortTable('常住人口')">常住人口 <span class="sort-icon">↕</span></th>
            <th onclick="sortTable('户籍人口')">户籍人口 <span class="sort-icon">↕</span></th>
            <th onclick="sortTable('老龄化率')">老龄化率 <span class="sort-icon">↕</span></th>
            <th>老龄化等级</th>
            <th onclick="sortTable('65岁及以上人口')">65岁+人口 <span class="sort-icon">↕</span></th>
            <th>15-64岁人口</th>
            <th>0-14岁人口</th>
          </tr>
        </thead>
        <tbody id="resultBody"></tbody>
      </table>
    </div>
    <div style="margin-top:8px;">
      <span id="recordCount" style="font-size:13px;color:#718096;">共 0 条记录</span>
    </div>
  </div>

  <!-- 图表 -->
  <div id="tab-chart" class="tab-content">
    <div class="chart-grid">
      <div class="chart-container">
        <h3 style="margin-bottom:12px;font-size:15px;color:#2d3748;">老龄化率年度趋势</h3>
        <div class="chart-box"><canvas id="agingTrendChart"></canvas></div>
      </div>
      <div class="chart-container">
        <h3 style="margin-bottom:12px;font-size:15px;color:#2d3748;">各区县2024年老龄化率对比</h3>
        <div class="chart-box"><canvas id="agingDistChart"></canvas></div>
      </div>
      <div class="chart-container">
        <h3 style="margin-bottom:12px;font-size:15px;color:#2d3748;">人口年龄结构堆叠</h3>
        <div class="chart-box"><canvas id="ageStructureChart"></canvas></div>
      </div>
      <div class="chart-container">
        <h3 style="margin-bottom:12px;font-size:15px;color:#2d3748;">各区域老龄化率对比</h3>
        <div class="chart-box"><canvas id="regionAgingChart"></canvas></div>
      </div>
    </div>
  </div>

  <div class="footer">重庆人口老龄化与医疗压力数据挖掘 &copy; 2026</div>
</div>

<script>
const RAW_DATA = {data_json};
const REGION_MAP = {json.dumps(district_region, ensure_ascii=False)};

// 补充计算字段
const DATA = RAW_DATA.map(d => ({{
  ...d,
  区域: REGION_MAP[d["区县"]] || "其他",
  老龄化率: d["65岁及以上人口"] / d["常住人口"],
  抚养比: (d["65岁及以上人口"] + d["0-14岁人口"]) / d["15-64岁人口"],
  老龄化等级: d["65岁及以上人口"] / d["常住人口"] < 0.18 ? "轻度" :
              d["65岁及以上人口"] / d["常住人口"] < 0.25 ? "中度" :
              d["65岁及以上人口"] / d["常住人口"] < 0.30 ? "重度" : "深度"
}}));

const DISTRICTS = [...new Set(DATA.map(d => d["区县"]))].sort();
let currentData = [];
let chartInstances = {{}};
let sortState = {{key: null, dir: 'desc'}};

DISTRICTS.forEach(d => {{
  const opt = document.createElement('option');
  opt.value = d; opt.textContent = d;
  document.getElementById('districtFilter').appendChild(opt);
}});

function doQuery() {{
  const district = document.getElementById('districtFilter').value;
  const region = document.getElementById('regionFilter').value;
  const yFrom = parseInt(document.getElementById('yearFrom').value);
  const yTo = parseInt(document.getElementById('yearTo').value);
  const minPop = (parseInt(document.getElementById('minPop').value) || 0) * 10000;
  const agingLevel = document.getElementById('agingLevelFilter').value;
  const sortKey = document.getElementById('sortBy').value;
  const sortDir = document.getElementById('sortDir').value;

  currentData = DATA.filter(d => {{
    if (district && d["区县"] !== district) return false;
    if (region && d["区域"] !== region) return false;
    if (d["年份"] < yFrom || d["年份"] > yTo) return false;
    if (d["常住人口"] < minPop) return false;
    if (agingLevel && d["老龄化等级"] !== agingLevel) return false;
    return true;
  }});

  if (sortKey === "年份") currentData.sort((a,b) => sortDir==='desc'?b["年份"]-a["年份"]:a["年份"]-b["年份"]);
  else if (sortKey === "老龄化率") currentData.sort((a,b) => sortDir==='desc'?b["老龄化率"]-a["老龄化率"]:a["老龄化率"]-b["老龄化率"]);
  else currentData.sort((a,b) => sortDir==='desc'?b[sortKey]-a[sortKey]:a[sortKey]-b[sortKey]);

  sortState = {{key: sortKey, dir: sortDir}};
  renderTable();
  renderStats();
  renderCharts();
}}

function resetQuery() {{
  document.getElementById('districtFilter').value = '';
  document.getElementById('regionFilter').value = '';
  document.getElementById('yearFrom').value = '2016';
  document.getElementById('yearTo').value = '2024';
  document.getElementById('minPop').value = '';
  document.getElementById('agingLevelFilter').value = '';
  document.getElementById('sortBy').value = '年份';
  document.getElementById('sortDir').value = 'desc';
  doQuery();
}}

function renderTable() {{
  const tbody = document.getElementById('resultBody');
  tbody.innerHTML = currentData.map(d => `
    <tr>
      <td><strong>${{d["区县"]}}</strong></td>
      <td><span class="region-badge region-${{d["区域"]}}">${{d["区域"]}}</span></td>
      <td>${{d["年份"]}}</td>
      <td>${{(d["常住人口"]/10000).toFixed(2)}}万</td>
      <td>${{(d["户籍人口"]/10000).toFixed(2)}}万</td>
      <td style="font-weight:600;">${{(d["老龄化率"]*100).toFixed(2)}}%</td>
      <td><span class="aging-level level-${{d["老龄化等级"]}}">${{d["老龄化等级"]}}老龄化</span></td>
      <td>${{d["65岁及以上人口"].toLocaleString()}}</td>
      <td>${{d["15-64岁人口"].toLocaleString()}}</td>
      <td>${{d["0-14岁人口"].toLocaleString()}}</td>
    </tr>
  `).join('');
  document.getElementById('recordCount').textContent = `共 ${{currentData.length}} 条记录`;
}}

function renderStats() {{
  if (currentData.length === 0) {{ document.getElementById('statsCards').innerHTML = '<div style="color:#718096;padding:20px;">无匹配数据</div>'; return; }}
  const totalPop = currentData.reduce((s,d) => s + d["常住人口"], 0);
  const totalElderly = currentData.reduce((s,d) => s + d["65岁及以上人口"], 0);
  const avgRate = currentData.reduce((s,d) => s + d["老龄化率"], 0) / currentData.length;
  const districts = new Set(currentData.map(d => d["区县"])).size;
  const deepCount = currentData.filter(d => d["老龄化等级"] === "深度").length;
  document.getElementById('statsCards').innerHTML = `
    <div class="stat-card" style="border-left:4px solid #38a169;">
      <div class="label">总常住人口</div>
      <div class="value">${{(totalPop/10000).toFixed(0)}}万</div>
      <div class="sub">覆盖 ${{districts}} 个区县</div>
    </div>
    <div class="stat-card" style="border-left:4px solid #e53e3e;">
      <div class="label">65岁及以上人口</div>
      <div class="value">${{(totalElderly/10000).toFixed(0)}}万</div>
      <div class="sub">占总人口 ${{(totalElderly/totalPop*100).toFixed(1)}}%</div>
    </div>
    <div class="stat-card" style="border-left:4px solid #d69e2e;">
      <div class="label">平均老龄化率</div>
      <div class="value">${{(avgRate*100).toFixed(2)}}%</div>
      <div class="sub">${{currentData.length}} 条记录</div>
    </div>
    <div class="stat-card" style="border-left:4px solid #805ad5;">
      <div class="label">深度老龄化记录</div>
      <div class="value">${{deepCount}}</div>
      <div class="sub">老龄化率 > 30%</div>
    </div>
    <div class="stat-card" style="border-left:4px solid #3182ce;">
      <div class="label">平均抚养比</div>
      <div class="value">${{(currentData.reduce((s,d) => s + d["抚养比"], 0) / currentData.length * 100).toFixed(1)}}%</div>
      <div class="sub">每百名劳动力抚养</div>
    </div>
    <div class="stat-card" style="border-left:4px solid #dd6b20;">
      <div class="label">0-14岁人口</div>
      <div class="value">${{(currentData.reduce((s,d) => s + d["0-14岁人口"], 0)/10000).toFixed(0)}}万</div>
      <div class="sub">少年儿童人口</div>
    </div>
  `;
}}

function sortTable(key) {{
  if (sortState.key === key) {{ sortState.dir = sortState.dir === 'desc' ? 'asc' : 'desc'; }}
  else {{ sortState.key = key; sortState.dir = 'desc'; }}
  document.getElementById('sortBy').value = key;
  document.getElementById('sortDir').value = sortState.dir;
  doQuery();
}}

function renderCharts() {{
  if (currentData.length === 0) return;
  renderAgingTrend();
  renderAgingDist();
  renderAgeStructure();
  renderRegionAging();
}}

function renderAgingTrend() {{
  const ctx = document.getElementById('agingTrendChart').getContext('2d');
  if (chartInstances.agingTrend) chartInstances.agingTrend.destroy();
  const yd = {{}};
  currentData.forEach(d => {{ if(!yd[d["年份"]]) yd[d["年份"]]=[]; yd[d["年份"]].push(d["老龄化率"]); }});
  const labels = Object.keys(yd).sort();
  const vals = labels.map(y => yd[y].reduce((a,b) => a+b, 0)/yd[y].length * 100);
  chartInstances.agingTrend = new Chart(ctx, {{
    type: 'line',
    data: {{ labels: labels.map(y => y+'年'), datasets: [{{ label: '老龄化率', data: vals, borderColor: '#e53e3e', backgroundColor: 'rgba(229,62,62,0.1)', fill: true, tension: 0.3, pointRadius: 5 }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ beginAtZero: false, ticks: {{ callback: v => v.toFixed(1)+'%' }} }} }} }}
  }});
}}

function renderAgingDist() {{
  const ctx = document.getElementById('agingDistChart').getContext('2d');
  if (chartInstances.agingDist) chartInstances.agingDist.destroy();
  // 取最新年份数据
  const yearData = currentData.filter(d => d["年份"] === currentData.reduce((max, r) => Math.max(max, r["年份"]), 0));
  const labels = yearData.map(d => d["区县"]);
  const vals = yearData.map(d => d["老龄化率"] * 100);
  const colors = vals.map(v => v >= 30 ? '#e53e3e' : v >= 25 ? '#d69e2e' : v >= 18 ? '#38a169' : '#3182ce');
  chartInstances.agingDist = new Chart(ctx, {{
    type: 'bar',
    data: {{ labels, datasets: [{{ label: '老龄化率(%)', data: vals, backgroundColor: colors }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ beginAtZero: false }} }} }}
  }});
}}

function renderAgeStructure() {{
  const ctx = document.getElementById('ageStructureChart').getContext('2d');
  if (chartInstances.ageStructure) chartInstances.ageStructure.destroy();
  const yd = {{}};
  currentData.forEach(d => {{ if(!yd[d["年份"]]) yd[d["年份"]]={{elderly:0,working:0,youth:0,total:0}}; yd[d["年份"]].elderly += d["65岁及以上人口"]; yd[d["年份"]].working += d["15-64岁人口"]; yd[d["年份"]].youth += d["0-14岁人口"]; yd[d["年份"]].total += d["常住人口"]; }});
  const labels = Object.keys(yd).sort();
  chartInstances.ageStructure = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: labels.map(y => y+'年'),
      datasets: [
        {{ label: '0-14岁', data: labels.map(y => yd[y].youth/yd[y].total*100), backgroundColor: '#3182ce' }},
        {{ label: '15-64岁', data: labels.map(y => yd[y].working/yd[y].total*100), backgroundColor: '#38a169' }},
        {{ label: '65岁+', data: labels.map(y => yd[y].elderly/yd[y].total*100), backgroundColor: '#e53e3e' }},
      ]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, scales: {{ x: {{ stacked: true }}, y: {{ stacked: true, ticks: {{ callback: v => v.toFixed(1)+'%' }} }} }} }}
  }});
}}

function renderRegionAging() {{
  const ctx = document.getElementById('regionAgingChart').getContext('2d');
  if (chartInstances.regionAging) chartInstances.regionAging.destroy();
  const rd = {{}};
  currentData.forEach(d => {{ if(!rd[d["区域"]]) rd[d["区域"]]=[]; rd[d["区域"]].push(d["老龄化率"]); }});
  const labels = Object.keys(rd);
  const vals = labels.map(l => rd[l].reduce((a,b)=>a+b,0)/rd[l].length*100);
  const colors = {{'中心城区':'rgba(49,130,206,0.7)','主城新区':'rgba(56,161,105,0.7)','渝东北':'rgba(214,158,46,0.7)','渝东南':'rgba(128,90,213,0.7)'}};
  chartInstances.regionAging = new Chart(ctx, {{
    type: 'bar',
    data: {{ labels, datasets: [{{ label: '老龄化率(%)', data: vals, backgroundColor: labels.map(l => colors[l]||'#a0aec0') }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: false, ticks: {{ callback: v => v.toFixed(1)+'%' }} }} }} }}
  }});
}}

function switchTab(name, el) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
  if (name === 'chart') setTimeout(renderCharts, 100);
}}

function exportCSV() {{
  if (currentData.length === 0) {{ alert('没有数据可导出'); return; }}
  const headers = ['区县','区域','年份','常住人口','户籍人口','65岁及以上人口','15-64岁人口','0-14岁人口','老龄化率','老龄化等级'];
  const rows = currentData.map(d => [d["区县"],d["区域"],d["年份"],d["常住人口"],d["户籍人口"],d["65岁及以上人口"],d["15-64岁人口"],d["0-14岁人口"],(d["老龄化率"]*100).toFixed(2)+'%',d["老龄化等级"]]);
  const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\\n');
  const blob = new Blob(['\\ufeff'+csv], {{type:'text/csv;charset=utf-8;'}});
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = '人口数据查询结果.csv';
  link.click();
}}

doQuery();
</script>
</body>
</html>"""

with open("output/人口数据查询系统.html", 'w', encoding='utf-8') as f:
    f.write(html_content)

import os
print(f"HTML: output/人口数据查询系统.html ({os.path.getsize('output/人口数据查询系统.html')} bytes)")
