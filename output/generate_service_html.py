"""生成便民服务数据查询HTML页面"""
import json

with open('output/service_data.json', 'r', encoding='utf-8') as f:
    records = json.load(f)

data_json = json.dumps(records, ensure_ascii=False)

service_types_list = sorted(set(r['类型'] for r in records))
regions_list = ['中心城区', '主城新区', '渝东北', '渝东南']

type_options = ''.join(f'<option value="{t}">{t}</option>' for t in service_types_list)
region_options = ''.join(f'<option value="{r}">{r}</option>' for r in regions_list)

html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>重庆市便民服务数据查询系统</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: #f0f4f8; color: #1a202c; }}
.header {{ background: linear-gradient(135deg, #b83280 0%, #d53f8c 100%); color: white; padding: 24px 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
.header h1 {{ font-size: 24px; font-weight: 600; margin-bottom: 4px; }}
.header p {{ font-size: 14px; opacity: 0.85; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
.query-panel {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }}
.query-panel h2 {{ font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #2d3748; }}
.query-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }}
.query-item {{ display: flex; flex-direction: column; }}
.query-item label {{ font-size: 13px; font-weight: 600; color: #4a5568; margin-bottom: 6px; }}
.query-item select, .query-item input {{ padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px; background: #f7fafc; outline: none; transition: border-color 0.2s; }}
.query-item select:focus, .query-item input:focus {{ border-color: #d53f8c; box-shadow: 0 0 0 3px rgba(213,63,140,0.15); }}
.query-item input {{ width: 100%; }}
.query-actions {{ display: flex; gap: 12px; margin-top: 20px; flex-wrap: wrap; }}
.btn {{ padding: 10px 24px; border: none; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; }}
.btn-primary {{ background: #d53f8c; color: white; }}
.btn-primary:hover {{ background: #b83280; }}
.btn-success {{ background: #3182ce; color: white; }}
.btn-success:hover {{ background: #2c5282; }}
.btn-outline {{ background: white; color: #4a5568; border: 1px solid #e2e8f0; }}
.btn-outline:hover {{ background: #f7fafc; }}
.stats-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px; }}
.stat-card {{ background: white; border-radius: 10px; padding: 16px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
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
tr:hover {{ background: #fff5f7; }}
tr:nth-child(even) {{ background: #f7fafc; }}
tr:nth-child(even):hover {{ background: #fff5f7; }}
.region-badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
.region-中心城区 {{ background: #ebf8ff; color: #2b6cb0; }}
.region-主城新区 {{ background: #f0fff4; color: #276749; }}
.region-渝东北 {{ background: #fffaf0; color: #c05621; }}
.region-渝东南 {{ background: #faf5ff; color: #6b46c1; }}
.status-active {{ color: #38a169; font-weight: 600; }}
.status-other {{ color: #d69e2e; font-weight: 600; }}
.chart-container {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }}
.chart-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
@media (max-width: 900px) {{ .chart-grid {{ grid-template-columns: 1fr; }} }}
.chart-box {{ position: relative; height: 350px; }}
.pagination {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 0; font-size: 13px; color: #718096; }}
.pagination button {{ padding: 6px 16px; background: white; border: 1px solid #e2e8f0; border-radius: 6px; cursor: pointer; font-size: 13px; }}
.pagination button:hover {{ background: #f7fafc; }}
.pagination button:disabled {{ opacity: 0.4; cursor: default; }}
.topnav {{ background: #97266d; color: rgba(255,255,255,0.7); padding: 8px 32px; font-size: 13px; display: flex; align-items: center; gap: 12px; }}
.topnav a {{ color: white; text-decoration: none; display: flex; align-items: center; gap: 4px; font-weight: 600; }}
.topnav a:hover {{ text-decoration: underline; }}
.topnav span {{ color: rgba(255,255,255,0.5); font-size: 12px; }}
</style>
</head>
<body>
<div class="topnav"><a href="../index.html">🏠 返回首页</a><span>便民服务数据查询系统</span></div>
<div class="header">
  <h1>🏪 重庆市便民服务数据查询系统</h1>
  <p>社区服务中心 · 老年活动中心 · 日间照料中心 · 社区食堂 · 便民药店 · 康复理疗等</p>
</div>
<div class="container">
  <div class="query-panel">
    <h2>查询条件</h2>
    <div class="query-grid">
      <div class="query-item">
        <label>区县</label>
        <select id="districtFilter"><option value="">全部区县</option></select>
      </div>
      <div class="query-item">
        <label>区域</label>
        <select id="regionFilter" onchange="updateDistricts()"><option value="">全部区域</option>{region_options}</select>
      </div>
      <div class="query-item">
        <label>服务类型</label>
        <select id="typeFilter"><option value="">全部类型</option>{type_options}</select>
      </div>
      <div class="query-item">
        <label>运营状态</label>
        <select id="statusFilter"><option value="">全部状态</option><option value="正常运营">正常运营</option><option value="升级改造">升级改造</option><option value="暂停服务">暂停服务</option></select>
      </div>
      <div class="query-item">
        <label>最低评分</label>
        <input type="number" id="minScore" min="0" max="5" step="0.1" placeholder="0">
      </div>
      <div class="query-item">
        <label>关键词搜索</label>
        <input type="text" id="keyword" placeholder="搜索名称/服务内容...">
      </div>
    </div>
    <div class="query-actions">
      <button class="btn btn-primary" onclick="query()">查询</button>
      <button class="btn btn-outline" onclick="resetQuery()">重置</button>
      <button class="btn btn-success" onclick="exportCSV()">导出CSV</button>
    </div>
  </div>

  <div class="stats-grid" id="statsGrid"></div>

  <div class="chart-grid">
    <div class="chart-container"><div class="chart-box"><canvas id="typeChart"></canvas></div></div>
    <div class="chart-container"><div class="chart-box"><canvas id="regionChart"></canvas></div></div>
  </div>
  <div class="chart-grid">
    <div class="chart-container"><div class="chart-box"><canvas id="statusChart"></canvas></div></div>
    <div class="chart-container"><div class="chart-box"><canvas id="scoreDistChart"></canvas></div></div>
  </div>

  <div class="table-container">
    <div style="padding:12px 14px;font-size:14px;font-weight:600;color:#2d3748;border-bottom:1px solid #e2e8f0;">
      查询结果 <span id="resultCount" style="font-weight:400;color:#718096;font-size:13px;"></span>
    </div>
    <table>
      <thead><tr>
        <th onclick="sortTable('区县')">区县 <span class="sort-icon">↕</span></th>
        <th onclick="sortTable('区域')">区域 <span class="sort-icon">↕</span></th>
        <th onclick="sortTable('名称')">名称 <span class="sort-icon">↕</span></th>
        <th onclick="sortTable('类型')">类型 <span class="sort-icon">↕</span></th>
        <th>服务内容</th>
        <th onclick="sortTable('评分')">评分 <span class="sort-icon">↕</span></th>
        <th onclick="sortTable('覆盖人数')">覆盖人数 <span class="sort-icon">↕</span></th>
        <th onclick="sortTable('运营状态')">状态 <span class="sort-icon">↕</span></th>
        <th>联系电话</th>
      </tr></thead>
      <tbody id="tableBody"></tbody>
    </table>
    <div class="pagination">
      <span id="pageInfo"></span>
      <div><button id="prevBtn" onclick="prevPage()">上一页</button><button id="nextBtn" onclick="nextPage()" style="margin-left:8px;">下一页</button></div>
    </div>
  </div>
</div>

<script>
const DATA = {data_json};
const DISTRICTS = [...new Set(DATA.map(d => d['区县']))];
DISTRICTS.sort();

let filteredData = [];
let currentPage = 1;
const PAGE_SIZE = 15;
let sortKey = null;
let sortAsc = true;

// 初始化区县下拉
document.getElementById('districtFilter').innerHTML = '<option value="">全部区县</option>' + DISTRICTS.map(d => '<option value="'+d+'">'+d+'</option>').join('');

function updateDistricts() {{
  const region = document.getElementById('regionFilter').value;
  const sel = document.getElementById('districtFilter');
  let opts = ['<option value="">全部区县</option>'];
  let ds = region ? DATA.filter(d => d['区域'] === region).map(d => d['区县']) : DISTRICTS;
  ds = [...new Set(ds)].sort();
  opts.push(...ds.map(d => '<option value="'+d+'">'+d+'</option>'));
  sel.innerHTML = opts.join('');
}}

function query() {{
  const district = document.getElementById('districtFilter').value;
  const region = document.getElementById('regionFilter').value;
  const type = document.getElementById('typeFilter').value;
  const status = document.getElementById('statusFilter').value;
  const minScore = parseFloat(document.getElementById('minScore').value) || 0;
  const keyword = document.getElementById('keyword').value.trim().toLowerCase();

  filteredData = DATA.filter(d => {{
    if (district && d['区县'] !== district) return false;
    if (region && d['区域'] !== region) return false;
    if (type && d['类型'] !== type) return false;
    if (status && d['运营状态'] !== status) return false;
    if (d['评分'] < minScore) return false;
    if (keyword && !d['名称'].toLowerCase().includes(keyword) && !d['服务内容'].toLowerCase().includes(keyword)) return false;
    return true;
  }});

  currentPage = 1;
  render();
}}

function resetQuery() {{
  document.querySelectorAll('.query-panel select, .query-panel input').forEach(el => el.value = '');
  query();
}}

function render() {{
  renderStats();
  renderCharts();
  renderTable();
}}

// ====== 统计 ======
function renderStats() {{
  const total = filteredData.length;
  const types = new Set(filteredData.map(d => d['类型'])).size;
  const active = filteredData.filter(d => d['运营状态'] === '正常运营').length;
  const avgScore = filteredData.length ? (filteredData.reduce((s,d) => s + d['评分'], 0) / filteredData.length) : 0;
  const totalCoverage = filteredData.reduce((s,d) => s + d['覆盖人数'], 0);

  document.getElementById('statsGrid').innerHTML = `
    <div class="stat-card" style="border-left:4px solid #d53f8c;">
      <div class="label">服务点总数</div>
      <div class="value">${{total}}</div>
      <div class="sub">${{types}} 种类型</div>
    </div>
    <div class="stat-card" style="border-left:4px solid #38a169;">
      <div class="label">正常运营</div>
      <div class="value">${{active}}</div>
      <div class="sub">${{total ? (active/total*100).toFixed(1) : 0}}%</div>
    </div>
    <div class="stat-card" style="border-left:4px solid #d69e2e;">
      <div class="label">平均评分</div>
      <div class="value">${{avgScore.toFixed(2)}}</div>
      <div class="sub">满分 5.0</div>
    </div>
    <div class="stat-card" style="border-left:4px solid #3182ce;">
      <div class="label">覆盖总人数</div>
      <div class="value">${{(totalCoverage/10000).toFixed(1)}}万</div>
      <div class="sub">人均 ${{total ? Math.round(totalCoverage/total) : 0}} 人/点</div>
    </div>
  `;
}}

// ====== 图表 ======
let charts = {{}};
function renderCharts() {{
  renderTypeChart(); renderRegionChart(); renderStatusChart(); renderScoreChart();
}}

function renderTypeChart() {{
  const ctx = document.getElementById('typeChart').getContext('2d');
  if (charts.type) charts.type.destroy();
  const grp = {{}}; filteredData.forEach(d => {{ grp[d['类型']] = (grp[d['类型']]||0) + 1; }});
  const labels = Object.keys(grp); const vals = Object.values(grp);
  const colors = ['#d53f8c','#ed64a6','#e53e3e','#dd6b20','#d69e2e','#38a169','#3182ce','#805ad5'];
  charts.type = new Chart(ctx, {{
    type: 'bar', data: {{ labels, datasets: [{{ label: '数量', data: vals, backgroundColor: colors.slice(0,labels.length) }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }}, title: {{ display: true, text: '各类型服务点数量', color: '#2d3748' }} }}, scales: {{ y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }} }} }}
  }});
}}

function renderRegionChart() {{
  const ctx = document.getElementById('regionChart').getContext('2d');
  if (charts.region) charts.region.destroy();
  const grp = {{}}; filteredData.forEach(d => {{ grp[d['区域']] = (grp[d['区域']]||0) + 1; }});
  const labels = ['中心城区','主城新区','渝东北','渝东南'].filter(r => grp[r]);
  const vals = labels.map(r => grp[r]||0);
  charts.region = new Chart(ctx, {{
    type: 'doughnut', data: {{ labels, datasets: [{{ data: vals, backgroundColor: ['#3182ce','#38a169','#d69e2e','#805ad5'] }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ title: {{ display: true, text: '各区域服务点分布', color: '#2d3748' }} }} }}
  }});
}}

function renderStatusChart() {{
  const ctx = document.getElementById('statusChart').getContext('2d');
  if (charts.status) charts.status.destroy();
  const grp = {{}}; filteredData.forEach(d => {{ grp[d['运营状态']] = (grp[d['运营状态']]||0) + 1; }});
  const labels = Object.keys(grp); const vals = Object.values(grp);
  charts.status = new Chart(ctx, {{
    type: 'pie', data: {{ labels, datasets: [{{ data: vals, backgroundColor: ['#38a169','#d69e2e','#e53e3e'] }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ title: {{ display: true, text: '运营状态分布', color: '#2d3748' }} }} }}
  }});
}}

function renderScoreChart() {{
  const ctx = document.getElementById('scoreDistChart').getContext('2d');
  if (charts.score) charts.score.destroy();
  const bins = [0,1,2,3,3.5,4,4.5,5]; const labels = ['0-1','1-2','2-3','3-3.5','3.5-4','4-4.5','4.5-5'];
  const counts = new Array(7).fill(0);
  filteredData.forEach(d => {{ for(let i=0;i<bins.length-1;i++) {{ if(d['评分']>=bins[i] && d['评分']<bins[i+1]) {{ counts[i]++; break; }} }} }});
  charts.score = new Chart(ctx, {{
    type: 'bar', data: {{ labels, datasets: [{{ label: '数量', data: counts, backgroundColor: '#d53f8c' }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }}, title: {{ display: true, text: '评分分布', color: '#2d3748' }} }}, scales: {{ y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }} }} }}
  }});
}}

// ====== 表格 ======
function sortTable(key) {{
  if (sortKey === key) {{ sortAsc = !sortAsc; }} else {{ sortKey = key; sortAsc = true; }}
  filteredData.sort((a,b) => {{ let va = a[key], vb = b[key]; if(typeof va === 'number') return sortAsc ? va-vb : vb-va; return sortAsc ? String(va).localeCompare(String(vb), 'zh') : String(vb).localeCompare(String(va), 'zh'); }});
  renderTable();
}}

function renderTable() {{
  const start = (currentPage-1) * PAGE_SIZE;
  const end = Math.min(start + PAGE_SIZE, filteredData.length);
  const pageData = filteredData.slice(start, end);
  const totalPages = Math.ceil(filteredData.length / PAGE_SIZE) || 1;

  document.getElementById('resultCount').textContent = '（共 ' + filteredData.length + ' 条）';
  document.getElementById('pageInfo').textContent = '第 ' + currentPage + ' / ' + totalPages + ' 页';
  document.getElementById('prevBtn').disabled = currentPage <= 1;
  document.getElementById('nextBtn').disabled = currentPage >= totalPages;

  const tbody = document.getElementById('tableBody');
  tbody.innerHTML = pageData.map(d => `
    <tr>
      <td style="font-weight:600;">${{d['区县']}}</td>
      <td><span class="region-badge region-${{d['区域']}}">${{d['区域']}}</span></td>
      <td>${{d['名称']}}</td>
      <td>${{d['类型']}}</td>
      <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${{d['服务内容']}}">${{d['服务内容']}}</td>
      <td>${{'⭐'.repeat(Math.round(d['评分']))}} ${{d['评分'].toFixed(1)}}</td>
      <td>${{d['覆盖人数'].toLocaleString()}}</td>
      <td class="${{d['运营状态']==='正常运营'?'status-active':'status-other'}}">${{d['运营状态']}}</td>
      <td style="color:#718096;">${{d['联系电话']}}</td>
    </tr>
  `).join('');
}}

function prevPage() {{ if (currentPage > 1) {{ currentPage--; renderTable(); }} }}
function nextPage() {{ if (currentPage * PAGE_SIZE < filteredData.length) {{ currentPage++; renderTable(); }} }}

function exportCSV() {{
  const headers = ['区县','区域','名称','类型','服务内容','评分','覆盖人数','运营状态','联系电话'];
  const rows = filteredData.map(d => headers.map(h => '"'+(d[h]||'')+'"').join(','));
  const csv = '\\uFEFF' + headers.join(',') + '\\n' + rows.join('\\n');
  const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = '便民服务数据.csv'; a.click();
}}

query();
</script>
</body>
</html>"""

with open("output/便民服务数据查询系统.html", 'w', encoding='utf-8') as f:
    f.write(html_content)

import os
print(f"HTML: output/便民服务数据查询系统.html ({os.path.getsize('output/便民服务数据查询系统.html')/1024:.0f}KB)")
