"""生成舆情数据查询HTML页面"""
import json

# 读取数据
with open('output/sentiment_data.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

# 清洗数据：修复列名BOM问题、转换类型
records = []
for r in raw:
    rec = {}
    for k, v in r.items():
        key = k.replace('\ufeff', '').strip()
        rec[key] = v
    # 类型转换
    rec['id'] = int(rec['id'])
    rec['sentiment_score'] = float(rec['sentiment_score'])
    rec['likes'] = int(rec['likes'])
    records.append(rec)

data_json = json.dumps(records, ensure_ascii=False)

# 获取各情感标签和平台的唯一值用于构建筛选
sentiment_labels = sorted(set(r['sentiment_label'] for r in records))
platforms = sorted(set(r['platform'] for r in records))

# 获取时间范围
dates = sorted(set(r['time'] for r in records))
min_date = dates[0]
max_date = dates[-1]

html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>重庆市老龄化舆情数据查询系统</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: #f0f4f8; color: #1a202c; }}
.header {{ background: linear-gradient(135deg, #553c9a 0%, #805ad5 100%); color: white; padding: 24px 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
.header h1 {{ font-size: 24px; font-weight: 600; margin-bottom: 4px; }}
.header p {{ font-size: 14px; opacity: 0.85; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
.query-panel {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }}
.query-panel h2 {{ font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #2d3748; }}
.query-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }}
.query-item {{ display: flex; flex-direction: column; }}
.query-item label {{ font-size: 13px; font-weight: 600; color: #4a5568; margin-bottom: 6px; }}
.query-item select, .query-item input {{ padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px; background: #f7fafc; outline: none; transition: border-color 0.2s; }}
.query-item select:focus, .query-item input:focus {{ border-color: #805ad5; box-shadow: 0 0 0 3px rgba(128,90,213,0.15); }}
.query-item input {{ width: 100%; }}
.query-actions {{ display: flex; gap: 12px; margin-top: 20px; flex-wrap: wrap; }}
.btn {{ padding: 10px 24px; border: none; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; }}
.btn-primary {{ background: #805ad5; color: white; }}
.btn-primary:hover {{ background: #6b46c1; }}
.btn-success {{ background: #38a169; color: white; }}
.btn-success:hover {{ background: #276749; }}
.btn-danger {{ background: #e53e3e; color: white; }}
.btn-danger:hover {{ background: #c53030; }}
.btn-outline {{ background: white; color: #4a5568; border: 1px solid #e2e8f0; }}
.btn-outline:hover {{ background: #f7fafc; }}
.stats-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }}
.stat-card {{ background: white; border-radius: 10px; padding: 16px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
.stat-card .label {{ font-size: 12px; color: #718096; margin-bottom: 4px; }}
.stat-card .value {{ font-size: 22px; font-weight: 700; color: #2d3748; }}
.stat-card .sub {{ font-size: 12px; color: #a0aec0; margin-top: 2px; }}
.table-container {{ overflow-x: auto; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); max-height: 650px; overflow-y: auto; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
thead {{ background: #2d3748; color: white; position: sticky; top: 0; z-index: 10; }}
th {{ padding: 12px 14px; text-align: left; font-weight: 600; white-space: nowrap; cursor: pointer; user-select: none; }}
th:hover {{ background: #4a5568; }}
th .sort-icon {{ margin-left: 4px; font-size: 10px; }}
td {{ padding: 10px 14px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }}
tr:hover {{ background: #faf5ff; }}
tr:nth-child(even) {{ background: #f7fafc; }}
tr:nth-child(even):hover {{ background: #faf5ff; }}
.sentiment-badge {{ display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
.sentiment-正面 {{ background: #c6f6d5; color: #22543d; }}
.sentiment-中性 {{ background: #fefcbf; color: #744210; }}
.sentiment-负面 {{ background: #fed7d7; color: #822727; }}
.platform-badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
.platform-douyin {{ background: #1a1a2e; color: white; }}
.platform-kuaishou {{ background: #ff6b35; color: white; }}
.content-cell {{ max-width: 380px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; }}
.content-cell:hover {{ white-space: normal; overflow: visible; position: relative; background: #fffff0; }}
.chart-container {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }}
.chart-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }}
@media (max-width: 1100px) {{ .chart-grid {{ grid-template-columns: 1fr 1fr; }} }}
@media (max-width: 700px) {{ .chart-grid {{ grid-template-columns: 1fr; }} }}
.chart-box {{ position: relative; height: 300px; }}
.tabs {{ display: flex; gap: 0; margin-bottom: 16px; border-bottom: 2px solid #e2e8f0; }}
.tab {{ padding: 10px 24px; cursor: pointer; font-size: 14px; font-weight: 600; color: #718096; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.2s; }}
.tab.active {{ color: #805ad5; border-bottom-color: #805ad5; }}
.tab:hover {{ color: #6b46c1; }}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; }}
.tag-cloud {{ display: flex; flex-wrap: wrap; gap: 8px; padding: 16px; justify-content: center; }}
.tag-item {{ display: inline-block; padding: 6px 14px; border-radius: 16px; background: #ebf8ff; color: #2b6cb0; font-size: 13px; cursor: pointer; transition: all 0.2s; }}
.tag-item:hover {{ transform: scale(1.05); background: #bee3f8; }}
.footer {{ text-align: center; padding: 20px; color: #a0aec0; font-size: 12px; }}
#searchKeyword {{ width: 100%; }}
</style>
</head>
<body>

<div class="header">
  <h1>重庆市老龄化舆情数据查询系统</h1>
  <p>抖音 / 快手平台老龄化相关评论数据 · 情感分析 · 趋势洞察</p>
</div>

<div class="container">
  <!-- 查询面板 -->
  <div class="query-panel">
    <h2>查询条件</h2>
    <div class="query-grid">
      <div class="query-item" style="grid-column: span 2;">
        <label>关键词搜索</label>
        <input type="text" id="searchKeyword" placeholder="请输入关键词搜索评论内容..." />
      </div>
      <div class="query-item">
        <label>平台</label>
        <select id="platformFilter">
          <option value="">全部平台</option>
          <option value="douyin">抖音</option>
          <option value="kuaishou">快手</option>
        </select>
      </div>
      <div class="query-item">
        <label>情感标签</label>
        <select id="sentimentFilter">
          <option value="">全部情感</option>
          <option value="正面">正面</option>
          <option value="中性">中性</option>
          <option value="负面">负面</option>
        </select>
      </div>
      <div class="query-item">
        <label>起始日期</label>
        <input type="date" id="dateFrom" value="{min_date}">
      </div>
      <div class="query-item">
        <label>截止日期</label>
        <input type="date" id="dateTo" value="{max_date}">
      </div>
      <div class="query-item">
        <label>最低点赞数</label>
        <input type="number" id="minLikes" placeholder="0" min="0">
      </div>
      <div class="query-item">
        <label>排序方式</label>
        <select id="sortBy">
          <option value="time">时间</option>
          <option value="likes">点赞数</option>
          <option value="sentiment_score">情感分数</option>
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
    <div class="tab" onclick="switchTab('chart', this)">分析图表</div>
    <div class="tab" onclick="switchTab('wordcloud', this)">热门词云</div>
  </div>

  <!-- 数据表格 -->
  <div id="tab-table" class="tab-content active">
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th style="width:50px">ID</th>
            <th style="width:70px" onclick="sortTable('platform')">平台 <span class="sort-icon">↕</span></th>
            <th onclick="sortTable('content')">评论内容 <span class="sort-icon">↕</span></th>
            <th style="width:80px" onclick="sortTable('sentiment_label')">情感 <span class="sort-icon">↕</span></th>
            <th style="width:90px" onclick="sortTable('sentiment_score')">情感分数 <span class="sort-icon">↕</span></th>
            <th style="width:70px" onclick="sortTable('likes')">点赞 <span class="sort-icon">↕</span></th>
            <th style="width:110px" onclick="sortTable('time')">时间 <span class="sort-icon">↕</span></th>
          </tr>
        </thead>
        <tbody id="resultBody"></tbody>
      </table>
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;">
      <span id="recordCount" style="font-size:13px;color:#718096;">共 0 条记录</span>
      <div>
        <label style="font-size:12px;color:#718096;">每页: </label>
        <select id="pageSize" onchange="doQuery()" style="padding:4px 8px;border:1px solid #e2e8f0;border-radius:4px;font-size:12px;">
          <option value="20">20</option>
          <option value="50" selected>50</option>
          <option value="100">100</option>
          <option value="0">全部</option>
        </select>
        <span id="pageInfo" style="font-size:12px;color:#718096;margin-left:12px;"></span>
        <button class="btn btn-outline" style="padding:4px 12px;font-size:12px;" onclick="prevPage()">上一页</button>
        <button class="btn btn-outline" style="padding:4px 12px;font-size:12px;" onclick="nextPage()">下一页</button>
      </div>
    </div>
  </div>

  <!-- 分析图表 -->
  <div id="tab-chart" class="tab-content">
    <div class="chart-grid">
      <div class="chart-container">
        <h3 style="margin-bottom:12px;font-size:15px;color:#2d3748;">情感分布</h3>
        <div class="chart-box"><canvas id="sentimentPieChart"></canvas></div>
      </div>
      <div class="chart-container">
        <h3 style="margin-bottom:12px;font-size:15px;color:#2d3748;">平台对比</h3>
        <div class="chart-box"><canvas id="platformChart"></canvas></div>
      </div>
      <div class="chart-container">
        <h3 style="margin-bottom:12px;font-size:15px;color:#2d3748;">情感分数分布</h3>
        <div class="chart-box"><canvas id="scoreDistChart"></canvas></div>
      </div>
      <div class="chart-container">
        <h3 style="margin-bottom:12px;font-size:15px;color:#2d3748;">月度评论趋势</h3>
        <div class="chart-box"><canvas id="monthlyTrendChart"></canvas></div>
      </div>
      <div class="chart-container">
        <h3 style="margin-bottom:12px;font-size:15px;color:#2d3748;">点赞数分布</h3>
        <div class="chart-box"><canvas id="likesDistChart"></canvas></div>
      </div>
      <div class="chart-container">
        <h3 style="margin-bottom:12px;font-size:15px;color:#2d3748;">各平台情感分布</h3>
        <div class="chart-box"><canvas id="platformSentimentChart"></canvas></div>
      </div>
    </div>
  </div>

  <!-- 热门词云 -->
  <div id="tab-wordcloud" class="tab-content">
    <div class="query-panel">
      <p style="color:#718096;font-size:13px;margin-bottom:12px;">以下为当前查询结果中出现频率最高的关键词，点击关键词可快速搜索</p>
      <div class="tag-cloud" id="tagCloud"></div>
    </div>
  </div>

  <div class="footer">
    重庆人口老龄化与医疗压力数据挖掘 &copy; 2026
  </div>
</div>

<script>
// ========== 数据 ==========
const RAW_DATA = {data_json};

// 修正数据格式
const DATA = RAW_DATA.map(d => ({{
  ...d,
  time_str: d.time,
  sentiment_score: parseFloat(d.sentiment_score),
  likes: parseInt(d.likes),
  id: parseInt(d.id),
}}));

// 停用词列表
const STOP_WORDS = new Set([
  '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
  '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
  '没有', '看', '好', '自己', '这', '他', '她', '它', '们', '那', '些',
  '什么', '怎么', '因为', '所以', '但是', '可以', '这个', '那个', '还',
  '被', '把', '让', '对', '从', '与', '而', '或', '如果', '虽然', '比较',
  '更', '最', '太', '非常', '真的', '确实', '实在', '简直', '特别',
  '有点', '有些', '感觉', '希望', '建议', '不是', '还是', '就是',
  '已经', '可以', '过来', '没有', '不会', '可能', '应该', '需要',
  '之后', '之前', '以后', '时候', '问题', '情况', '方式', '地方',
  '一样', '一些', '一起', '一直', '一点', '很多', '不少', '对于',
  '关于', '通过', '作为', '进行', '以及', '及其', '等等',
]);

let currentData = [];
let filteredData = [];
let chartInstances = {{}};
let sortState = {{key: 'time', dir: 'desc'}};
let currentPage = 0;

// ========== 查询 ==========
function doQuery() {{
  const keyword = document.getElementById('searchKeyword').value.trim().toLowerCase();
  const platform = document.getElementById('platformFilter').value;
  const sentiment = document.getElementById('sentimentFilter').value;
  const dateFrom = document.getElementById('dateFrom').value;
  const dateTo = document.getElementById('dateTo').value;
  const minLikes = parseInt(document.getElementById('minLikes').value) || 0;
  const sortKey = document.getElementById('sortBy').value;
  const sortDir = document.getElementById('sortDir').value;

  filteredData = DATA.filter(d => {{
    if (platform && d.platform !== platform) return false;
    if (sentiment && d.sentiment_label !== sentiment) return false;
    if (d.time < dateFrom || d.time > dateTo) return false;
    if (d.likes < minLikes) return false;
    if (keyword && !d.content.toLowerCase().includes(keyword)) return false;
    return true;
  }});

  // 排序
  if (sortKey === 'time') {{
    filteredData.sort((a, b) => sortDir === 'desc' ? b.time.localeCompare(a.time) : a.time.localeCompare(b.time));
  }} else if (sortKey === 'likes') {{
    filteredData.sort((a, b) => sortDir === 'desc' ? b.likes - a.likes : a.likes - b.likes);
  }} else {{
    filteredData.sort((a, b) => sortDir === 'desc' ? b.sentiment_score - a.sentiment_score : a.sentiment_score - b.sentiment_score);
  }}

  sortState = {{key: sortKey, dir: sortDir}};
  currentPage = 0;
  renderTable();
  renderStats();
  renderCharts();
  renderTagCloud();
}}

function resetQuery() {{
  document.getElementById('searchKeyword').value = '';
  document.getElementById('platformFilter').value = '';
  document.getElementById('sentimentFilter').value = '';
  document.getElementById('dateFrom').value = '{min_date}';
  document.getElementById('dateTo').value = '{max_date}';
  document.getElementById('minLikes').value = '';
  document.getElementById('sortBy').value = 'time';
  document.getElementById('sortDir').value = 'desc';
  doQuery();
}}

// ========== 表格渲染(分页) ==========
function renderTable() {{
  const pageSize = parseInt(document.getElementById('pageSize').value) || filteredData.length;
  const totalPages = pageSize > 0 ? Math.ceil(filteredData.length / pageSize) : 1;
  if (currentPage >= totalPages) currentPage = totalPages - 1;
  if (currentPage < 0) currentPage = 0;
  const start = pageSize > 0 ? currentPage * pageSize : 0;
  const end = pageSize > 0 ? start + pageSize : filteredData.length;
  const pageData = filteredData.slice(start, end);

  const tbody = document.getElementById('resultBody');
  tbody.innerHTML = pageData.map(d => `
    <tr>
      <td style="color:#a0aec0;">${{d.id}}</td>
      <td><span class="platform-badge platform-${{d.platform}}">${{d.platform === 'douyin' ? '抖音' : '快手'}}</span></td>
      <td class="content-cell" title="${{d.content.replace(/"/g, '&quot;')}}">${{d.content}}</td>
      <td><span class="sentiment-badge sentiment-${{d.sentiment_label}}">${{d.sentiment_label}}</span></td>
      <td>${{d.sentiment_score.toFixed(4)}}</td>
      <td style="font-weight:600;">${{d.likes}}</td>
      <td style="color:#718096;">${{d.time}}</td>
    </tr>
  `).join('');

  document.getElementById('recordCount').textContent = `共 ${{filteredData.length}} 条记录`;
  document.getElementById('pageInfo').textContent = `第 ${{currentPage + 1}} / ${{totalPages}} 页`;
}}

function prevPage() {{ if (currentPage > 0) {{ currentPage--; renderTable(); }} }}
function nextPage() {{ const ps = parseInt(document.getElementById('pageSize').value) || filteredData.length; const tp = Math.ceil(filteredData.length / ps); if (currentPage < tp - 1) {{ currentPage++; renderTable(); }} }}

// ========== 统计卡片 ==========
function renderStats() {{
  if (filteredData.length === 0) {{ document.getElementById('statsCards').innerHTML = '<div style="color:#718096;padding:20px;">无匹配数据</div>'; return; }}
  const total = filteredData.length;
  const pos = filteredData.filter(d => d.sentiment_label === '正面').length;
  const neu = filteredData.filter(d => d.sentiment_label === '中性').length;
  const neg = filteredData.filter(d => d.sentiment_label === '负面').length;
  const avgScore = filteredData.reduce((s, d) => s + d.sentiment_score, 0) / total;
  const totalLikes = filteredData.reduce((s, d) => s + d.likes, 0);
  const avgLikes = (totalLikes / total).toFixed(1);
  const douyinCount = filteredData.filter(d => d.platform === 'douyin').length;
  const kuaishouCount = filteredData.filter(d => d.platform === 'kuaishou').length;
  document.getElementById('statsCards').innerHTML = `
    <div class="stat-card" style="border-left:4px solid #805ad5;">
      <div class="label">总评论数</div>
      <div class="value">${{total.toLocaleString()}}</div>
      <div class="sub">抖音 ${{douyinCount}} / 快手 ${{kuaishouCount}}</div>
    </div>
    <div class="stat-card" style="border-left:4px solid #38a169;">
      <div class="label">正面评价</div>
      <div class="value">${{pos.toLocaleString()}}</div>
      <div class="sub">占 ${{(pos/total*100).toFixed(1)}}%</div>
    </div>
    <div class="stat-card" style="border-left:4px solid #d69e2e;">
      <div class="label">中性评价</div>
      <div class="value">${{neu.toLocaleString()}}</div>
      <div class="sub">占 ${{(neu/total*100).toFixed(1)}}%</div>
    </div>
    <div class="stat-card" style="border-left:4px solid #e53e3e;">
      <div class="label">负面评价</div>
      <div class="value">${{neg.toLocaleString()}}</div>
      <div class="sub">占 ${{(neg/total*100).toFixed(1)}}%</div>
    </div>
    <div class="stat-card" style="border-left:4px solid #3182ce;">
      <div class="label">平均情感分数</div>
      <div class="value">${{avgScore.toFixed(3)}}</div>
      <div class="sub">0~1 越高越正面</div>
    </div>
    <div class="stat-card" style="border-left:4px solid #dd6b20;">
      <div class="label">平均点赞数</div>
      <div class="value">${{avgLikes}}</div>
      <div class="sub">总点赞 ${{totalLikes.toLocaleString()}}</div>
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
  if (filteredData.length === 0) return;
  renderSentimentPie();
  renderPlatformChart();
  renderScoreDist();
  renderMonthlyTrend();
  renderLikesDist();
  renderPlatformSentiment();
}}

function renderSentimentPie() {{
  const ctx = document.getElementById('sentimentPieChart').getContext('2d');
  if (chartInstances.sentimentPie) chartInstances.sentimentPie.destroy();
  const labels = ['正面', '中性', '负面'];
  const vals = labels.map(l => filteredData.filter(d => d.sentiment_label === l).length);
  chartInstances.sentimentPie = new Chart(ctx, {{
    type: 'doughnut',
    data: {{
      labels: ['正面', '中性', '负面'],
      datasets: [{{
        data: vals,
        backgroundColor: ['#38a169', '#d69e2e', '#e53e3e'],
      }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
  }});
}}

function renderPlatformChart() {{
  const ctx = document.getElementById('platformChart').getContext('2d');
  if (chartInstances.platform) chartInstances.platform.destroy();
  const dc = filteredData.filter(d => d.platform === 'douyin').length;
  const kc = filteredData.filter(d => d.platform === 'kuaishou').length;
  chartInstances.platform = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: ['抖音', '快手'],
      datasets: [{{
        label: '评论数',
        data: [dc, kc],
        backgroundColor: ['rgba(26,26,46,0.8)', 'rgba(255,107,53,0.8)'],
      }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
  }});
}}

function renderScoreDist() {{
  const ctx = document.getElementById('scoreDistChart').getContext('2d');
  if (chartInstances.scoreDist) chartInstances.scoreDist.destroy();
  const bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0];
  const counts = bins.map((b, i) => {{
    if (i === bins.length - 1) return filteredData.filter(d => d.sentiment_score >= b && d.sentiment_score <= 1).length;
    return filteredData.filter(d => d.sentiment_score >= b && d.sentiment_score < bins[i+1]).length;
  }});
  chartInstances.scoreDist = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: bins.map((b, i) => i < bins.length - 1 ? `${{(b*100).toFixed(0)}}-${{(bins[i+1]*100).toFixed(0)}}` : `${{(b*100).toFixed(0)}}`),
      datasets: [{{
        label: '评论数',
        data: counts,
        backgroundColor: counts.map((v, i) => {{
          if (i < 3) return 'rgba(229,62,62,0.7)';
          if (i < 5) return 'rgba(214,158,46,0.7)';
          return 'rgba(56,161,105,0.7)';
        }}),
      }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
  }});
}}

function renderMonthlyTrend() {{
  const ctx = document.getElementById('monthlyTrendChart').getContext('2d');
  if (chartInstances.monthlyTrend) chartInstances.monthlyTrend.destroy();
  const monthData = {{}};
  filteredData.forEach(d => {{
    const m = d.time.substring(0, 7);
    if (!monthData[m]) monthData[m] = 0;
    monthData[m]++;
  }});
  const labels = Object.keys(monthData).sort();
  const vals = labels.map(l => monthData[l]);
  chartInstances.monthlyTrend = new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: labels,
      datasets: [{{
        label: '评论数',
        data: vals,
        borderColor: '#805ad5',
        backgroundColor: 'rgba(128,90,213,0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 4,
      }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false }}
  }});
}}

function renderLikesDist() {{
  const ctx = document.getElementById('likesDistChart').getContext('2d');
  if (chartInstances.likesDist) chartInstances.likesDist.destroy();
  // 点赞数分段
  const buckets = [['0-10', 0, 10], ['10-50', 10, 50], ['50-100', 50, 100], ['100-500', 100, 500], ['500+', 500, Infinity]];
  const counts = buckets.map(([_, min, max]) =>
    filteredData.filter(d => d.likes >= min && d.likes < max).length
  );
  chartInstances.likesDist = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: buckets.map(b => b[0]),
      datasets: [{{
        label: '评论数',
        data: counts,
        backgroundColor: 'rgba(128,90,213,0.7)',
      }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
  }});
}}

function renderPlatformSentiment() {{
  const ctx = document.getElementById('platformSentimentChart').getContext('2d');
  if (chartInstances.platformSentiment) chartInstances.platformSentiment.destroy();
  const platforms = ['douyin', 'kuaishou'];
  const sentiments = ['正面', '中性', '负面'];
  const data = platforms.map(p => sentiments.map(s =>
    filteredData.filter(d => d.platform === p && d.sentiment_label === s).length
  ));
  chartInstances.platformSentiment = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: ['抖音', '快手'],
      datasets: [
        {{ label: '正面', data: [data[0][0], data[1][0]], backgroundColor: '#38a169' }},
        {{ label: '中性', data: [data[0][1], data[1][1]], backgroundColor: '#d69e2e' }},
        {{ label: '负面', data: [data[0][2], data[1][2]], backgroundColor: '#e53e3e' }},
      ]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, scales: {{ x: {{ stacked: true }}, y: {{ stacked: true }} }} }}
  }});
}}

// ========== 热门词云 ==========
function renderTagCloud() {{
  const container = document.getElementById('tagCloud');
  if (filteredData.length === 0) {{ container.innerHTML = '<p style="color:#718096;">无匹配数据</p>'; return; }}

  // 统计词频
  const wordCount = {{}};
  const allText = filteredData.map(d => d.content).join(' ');
  // 简单的分词：按非中文字符分割，保留中文词语
  const tokens = allText.match(/[\\u4e00-\\u9fff]+/g) || [];
  tokens.forEach(token => {{
    // 对每个中文词，按2-4字长度提取
    for (let i = 0; i < token.length - 1; i++) {{
      for (let j = 2; j <= 4 && i + j <= token.length; j++) {{
        const word = token.substring(i, i + j);
        if (!STOP_WORDS.has(word)) {{
          wordCount[word] = (wordCount[word] || 0) + 1;
        }}
      }}
    }}
  }});

  const sorted = Object.entries(wordCount).sort((a, b) => b[1] - a[1]).slice(0, 80);
  if (sorted.length === 0) {{ container.innerHTML = '<p style="color:#718096;">未提取到热门词</p>'; return; }}

  const maxCount = sorted[0][1];
  const minCount = sorted[sorted.length - 1][1];
  container.innerHTML = sorted.map(([word, count]) => {{
    const size = 12 + (count - minCount) / (maxCount - minCount) * 20;
    const opacity = 0.5 + (count - minCount) / (maxCount - minCount) * 0.5;
    return `<span class="tag-item" style="font-size:${{size.toFixed(0)}}px;opacity:${{opacity.toFixed(2)}};" onclick="searchTag('${{word}}')">${{word}}</span>`;
  }}).join('');
}}

function searchTag(word) {{
  document.getElementById('searchKeyword').value = word;
  doQuery();
  switchTab('table', document.querySelector('.tab'));
}}

// ========== 标签切换 ==========
function switchTab(name, el) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
  if (name === 'chart') setTimeout(renderCharts, 100);
  if (name === 'wordcloud') setTimeout(renderTagCloud, 100);
}}

// ========== 导出CSV ==========
function exportCSV() {{
  if (filteredData.length === 0) {{ alert('没有数据可导出'); return; }}
  const headers = ['ID', '平台', '评论内容', '情感标签', '情感分数', '点赞数', '时间'];
  const rows = filteredData.map(d => [
    d.id,
    d.platform === 'douyin' ? '抖音' : '快手',
    '"' + d.content.replace(/"/g, '""') + '"',
    d.sentiment_label,
    d.sentiment_score.toFixed(4),
    d.likes,
    d.time
  ]);
  const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\\n');
  const blob = new Blob(['\\ufeff' + csv], {{type: 'text/csv;charset=utf-8;'}});
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = '舆情数据查询结果.csv';
  link.click();
}}

// ========== 初始化 ==========
doQuery();
</script>
</body>
</html>"""

# 写入文件
output_path = "output/舆情数据查询系统.html"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

import os
file_size = os.path.getsize(output_path)
print(f"HTML文件已生成: {output_path}")
print(f"文件大小: {file_size} 字节")
