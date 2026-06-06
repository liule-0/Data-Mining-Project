"""生成综合数据分析大屏HTML页面"""
import json

with open('output/combined_data.json', 'r', encoding='utf-8') as f:
    records = json.load(f)

data_json = json.dumps(records, ensure_ascii=False)

district_region = {
    "渝中区":"中心城区","江北区":"中心城区","南岸区":"中心城区","九龙坡区":"中心城区",
    "沙坪坝区":"中心城区","大渡口区":"中心城区","渝北区":"中心城区","巴南区":"中心城区","北碚区":"中心城区",
    "涪陵区":"主城新区","长寿区":"主城新区","江津区":"主城新区","合川区":"主城新区",
    "永川区":"主城新区","南川区":"主城新区","綦江区":"主城新区","大足区":"主城新区",
    "璧山区":"主城新区","铜梁区":"主城新区","潼南区":"主城新区","荣昌区":"主城新区",
    "万州区":"渝东北","开州区":"渝东北","梁平区":"渝东北","城口县":"渝东北",
    "丰都县":"渝东北","垫江县":"渝东北","忠县":"渝东北","云阳县":"渝东北",
    "奉节县":"渝东北","巫山县":"渝东北","巫溪县":"渝东北",
    "黔江区":"渝东南","武隆区":"渝东南","石柱县":"渝东南","秀山县":"渝东南","酉阳县":"渝东南","彭水县":"渝东南",
}

