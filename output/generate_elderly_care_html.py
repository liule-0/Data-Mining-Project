# -*- coding: utf-8 -*-
"""生成养老机构数据查询HTML页面"""
import json

with open('output/elderly_care_data.json', 'r', encoding='utf-8') as f:
    records = json.load(f)

data_json = json.dumps(records, ensure_ascii=False)

inst_types = sorted(set(r['类型'] for r in records))
type_opts = ''.join(f'<option value="{t}">{t}</option>' for t in inst_types)
region_opts = ''.join(f'<option value="{r}">{r}</option>' for r in ['中心城区','主城新区','渝东北','渝东南'])

html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>重庆市养老机构数据查询系统</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: #f0f4f8; color: #1a202c; }}
.header {{ background: linear-gradient(135deg, #c05621 0%, #dd6b20 100%); color: white; padding: 24px 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
.header h1 {{ font-size: 24px; font-weight: 600; margin-bottom: 4px; }}
.header p {{ font-size: 14px; opacity: 0.85; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
.query-panel {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }}
.query-panel h2 {{ font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #2d3748; }}
.query-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }}
.query-item {{ display: flex; flex-direction: column; }}
.query-item label {{ font-size: 13px; font-weight: 600; color: #4a5568; margin-bottom: 6px; }}
.query-item select, .query-item input {{ padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px; background: #f7fafc; outline: none; transition: border-color 0.2s; }}
.query-item select:focus, .query-item input:focus {{ border-color: #dd6b20; box-shadow: 0 0 0 3px rgba(221,107,32,0.15); }}
.query-item input {{ width: 100%; }}
.query-actions {{ display: flex; gap: 12px; margin-top: 20px; flex-wrap: wrap; }}
.btn {{ padding: 10px 24px; border: none; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; }}
.btn-primary {{ background: #dd6b20; color: white; }}
.btn-primary:hover {{ background: #c05621; }}
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
tr:hover {{ background: #fffaf0; }}
tr:nth-child(even) {{ background: #f7fafc; }}
tr:nth-child(even):hover {{ background: #fffaf0; }}
.region-badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
.region-中心城区 {{ background: #ebf8ff; color: #2b6cb0; }}
.region-主城新区 {{ background: #f0fff4; color: #276749; }}
.region-渝东北 {{ background: #fffaf0; color: #c05621; }}
.region-渝东南 {{ background: #faf5ff; color: #6b46c1; }}
.chart-container {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }}
.chart-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
@media (max-width: 900px) {{ .chart-grid {{ grid-template-columns: 1fr; }} }}
.chart-box {{ position: relative; height: 350px; }}
.pagination {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 0; font-size: 13px; color: #718096; }}
.pagination button {{ padding: 6px 16px; background: white; border: 1px solid #e2e8f0; border-radius: 6px; cursor: pointer; font-size: 13px; }}
.pagination button:hover {{ background: #f7fafc; }}
.pagination button:disabled {{ opacity: 0.4; cursor: default; }}
.topnav {{ background: #9b422b; color: rgba(255,255,255,0.7); padding: 8px 32px; font-size: 13px; display: flex; align-items: center; gap: 12px; }}
.topnav a {{ color: white; text-decoration: none; display: flex; align-items: center; gap: 4px; font-weight: 600; }}
.topnav a:hover {{ text-decoration: underline; }}
.topnav span {{ color: rgba(255,255,255,0.5); font-size: 12px; }}
</style>
</head>
<body>
<div class="topnav"><a href="../index.html">🏠 返回首页</a><span>养老机构数据查询系统</span></div>
<div class="header">
  <h1>🏠 重庆市养老机构数据查询系统</h1>
  <p>公办养老院 · 民办养老院 · 敬老院 · 老年公寓 · 护理院 · 床位数 · 入住率 · 收费标准</p>
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
        <select id="regionFilter" onchange="updateDistricts()"><option value="">全部区域</option>{region_opts}</select>
      </div>
      <div class="query-item">
        <label>机构类型</label>
        <select id="typeFilter"><option value="">全部类型</option>{type_opts}</select>
      </div>
      <div class="query-item">
        <label>医养结合</label>
        <select id="medicalFilter"><option value="">全部</option><option value="是">是</option><option value="否">否</option></select>
      </div>
      <div class="query-item">
        <label>最低评分</label>
        <input type="number" id="minScore" min="0" max="5" step="0.1" placeholder="0">
      </div>
      <div class="query-item">
        <label>最高月费(元)</label>
        <input type="number" id="maxFee" min="0" placeholder="不限">
      </div>
      <div class="query-item">
        <label>最低床位数</label>
        <input type="number" id="minBeds" min="0" placeholder="不限">
      </div>
      <div class="query-item">
        <label>关键词搜索</label>
        <input type="text" id="keyword" placeholder="搜索名称...">
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
    <div class="chart-container"><div class="chart-box"><canvas id="occChart"></canvas></div></div>
    <div class="chart-container"><div class="chart-box"><canvas id="feeChart"></canvas></div></div>
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
        <th onclick="sortTable('床位数')">床位数 <span class="sort-icon">↕</span></th>
        <th onclick="sortTable('入住率')">入住率 <span class="sort-icon">↕</span></th>
        <th onclick="sortTable('收费标准_元月')">月费(元) <span class="sort-icon">↕</span></th>
        <th onclick="sortTable('评分')">评分 <span class="sort-icon">↕</span></th>
        <th>医养结合</th>
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
const DISTRICTS = [...new Set(DATA.map(d => d['区县']))].sort();

let filteredData = [];
let currentPage = 1;
const PAGE_SIZE = 15;
let sortKey = null;
let sortAsc = true;

document.getElementById('districtFilter').innerHTML = '<option value="">全部区县</option>' + DISTRICTS.map(d => '<option value="'+d+'">'+d+'</option>').join('');

function updateDistricts() {{
  const region = document.getElementById('regionFilter').value;
  const sel = document.getElementById('districtFilter');
  let ds = region ? [...new Set(DATA.filter(d => d['区域'] === region).map(d => d['区县']))].sort() : DISTRICTS;
  sel.innerHTML = '<option value="">全部区县</option>' + ds.map(d => '<option value="'+d+'">'+d+'</option>').join('');
}}

function query() {{
  const district = document.getElementById('districtFilter').value;
  const region = document.getElementById('regionFilter').value;
  const type = document.getElementById('typeFilter').value;
  const medical = document.getElementById('medicalFilter').value;
  const minScore = parseFloat(document.getElementById('minScore').value) || 0;
  const maxFee = parseFloat(document.getElementById('maxFee').value) || Infinity;
  const minBeds = parseInt(document.getElementById('minBeds').value) || 0;
  const keyword = document.getElementById('keyword').value.trim().toLowerCase();

  filteredData = DATA.filter(d => {{
    if (district && d['区县'] !== district) return false;
    if (region && d['区域'] !== region) return false;
    if (type && d['类型'] !== type) return false;
    if (medical && d['医养结合'] !== medical) return false;
    if (d['评分'] < minScore) return false;
    if (d['收费标准_元月'] > maxFee) return false;
    if (d['床位数'] < minBeds) return false;
    if (keyword && !d['名称'].toLowerCase().includes(keyword)) return false;
    return true;
  }});

  currentPage = 1;
  render();
}}

function resetQuery() {{
  document.querySelectorAll('.query-panel select, .query-panel input').forEach(el => el.value = '');
  query();
}}

function render() {{ renderStats(); renderCharts(); renderTable(); }}

function renderStats() {{
  const n = filteredData.length;
  const totalBeds = filteredData.reduce((s,d) => s + d['床位数'], 0);
  const totalResidents = filteredData.reduce((s,d) => s + d['入住人数'], 0);
  const avgOcc = filteredData.length ? (totalResidents/totalBeds*100) : 0;
  const avgFee = filteredData.length ? Math.round(filteredData.reduce((s,d) => s + d['收费标准_元月'], 0) / filteredData.length) : 0;
  const medicalCount = filteredData.filter(d => d['医养结合'] === '是').length;
  document.getElementById('statsGrid').innerHTML = `
    <div class="stat-card" style="border-left:4px solid #dd6b20;"><div class="label">机构总数</div><div class="value">${{n}}</div><div class="sub">${{new Set(filteredData.map(d => d['类型'])).size}} 种类型</div></div>
    <div class="stat-card" style="border-left:4px solid #3182ce;"><div class="label">总床位数</div><div class="value">${{totalBeds.toLocaleString()}}</div><div class="sub">已入住 ${{totalResidents.toLocaleString()}} 人</div></div>
    <div class="stat-card" style="border-left:4px solid #38a169;"><div class="label">平均入住率</div><div class="value">${{avgOcc.toFixed(1)}}%</div><div class="sub">${{medicalCount}} 家医养结合</div></div>
    <div class="stat-card" style="border-left:4px solid #d69e2e;"><div class="label">平均月费</div><div class="value">${{avgFee.toLocaleString()}}元</div><div class="sub">${{n ? Math.round(filteredData.reduce((s,d) => Math.min(s, d['收费标准_元月']), Infinity)) : 0}} - ${{n ? Math.round(filteredData.reduce((s,d) => Math.max(s, d['收费标准_元月']), 0)) : 0}} 元</div></div>
  `;
}}

let charts = {{}};
function renderCharts() {{
  // 类型分布
  const ctx1 = document.getElementById('typeChart').getContext('2d');
  if (charts.type) charts.type.destroy();
  const grp1 = {{}}; filteredData.forEach(d => {{ grp1[d['类型']] = (grp1[d['类型']]||0) + 1; }});
  charts.type = new Chart(ctx1, {{ type: 'bar', data: {{ labels: Object.keys(grp1), datasets: [{{ data: Object.values(grp1), backgroundColor: ['#dd6b20','#ed8936','#f6ad55','#fbd38d','#feebc8'] }}] }}, options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }}, title: {{ display: true, text: '各类型机构数量', color: '#2d3748' }} }}, scales: {{ y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }} }} }} }});

  // 区域分布
  const ctx2 = document.getElementById('regionChart').getContext('2d');
  if (charts.region) charts.region.destroy();
  const grp2 = {{}}; filteredData.forEach(d => {{ grp2[d['区域']] = (grp2[d['区域']]||0) + 1; }});
  const labels2 = ['中心城区','主城新区','渝东北','渝东南'].filter(r => grp2[r]);
  charts.region = new Chart(ctx2, {{ type: 'doughnut', data: {{ labels: labels2, datasets: [{{ data: labels2.map(r => grp2[r]), backgroundColor: ['#3182ce','#38a169','#d69e2e','#805ad5'] }}] }}, options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ title: {{ display: true, text: '各区域机构分布', color: '#2d3748' }} }} }} }});

  // 入住率分布
  const ctx3 = document.getElementById('occChart').getContext('2d');
  if (charts.occ) charts.occ.destroy();
  const bins = [0,60,70,80,90,100]; const lbls = ['<60%','60-70%','70-80%','80-90%','90-100%'];
  const cnts = new Array(5).fill(0);
  filteredData.forEach(d => {{ const r = d['入住率']; for(let i=0;i<5;i++) {{ if(r>=bins[i] && r<bins[i+1]) {{ cnts[i]++; break; }} }} }});
  charts.occ = new Chart(ctx3, {{ type: 'bar', data: {{ labels: lbls, datasets: [{{ data: cnts, backgroundColor: '#dd6b20' }}] }}, options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }}, title: {{ display: true, text: '入住率分布', color: '#2d3748' }} }}, scales: {{ y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }} }} }} }});

  // 月费分布
  const ctx4 = document.getElementById('feeChart').getContext('2d');
  if (charts.fee) charts.fee.destroy();
  const fbins = [0,1500,3000,5000,8000,15000]; const flbls = ['<1500','1500-3000','3000-5000','5000-8000','8000+'];
  const fcnts = new Array(5).fill(0);
  filteredData.forEach(d => {{ const f = d['收费标准_元月']; for(let i=0;i<5;i++) {{ if(f>=fbins[i] && f<fbins[i+1]) {{ fcnts[i]++; break; }} }} }});
  charts.fee = new Chart(ctx4, {{ type: 'bar', data: {{ labels: flbls, datasets: [{{ data: fcnts, backgroundColor: '#ed8936' }}] }}, options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }}, title: {{ display: true, text: '月费分布(元)', color: '#2d3748' }} }}, scales: {{ y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }} }} }} }});
}}

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

  document.getElementById('tableBody').innerHTML = pageData.map(d => {
    const occColor = d['入住率'] >= 90 ? '#e53e3e' : d['入住率'] >= 75 ? '#d69e2e' : '#38a169';
    return '<tr><td style="font-weight:600;">' + d['区县'] + '</td><td><span class="region-badge region-' + d['区域'] + '">' + d['区域'] + '</span></td><td>' + d['名称'] + '</td><td>' + d['类型'] + '</td><td>' + d['床位数'].toLocaleString() + '</td><td style="color:' + occColor + ';font-weight:600;">' + d['入住率'].toFixed(1) + '%</td><td>' + d['收费标准_元月'].toLocaleString() + '</td><td>' + '⭐'.repeat(Math.round(d['评分'])) + ' ' + d['评分'].toFixed(1) + '</td><td>' + (d['医养结合'] === '是' ? '<span style="color:#38a169;font-weight:600;">✓ 是</span>' : '<span style="color:#a0aec0;">否</span>') + '</td><td style="color:#718096;">' + d['联系电话'] + '</td></tr>';
  }).join('');
}}

function prevPage() {{ if (currentPage > 1) {{ currentPage--; renderTable(); }} }}
function nextPage() {{ if (currentPage * PAGE_SIZE < filteredData.length) {{ currentPage++; renderTable(); }} }}

function exportCSV() {{
  const headers = ['区县','区域','名称','类型','床位数','入住人数','入住率(%)','收费标准_元月','评分','员工数','医养结合','联系电话'];
  const rows = filteredData.map(d => headers.map(h => '"'+(d[h]||'')+'"').join(','));
  const csv = '\\uFEFF' + headers.join(',') + '\\n' + rows.join('\\n');
  const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = '养老机构数据.csv'; a.click();
}}

query();
</script>
</body>
</html>"""

with open("output/养老机构数据查询系统.html", 'w', encoding='utf-8') as f:
    f.write(html_content)

import os
print(f"HTML: output/养老机构数据查询系统.html ({os.path.getsize('output/养老机构数据查询系统.html')/1024:.0f}KB)")