html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>重庆市人口老龄化与医疗压力综合数据大屏</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: #0f172a; color: #e2e8f0; }}
.dashboard {{ max-width: 1600px; margin: 0 auto; padding: 16px; }}
.header {{ display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; background: linear-gradient(135deg, #1e293b, #334155); border-radius: 12px; margin-bottom: 16px; border: 1px solid #475569; }}
.header h1 {{ font-size: 22px; font-weight: 700; background: linear-gradient(90deg, #60a5fa, #34d399); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.header p {{ font-size: 13px; color: #94a3b8; }}
.header .time {{ font-size: 13px; color: #94a3b8; }}
.grid {{ display: grid; gap: 12px; }}
.row {{ display: grid; gap: 12px; margin-bottom: 12px; }}
.col-2 {{ grid-template-columns: 1fr 1fr; }}
.col-3 {{ grid-template-columns: 1fr 1fr 1fr; }}
.col-4 {{ grid-template-columns: 1fr 1fr 1fr 1fr; }}
@media (max-width: 1100px) {{ .col-2, .col-3, .col-4 {{ grid-template-columns: 1fr 1fr; }} }}
@media (max-width: 700px) {{ .col-2, .col-3, .col-4 {{ grid-template-columns: 1fr; }} }}
.card {{ background: #1e293b; border-radius: 10px; padding: 16px; border: 1px solid #334155; }}
.card-title {{ font-size: 13px; color: #94a3b8; margin-bottom: 8px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
.kpi {{ text-align: center; padding: 16px 12px; }}
.kpi .value {{ font-size: 28px; font-weight: 700; }}
.kpi .label {{ font-size: 12px; color: #94a3b8; margin-top: 4px; }}
.kpi .change {{ font-size: 12px; margin-top: 2px; }}
.chart-box {{ position: relative; height: 280px; }}
.chart-box-sm {{ height: 220px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
th {{ padding: 8px 10px; text-align: left; color: #94a3b8; font-weight: 600; border-bottom: 1px solid #334155; }}
td {{ padding: 6px 10px; border-bottom: 1px solid #1a2332; }}
tr:hover {{ background: #334155; }}
.progress-bar {{ height: 6px; border-radius: 3px; background: #334155; overflow: hidden; }}
.progress-fill {{ height: 100%; border-radius: 3px; transition: width 0.5s; }}
.color-up {{ color: #34d399; }}
.color-down {{ color: #f87171; }}
.color-warn {{ color: #fbbf24; }}
.footer {{ text-align: center; padding: 16px; color: #475569; font-size: 12px; }}
.control-bar {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
.control-bar select, .control-bar button {{ padding: 6px 14px; border-radius: 6px; border: 1px solid #475569; background: #1e293b; color: #e2e8f0; font-size: 13px; cursor: pointer; }}
.control-bar select:focus {{ outline: none; border-color: #60a5fa; }}
.control-bar button {{ background: #2563eb; border-color: #2563eb; font-weight: 600; }}
.control-bar button:hover {{ background: #1d4ed8; }}
</style>
</head>
<body>

<div class="dashboard">
  <!-- 顶部标题 -->
  <div class="header">
    <div>
      <h1>重庆市人口老龄化与医疗压力 · 综合数据大屏</h1>
      <p>2016-2024年 · 38个区县 · 人口结构与医疗压力关联分析</p>
    </div>
    <div class="control-bar">
      <select id="yearSelector" onchange="updateDashboard()">
        <option value="0">全部年份</option>
        <option value="2016">2016</option><option value="2017">2017</option>
        <option value="2018">2018</option><option value="2019">2019</option>
        <option value="2020">2020</option><option value="2021">2021</option>
        <option value="2022">2022</option><option value="2023">2023</option>
        <option value="2024" selected>2024</option>
      </select>
      <select id="regionSelector" onchange="updateDashboard()">
        <option value="">全市</option>
        <option value="中心城区">中心城区</option>
        <option value="主城新区">主城新区</option>
        <option value="渝东北">渝东北</option>
        <option value="渝东南">渝东南</option>
      </select>
      <button onclick="updateDashboard()">刷新</button>
    </div>
    <div class="time">
      <span id="currentTime"></span>
    </div>
  </div>

  <!-- KPI 指标行 -->
  <div class="row col-4" id="kpiRow"></div>

  <!-- 图表行1 -->
  <div class="row col-2">
    <div class="card">
      <div class="card-title">老龄化率 vs 老年住院占比 趋势对比</div>
      <div class="chart-box"><canvas id="trendCompareChart"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">老龄化率与住院压力的相关性</div>
      <div class="chart-box"><canvas id="correlationChart"></canvas></div>
    </div>
  </div>

  <!-- 图表行2 -->
  <div class="row col-3">
    <div class="card">
      <div class="card-title">各区县老年人口与住院人次</div>
      <div class="chart-box-sm"><canvas id="elderlyVsAdmissionChart"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">慢性病住院量占比</div>
      <div class="chart-box-sm"><canvas id="diseaseRatioChart"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">各区域综合压力指数</div>
      <div class="chart-box-sm"><canvas id="pressureIndexChart"></canvas></div>
    </div>
  </div>

  <!-- 图表行3 + 表格 -->
  <div class="row col-2">
    <div class="card">
      <div class="card-title">各区域老龄化率年度变化</div>
      <div class="chart-box"><canvas id="regionTrendChart"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">区县排名 TOP 15（综合压力指数）</div>
      <div style="max-height:300px;overflow-y:auto;">
        <table>
          <thead><tr><th>排名</th><th>区县</th><th>区域</th><th>老龄化率</th><th>老年住院占比</th><th>压力指数</th></tr></thead>
          <tbody id="rankingTable"></tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="footer">重庆人口老龄化与医疗压力数据挖掘 &copy; 2026 · 综合数据大屏</div>
</div>

<script>
const RAW_DATA = {data_json};
const REGION_MAP = {json.dumps(district_region, ensure_ascii=False)};

// 计算衍生字段
const DATA = RAW_DATA.map(d => ({{
  ...d,
  区域: REGION_MAP[d["区县"]] || "其他",
  老龄化率: d["65岁及以上人口"] / d["常住人口"],
  老年住院占比: d["老年住院人次"] / d["总住院人次"],
  慢性病住院量: d["心衰_住院量"] + d["高血压_住院量"] + d["糖尿病_住院量"] + d["慢性阻塞性肺疾病_住院量"] + d["脑卒中_住院量"],
  压力指数: (d["老年住院人次"] / d["总住院人次"]) / (d["65岁及以上人口"] / d["常住人口"] || 0.01),
}}));

let charts = {{}};
let filteredData = [];

function updateDashboard() {{
  const year = parseInt(document.getElementById('yearSelector').value);
  const region = document.getElementById('regionSelector').value;
  
  filteredData = DATA.filter(d => {{
    if (year && d["年份"] !== year) return false;
    if (region && d["区域"] !== region) return false;
    return true;
  }});

  if (filteredData.length === 0) filteredData = DATA;
  renderKPIs();
  renderTrendCompare();
  renderCorrelation();
  renderElderlyVsAdmission();
  renderDiseaseRatio();
  renderPressureIndex();
  renderRegionTrend();
  renderRanking();
}}

// ====== KPI ======
function renderKPIs() {{
  const totalPop = filteredData.reduce((s,d) => s + d["常住人口"], 0);
  const totalElderly = filteredData.reduce((s,d) => s + d["65岁及以上人口"], 0);
  const totalAdm = filteredData.reduce((s,d) => s + d["总住院人次"], 0);
  const totalElderlyAdm = filteredData.reduce((s,d) => s + d["老年住院人次"], 0);
  const avgRate = filteredData.reduce((s,d) => s + d["老龄化率"], 0) / filteredData.length;
  const avgElderlyAdmRatio = filteredData.reduce((s,d) => s + d["老年住院占比"], 0) / filteredData.length;
  const districts = new Set(filteredData.map(d => d["区县"])).size;

  document.getElementById('kpiRow').innerHTML = `
    <div class="card kpi" style="border-left:4px solid #60a5fa;">
      <div class="value" style="color:#60a5fa;">${{(totalPop/10000).toFixed(0)}}万</div>
      <div class="label">总常住人口 · ${{districts}}个区县</div>
    </div>
    <div class="card kpi" style="border-left:4px solid #f87171;">
      <div class="value" style="color:#f87171;">${{(totalElderly/10000).toFixed(0)}}万</div>
      <div class="label">65岁+人口 · ${{(totalElderly/totalPop*100).toFixed(1)}}%</div>
    </div>
    <div class="card kpi" style="border-left:4px solid #34d399;">
      <div class="value" style="color:#34d399;">${{(avgRate*100).toFixed(2)}}%</div>
      <div class="label">平均老龄化率</div>
      <div class="change color-warn">${{avgRate >= 0.25 ? '⚠ 重度老龄化' : avgRate >= 0.18 ? '中度老龄化' : '轻度老龄化'}}</div>
    </div>
    <div class="card kpi" style="border-left:4px solid #fbbf24;">
      <div class="value" style="color:#fbbf24;">${{(avgElderlyAdmRatio*100).toFixed(1)}}%</div>
      <div class="label">平均老年住院占比</div>
      <div class="change">总住院 ${{(totalAdm/10000).toFixed(0)}}万 · 老年 ${{(totalElderlyAdm/10000).toFixed(0)}}万</div>
    </div>
  `;
}}

// ====== 趋势对比 ======
function renderTrendCompare() {{
  const ctx = document.getElementById('trendCompareChart').getContext('2d');
  if (charts.trendCompare) charts.trendCompare.destroy();
  const yd = {{}};
  filteredData.forEach(d => {{ if(!yd[d["年份"]]) yd[d["年份"]]={{rate:[],ratio:[]}}; yd[d["年份"]].rate.push(d["老龄化率"]); yd[d["年份"]].ratio.push(d["老年住院占比"]); }});
  const labels = Object.keys(yd).sort();
  const rateData = labels.map(y => yd[y].rate.reduce((a,b)=>a+b,0)/yd[y].rate.length*100);
  const ratioData = labels.map(y => yd[y].ratio.reduce((a,b)=>a+b,0)/yd[y].ratio.length*100);
  charts.trendCompare = new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: labels.map(y => y+'年'),
      datasets: [
        {{ label: '老龄化率(%)', data: rateData, borderColor: '#f87171', backgroundColor: 'rgba(248,113,113,0.1)', fill: true, tension: 0.3, pointRadius: 5, yAxisID: 'y' }},
        {{ label: '老年住院占比(%)', data: ratioData, borderColor: '#60a5fa', backgroundColor: 'rgba(96,165,250,0.1)', fill: true, tension: 0.3, pointRadius: 5, yAxisID: 'y1' }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{ y: {{ beginAtZero: false, position: 'left', ticks: {{ callback: v => v.toFixed(1)+'%', color: '#f87171' }} }}, y1: {{ beginAtZero: false, position: 'right', grid: {{ drawOnChartArea: false }}, ticks: {{ callback: v => v.toFixed(1)+'%', color: '#60a5fa' }} }} }},
      plugins: {{ legend: {{ labels: {{ color: '#94a3b8' }} }} }}
    }}
  }});
}}

// ====== 相关性散点 ======
function renderCorrelation() {{
  const ctx = document.getElementById('correlationChart').getContext('2d');
  if (charts.correlation) charts.correlation.destroy();
  const pts = filteredData.filter(d => d["老龄化率"] > 0 && d["老年住院占比"] > 0);
  const labels = pts.map(d => d["区县"] + ' ' + d["年份"]);
  const x = pts.map(d => d["老龄化率"] * 100);
  const y = pts.map(d => d["老年住院占比"] * 100);
  charts.correlation = new Chart(ctx, {{
    type: 'scatter',
    data: {{
      datasets: [{{
        label: '各区县数据点',
        data: pts.map(d => ({{x: d["老龄化率"]*100, y: d["老年住院占比"]*100}})),
        backgroundColor: pts.map(d => d["区域"] === '中心城区' ? '#60a5fa' : d["区域"] === '主城新区' ? '#34d399' : d["区域"] === '渝东北' ? '#fbbf24' : '#a78bfa'),
        pointRadius: 6,
        pointHoverRadius: 9,
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      scales: {{ x: {{ title: {{ display: true, text: '老龄化率(%)', color: '#94a3b8' }}, ticks: {{ color: '#94a3b8' }} }}, y: {{ title: {{ display: true, text: '老年住院占比(%)', color: '#94a3b8' }}, ticks: {{ color: '#94a3b8' }} }} }},
      plugins: {{ legend: {{ display: false }}, tooltip: {{ callbacks: {{ label: ctx => pts[ctx.dataIndex] ? pts[ctx.dataIndex]["区县"] + ' ' + pts[ctx.dataIndex]["年份"] + ': ' + ctx.parsed.x.toFixed(1) + '% / ' + ctx.parsed.y.toFixed(1) + '%' : '' }} }} }}
    }}
  }});
}}

// ====== 老年人口 vs 住院人次 ======
function renderElderlyVsAdmission() {{
  const ctx = document.getElementById('elderlyVsAdmissionChart').getContext('2d');
  if (charts.elderlyVsAdmission) charts.elderlyVsAdmission.destroy();
  const grouped = {{}};
  filteredData.forEach(d => {{ if(!grouped[d["区县"]]) grouped[d["区县"]]={{elderly:0,adm:0}}; grouped[d["区县"]].elderly += d["65岁及以上人口"]; grouped[d["区县"]].adm += d["老年住院人次"]; }});
  const sorted = Object.entries(grouped).sort((a,b) => b[1].elderly - a[1].elderly).slice(0, 15);
  charts.elderlyVsAdmission = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: sorted.map(s => s[0]),
      datasets: [
        {{ label: '65岁+人口', data: sorted.map(s => s[1].elderly), backgroundColor: 'rgba(248,113,113,0.7)', yAxisID: 'y' }},
        {{ label: '老年住院人次', data: sorted.map(s => s[1].adm), backgroundColor: 'rgba(96,165,250,0.7)', yAxisID: 'y' }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ labels: {{ color: '#94a3b8', boxWidth: 12 }} }} }},
      scales: {{ x: {{ ticks: {{ color: '#94a3b8' }} }}, y: {{ beginAtZero: true, ticks: {{ color: '#94a3b8' }} }} }}
    }}
  }});
}}

// ====== 慢性病占比 ======
function renderDiseaseRatio() {{
  const ctx = document.getElementById('diseaseRatioChart').getContext('2d');
  if (charts.diseaseRatio) charts.diseaseRatio.destroy();
  const diseases = ['心衰_住院量','高血压_住院量','糖尿病_住院量','慢性阻塞性肺疾病_住院量','脑卒中_住院量'];
  const names = ['心衰','高血压','糖尿病','慢阻肺','脑卒中'];
  const totals = diseases.map(k => filteredData.reduce((s,d) => s + d[k], 0));
  const total = totals.reduce((a,b) => a+b, 0);
  const colors = ['#f87171','#fbbf24','#34d399','#60a5fa','#a78bfa'];
  charts.diseaseRatio = new Chart(ctx, {{
    type: 'doughnut',
    data: {{ labels: names, datasets: [{{ data: totals.map(v => (v/total*100).toFixed(1)), backgroundColor: colors }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'right', labels: {{ color: '#94a3b8', boxWidth: 12 }} }}, tooltip: {{ callbacks: {{ label: ctx => names[ctx.dataIndex] + ': ' + totals[ctx.dataIndex].toLocaleString() + ' (' + ctx.parsed + '%)' }} }} }} }}
  }});
}}

// ====== 各区域压力指数 ======
function renderPressureIndex() {{
  const ctx = document.getElementById('pressureIndexChart').getContext('2d');
  if (charts.pressureIndex) charts.pressureIndex.destroy();
  const rd = {{}};
  filteredData.forEach(d => {{ if(!rd[d["区域"]]) rd[d["区域"]]={{rate:0,ratio:0,c:0}}; rd[d["区域"]].rate += d["老龄化率"]; rd[d["区域"]].ratio += d["老年住院占比"]; rd[d["区域"]].c++; }});
  const labels = Object.keys(rd).filter(l => l !== '其他');
  const index = labels.map(l => (rd[l].ratio/rd[l].c) / (rd[l].rate/rd[l].c || 0.01));
  const colors = ['#60a5fa','#34d399','#fbbf24','#a78bfa'];
  charts.pressureIndex = new Chart(ctx, {{
    type: 'radar',
    data: {{
      labels: labels,
      datasets: [{{
        label: '压力指数',
        data: index.map(v => v.toFixed(2)),
        backgroundColor: 'rgba(96,165,250,0.2)',
        borderColor: '#60a5fa',
        pointBackgroundColor: colors,
      }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ r: {{ ticks: {{ color: '#94a3b8', backdropColor: 'transparent' }}, grid: {{ color: '#334155' }}, pointLabels: {{ color: '#e2e8f0' }} }} }} }}
  }});
}}

// ====== 各区域老龄化趋势 ======
function renderRegionTrend() {{
  const ctx = document.getElementById('regionTrendChart').getContext('2d');
  if (charts.regionTrend) charts.regionTrend.destroy();
  const rd = {{}};
  filteredData.forEach(d => {{ if(!rd[d["区域"]]) rd[d["区域"]]={{}}; if(!rd[d["区域"]][d["年份"]]) rd[d["区域"]][d["年份"]]=[]; rd[d["区域"]][d["年份"]].push(d["老龄化率"]); }});
  const regions = ['中心城区','主城新区','渝东北','渝东南'];
  const years = [...new Set(filteredData.map(d => d["年份"]))].sort();
  const colors = ['#60a5fa','#34d399','#fbbf24','#a78bfa'];
  charts.regionTrend = new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: years.map(y => y+'年'),
      datasets: regions.filter(r => rd[r]).map((r, i) => ({{
        label: r,
        data: years.map(y => rd[r] && rd[r][y] ? rd[r][y].reduce((a,b)=>a+b,0)/rd[r][y].length*100 : null),
        borderColor: colors[i],
        tension: 0.3,
        pointRadius: 4,
      }}))
    }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ labels: {{ color: '#94a3b8', boxWidth: 12 }} }} }}, scales: {{ y: {{ beginAtZero: false, ticks: {{ callback: v => v.toFixed(1)+'%', color: '#94a3b8' }} }}, x: {{ ticks: {{ color: '#94a3b8' }} }} }} }}
  }});
}}

// ====== 排名表 ======
function renderRanking() {{
  const year = parseInt(document.getElementById('yearSelector').value) || 2024;
  let data = filteredData.filter(d => d["年份"] === year);
  if (data.length === 0) data = filteredData.filter(d => d["年份"] === Math.max(...filteredData.map(x => x["年份"])));
  data.sort((a,b) => b["压力指数"] - a["压力指数"]);
  const tbody = document.getElementById('rankingTable');
  tbody.innerHTML = data.slice(0, 15).map((d, i) => `
    <tr>
      <td style="color:#94a3b8;">${{i+1}}</td>
      <td style="font-weight:600;">${{d["区县"]}}</td>
      <td><span style="color:#94a3b8;">${{d["区域"]}}</span></td>
      <td style="color:${{d["老龄化率"]>=0.3?'#f87171':d["老龄化率"]>=0.25?'#fbbf24':'#34d399'}};">${{(d["老龄化率"]*100).toFixed(1)}}%</td>
      <td>${{(d["老年住院占比"]*100).toFixed(1)}}%</td>
      <td style="font-weight:700;color:${{d["压力指数"]>=1.2?'#f87171':d["压力指数"]>=1.0?'#fbbf24':'#34d399'}};">${{d["压力指数"].toFixed(2)}}</td>
    </tr>
  `).join('');
}}

// 时钟
function updateClock() {{
  const now = new Date();
  document.getElementById('currentTime').textContent = now.toLocaleString('zh-CN');
}}
setInterval(updateClock, 1000);
updateClock();

updateDashboard();
</script>
</body>
</html>"""

with open("output/综合数据分析大屏.html", 'w', encoding='utf-8') as f:
    f.write(html_content)

import os
print(f"HTML: output/综合数据分析大屏.html ({os.path.getsize('output/综合数据分析大屏.html')} bytes)")
