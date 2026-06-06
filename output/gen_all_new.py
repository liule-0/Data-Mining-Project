# -*- coding: utf-8 -*-
"""Generate all 3 new module HTML pages (no f-string issues)"""
import json, os

def read_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f), json.dumps(json.load(open(path, 'r', encoding='utf-8')), ensure_ascii=False)

def gen_elderly():
    records, data_json = read_json('output/elderly_care_data.json')
    types = sorted(set(r['类型'] for r in records))
    type_opts = ''.join(f'<option value="{t}">{t}</option>' for t in types)
    regions = ['中心城区', '主城新区', '渝东北', '渝东南']
    region_opts = ''.join(f'<option value="{r}">{r}</option>' for r in regions)
    
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>重庆市养老机构数据查询系统</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:#f0f4f8;color:#1a202c}
.header{background:linear-gradient(135deg,#c05621,#dd6b20);color:#fff;padding:24px 32px}
.header h1{font-size:24px;font-weight:600;margin-bottom:4px}
.header p{font-size:14px;opacity:.85}
.container{max-width:1400px;margin:0 auto;padding:20px}
.query-panel{background:#fff;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,.08);margin-bottom:20px}
.query-panel h2{font-size:18px;font-weight:600;margin-bottom:16px;color:#2d3748}
.query-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px}
.query-item{display:flex;flex-direction:column}
.query-item label{font-size:13px;font-weight:600;color:#4a5568;margin-bottom:6px}
.query-item select,.query-item input{padding:8px 12px;border:1px solid #e2e8f0;border-radius:6px;font-size:14px;background:#f7fafc}
.query-actions{display:flex;gap:12px;margin-top:20px;flex-wrap:wrap}
.btn{padding:10px 24px;border:none;border-radius:6px;font-size:14px;font-weight:600;cursor:pointer}
.btn-primary{background:#dd6b20;color:#fff}
.btn-success{background:#3182ce;color:#fff}
.btn-outline{background:#fff;color:#4a5568;border:1px solid #e2e8f0}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin-bottom:20px}
.stat-card{background:#fff;border-radius:10px;padding:16px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.stat-card .label{font-size:12px;color:#718096;margin-bottom:4px}
.stat-card .value{font-size:22px;font-weight:700;color:#2d3748}
.table-container{overflow-x:auto;background:#fff;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
table{width:100%;border-collapse:collapse;font-size:13px}
thead{background:#2d3748;color:#fff}
th{padding:12px 14px;text-align:left;font-weight:600;white-space:nowrap;cursor:pointer}
th:hover{background:#4a5568}
td{padding:10px 14px;border-bottom:1px solid #e2e8f0}
tr:hover{background:#fffaf0}
tr:nth-child(even){background:#f7fafc}
.region-badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600}
.rc{background:#ebf8ff;color:#2b6cb0}.rn{background:#f0fff4;color:#276749}.re{background:#fffaf0;color:#c05621}.rs{background:#faf5ff;color:#6b46c1}
.chart-container{background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.08);margin-bottom:20px}
.chart-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:900px){.chart-grid{grid-template-columns:1fr}}
.chart-box{position:relative;height:350px}
.pagination{display:flex;justify-content:space-between;align-items:center;padding:12px 0;font-size:13px;color:#718096}
.pagination button{padding:6px 16px;background:#fff;border:1px solid #e2e8f0;border-radius:6px;cursor:pointer;font-size:13px}
.pagination button:disabled{opacity:.4;cursor:default}
.topnav{background:#9b422b;color:rgba(255,255,255,.7);padding:8px 32px;font-size:13px;display:flex;align-items:center;gap:12px}
.topnav a{color:#fff;text-decoration:none;font-weight:600}
.topnav a:hover{text-decoration:underline}
.topnav span{color:rgba(255,255,255,.5);font-size:12px}
</style>
</head>
<body>
<div class="topnav"><a href="../index.html">返回首页</a><span>养老机构数据查询系统</span></div>
<div class="header"><h1>重庆市养老机构数据查询系统</h1><p>公办养老院 / 民办养老院 / 敬老院 / 老年公寓 / 护理院</p></div>
<div class="container">
<div class="query-panel"><h2>查询条件</h2>
<div class="query-grid">
<div class="query-item"><label>区县</label><select id="districtFilter"><option value="">全部区县</option></select></div>
<div class="query-item"><label>区域</label><select id="regionFilter" onchange="updateDistricts()"><option value="">全部区域</option>'''
    html += region_opts
    html += '''</select></div>
<div class="query-item"><label>机构类型</label><select id="typeFilter"><option value="">全部类型</option>'''
    html += type_opts
    html += '''</select></div>
<div class="query-item"><label>医养结合</label><select id="medicalFilter"><option value="">全部</option><option value="是">是</option><option value="否">否</option></select></div>
<div class="query-item"><label>最低评分</label><input type="number" id="minScore" min="0" max="5" step="0.1" placeholder="0"></div>
<div class="query-item"><label>最高月费(元)</label><input type="number" id="maxFee" min="0" placeholder="不限"></div>
<div class="query-item"><label>最低床位数</label><input type="number" id="minBeds" min="0" placeholder="不限"></div>
<div class="query-item"><label>关键词</label><input type="text" id="keyword" placeholder="搜索名称"></div>
</div>
<div class="query-actions"><button class="btn btn-primary" onclick="query()">查询</button><button class="btn btn-outline" onclick="resetQuery()">重置</button><button class="btn btn-success" onclick="exportCSV()">导出CSV</button></div>
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
<div style="padding:12px 14px;font-size:14px;font-weight:600;color:#2d3748;border-bottom:1px solid #e2e8f0;">查询结果 <span id="resultCount" style="font-weight:400;color:#718096;font-size:13px;"></span></div>
<table><thead><tr>
<th onclick="sortTable(0)">区县</th><th onclick="sortTable(1)">区域</th><th onclick="sortTable(2)">名称</th><th onclick="sortTable(3)">类型</th>
<th onclick="sortTable(4)">床位数</th><th onclick="sortTable(5)">入住率</th><th onclick="sortTable(6)">月费(元)</th><th onclick="sortTable(7)">评分</th><th>医养结合</th><th>联系电话</th>
</tr></thead>
<tbody id="tableBody"></tbody></table>
<div class="pagination"><span id="pageInfo"></span><div><button id="prevBtn" onclick="prevPage()">上一页</button><button id="nextBtn" onclick="nextPage()" style="margin-left:8px;">下一页</button></div></div>
</div>
</div>
<script>
var DATA = ''' + data_json + ''';

function regClass(r){if(r=="中心城区")return"rc";if(r=="主城新区")return"rn";if(r=="渝东北")return"re";return"rs"}
var DISTRICTS = [];DATA.forEach(function(d){if(DISTRICTS.indexOf(d["区县"])<0)DISTRICTS.push(d["区县"])});DISTRICTS.sort();
var filteredData = [];var currentPage = 1;var PG = 15;var sortCol = -1;var sortAsc = true;

document.getElementById("districtFilter").innerHTML = '<option value="">全部区县</option>'+DISTRICTS.map(function(d){return"<option value=\\""+d+"\\">"+d+"</option>"}).join("");

function updateDistricts(){var r=document.getElementById("regionFilter").value;var s=document.getElementById("districtFilter");var ds=r?[...new Set(DATA.filter(function(d){return d["区域"]===r}).map(function(d){return d["区县"]}))].sort():DISTRICTS;s.innerHTML='<option value="">全部区县</option>'+ds.map(function(d){return"<option value=\\""+d+"\\">"+d+"</option>"}).join("")}

function query(){var df=document.getElementById("districtFilter").value;var rf=document.getElementById("regionFilter").value;var tf=document.getElementById("typeFilter").value;var mf=document.getElementById("medicalFilter").value;var ms=parseFloat(document.getElementById("minScore").value)||0;var mf2=parseFloat(document.getElementById("maxFee").value)||Infinity;var mb=parseInt(document.getElementById("minBeds").value)||0;var kw=document.getElementById("keyword").value.trim().toLowerCase();filteredData=DATA.filter(function(d){if(df&&d["区县"]!==df)return false;if(rf&&d["区域"]!==rf)return false;if(tf&&d["类型"]!==tf)return false;if(mf&&d["医养结合"]!==mf)return false;if(d["评分"]<ms)return false;if(d["收费标准_元月"]>mf2)return false;if(d["床位数"]<mb)return false;if(kw&&d["名称"].toLowerCase().indexOf(kw)<0)return false;return true});currentPage=1;render()}

function resetQuery(){document.querySelectorAll(".query-panel select,.query-panel input").forEach(function(e){e.value=""});query()}

function render(){renderStats();renderCharts();renderTable()}

function renderStats(){var n=filteredData.length;var tb=filteredData.reduce(function(s,d){return s+d["床位数"]},0);var tr=filteredData.reduce(function(s,d){return s+d["入住人数"]},0);var ao=n?(tr/tb*100):0;var af=n?Math.round(filteredData.reduce(function(s,d){return s+d["收费标准_元月"]},0)/n):0;var mc=filteredData.filter(function(d){return d["医养结合"]==="是"}).length;var minF=n?Math.round(filteredData.reduce(function(s,d){return Math.min(s,d["收费标准_元月"])},Infinity)):0;var maxF=n?Math.round(filteredData.reduce(function(s,d){return Math.max(s,d["收费标准_元月"])},0)):0;document.getElementById("statsGrid").innerHTML='<div class="stat-card" style="border-left:4px solid #dd6b20"><div class="label">机构总数</div><div class="value">'+n+'</div><div class="sub">'+new Set(filteredData.map(function(d){return d["类型"]})).size+'种</div></div><div class="stat-card" style="border-left:4px solid #3182ce"><div class="label">总床位数</div><div class="value">'+tb.toLocaleString()+'</div><div class="sub">入住'+tr.toLocaleString()+'人</div></div><div class="stat-card" style="border-left:4px solid #38a169"><div class="label">平均入住率</div><div class="value">'+ao.toFixed(1)+'%</div><div class="sub">'+mc+'家医养结合</div></div><div class="stat-card" style="border-left:4px solid #d69e2e"><div class="label">平均月费</div><div class="value">'+af.toLocaleString()+'元</div><div class="sub">'+minF.toLocaleString()+'-'+maxF.toLocaleString()+'元</div></div>'}

var charts={};
function renderCharts(){
var c1=document.getElementById("typeChart").getContext("2d");if(charts.type)charts.type.destroy();var g1={};filteredData.forEach(function(d){g1[d["类型"]]=(g1[d["类型"]]||0)+1});charts.type=new Chart(c1,{type:"bar",data:{labels:Object.keys(g1),datasets:[{data:Object.values(g1),backgroundColor:["#dd6b20","#ed8936","#f6ad55","#fbd38d","#feebc8"]}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},title:{display:true,text:"各类型机构数量",color:"#2d3748"}},scales:{y:{beginAtZero:true,ticks:{stepSize:1}}}}});
var c2=document.getElementById("regionChart").getContext("2d");if(charts.region)charts.region.destroy();var g2={};filteredData.forEach(function(d){g2[d["区域"]]=(g2[d["区域"]]||0)+1});var rl=["中心城区","主城新区","渝东北","渝东南"].filter(function(r){return g2[r]});charts.region=new Chart(c2,{type:"doughnut",data:{labels:rl,datasets:[{data:rl.map(function(r){return g2[r]}),backgroundColor:["#3182ce","#38a169","#d69e2e","#805ad5"]}]},options:{responsive:true,maintainAspectRatio:false,plugins:{title:{display:true,text:"各区域机构分布",color:"#2d3748"}}}});
var c3=document.getElementById("occChart").getContext("2d");if(charts.occ)charts.occ.destroy();var bins=[0,60,70,80,90,100];var blbls=["<60%","60-70%","70-80%","80-90%","90-100%"];var cnts=[0,0,0,0,0];filteredData.forEach(function(d){var r=d["入住率"];for(var i=0;i<5;i++){if(r>=bins[i]&&r<bins[i+1]){cnts[i]++;break}}});charts.occ=new Chart(c3,{type:"bar",data:{labels:blbls,datasets:[{data:cnts,backgroundColor:"#dd6b20"}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},title:{display:true,text:"入住率分布",color:"#2d3748"}},scales:{y:{beginAtZero:true,ticks:{stepSize:1}}}}});
var c4=document.getElementById("feeChart").getContext("2d");if(charts.fee)charts.fee.destroy();var fb=[0,1500,3000,5000,8000,15000];var flbls=["<1500","1500-3000","3000-5000","5000-8000","8000+"];var fcnts=[0,0,0,0,0];filteredData.forEach(function(d){var f=d["收费标准_元月"];for(var i=0;i<5;i++){if(f>=fb[i]&&f<fb[i+1]){fcnts[i]++;break}}});charts.fee=new Chart(c4,{type:"bar",data:{labels:flbls,datasets:[{data:fcnts,backgroundColor:"#ed8936"}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},title:{display:true,text:"月费分布(元)",color:"#2d3748"}},scales:{y:{beginAtZero:true,ticks:{stepSize:1}}}}})}

function sortTable(col){if(sortCol===col){sortAsc=!sortAsc}else{sortCol=col;sortAsc=true}var keys=["区县","区域","名称","类型","床位数","入住率","收费标准_元月","评分"];var key=keys[col];filteredData.sort(function(a,b){var va=a[key],vb=b[key];if(typeof va==="number")return sortAsc?va-vb:vb-va;return sortAsc?String(va).localeCompare(String(vb),"zh"):String(vb).localeCompare(String(va),"zh")});renderTable()}

function renderTable(){var start=(currentPage-1)*PG;var end=Math.min(start+PG,filteredData.length);var pd=filteredData.slice(start,end);var tp=Math.ceil(filteredData.length/PG)||1;document.getElementById("resultCount").textContent="（共"+filteredData.length+"条）";document.getElementById("pageInfo").textContent="第"+currentPage+"/"+tp+"页";document.getElementById("prevBtn").disabled=currentPage<=1;document.getElementById("nextBtn").disabled=currentPage>=tp;var h="";for(var i=0;i<pd.length;i++){var d=pd[i];var oc=d["入住率"]>=90?"#e53e3e":d["入住率"]>=75?"#d69e2e":"#38a169";h+="<tr><td style=\\"font-weight:600\\">"+d["区县"]+'</td><td><span class="region-badge '+regClass(d["区域"])+'">'+d["区域"]+'</span></td><td>'+d["名称"]+'</td><td>'+d["类型"]+'</td><td>'+d["床位数"].toLocaleString()+'</td><td style=\\"color:'+oc+';font-weight:600\\">'+d["入住率"].toFixed(1)+'%</td><td>'+d["收费标准_元月"].toLocaleString()+'</td><td>'+d["评分"].toFixed(1)+'</td><td>'+(d["医养结合"]==="是"?'<span style=\\"color:#38a169;font-weight:600\\">是</span>':'<span style=\\"color:#a0aec0\\">否</span>')+'</td><td style=\\"color:#718096\\">'+d["联系电话"]+'</td></tr>'}document.getElementById("tableBody").innerHTML=h}

function prevPage(){if(currentPage>1){currentPage--;renderTable()}}
function nextPage(){if(currentPage*PG<filteredData.length){currentPage++;renderTable()}}
function exportCSV(){var hd=["区县","区域","名称","类型","床位数","入住人数","入住率","收费标准_元月","评分","员工数","医养结合","联系电话"];var rows=filteredData.map(function(d){return hd.map(function(h){return"\\""+(d[h]||"")+"\\""}).join(",")});var csv="\\uFEFF"+hd.join(",")+"\\n"+rows.join("\\n");var blob=new Blob([csv],{type:"text/csv;charset=utf-8"});var a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="养老机构数据.csv";a.click()}
query();
</script>
</body>
</html>'''
    
    outpath = 'output/养老机构数据查询系统.html'
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"OK {os.path.basename(outpath)} ({os.path.getsize(outpath)/1024:.0f}KB)")

# Also generate the medical institutions page
def gen_medical():
    records, data_json = read_json('output/medical_inst_data.json')
    mtypes = sorted(set(r['类型'] for r in records))
    type_opts = ''.join(f'<option value="{t}">{t}</option>' for t in mtypes)
    regions = ['中心城区', '主城新区', '渝东北', '渝东南']
    region_opts = ''.join(f'<option value="{r}">{r}</option>' for r in regions)
    
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>重庆市医疗机构数据查询系统</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:#f0f4f8;color:#1a202c}
.header{background:linear-gradient(135deg,#2b6cb0,#3182ce);color:#fff;padding:24px 32px}
.header h1{font-size:24px;font-weight:600;margin-bottom:4px}
.header p{font-size:14px;opacity:.85}
.container{max-width:1400px;margin:0 auto;padding:20px}
.query-panel{background:#fff;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,.08);margin-bottom:20px}
.query-panel h2{font-size:18px;font-weight:600;margin-bottom:16px;color:#2d3748}
.query-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px}
.query-item{display:flex;flex-direction:column}
.query-item label{font-size:13px;font-weight:600;color:#4a5568;margin-bottom:6px}
.query-item select,.query-item input{padding:8px 12px;border:1px solid #e2e8f0;border-radius:6px;font-size:14px;background:#f7fafc}
.query-actions{display:flex;gap:12px;margin-top:20px;flex-wrap:wrap}
.btn{padding:10px 24px;border:none;border-radius:6px;font-size:14px;font-weight:600;cursor:pointer}
.btn-primary{background:#3182ce;color:#fff}
.btn-success{background:#38a169;color:#fff}
.btn-outline{background:#fff;color:#4a5568;border:1px solid #e2e8f0}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin-bottom:20px}
.stat-card{background:#fff;border-radius:10px;padding:16px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.stat-card .label{font-size:12px;color:#718096;margin-bottom:4px}
.stat-card .value{font-size:22px;font-weight:700;color:#2d3748}
.table-container{overflow-x:auto;background:#fff;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
table{width:100%;border-collapse:collapse;font-size:13px}
thead{background:#2d3748;color:#fff}
th{padding:12px 14px;text-align:left;font-weight:600;white-space:nowrap;cursor:pointer}
th:hover{background:#4a5568}
td{padding:10px 14px;border-bottom:1px solid #e2e8f0}
tr:hover{background:#ebf8ff}
tr:nth-child(even){background:#f7fafc}
.region-badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600}
.rc{background:#ebf8ff;color:#2b6cb0}.rn{background:#f0fff4;color:#276749}.re{background:#fffaf0;color:#c05621}.rs{background:#faf5ff;color:#6b46c1}
.chart-container{background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.08);margin-bottom:20px}
.chart-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:900px){.chart-grid{grid-template-columns:1fr}}
.chart-box{position:relative;height:350px}
.pagination{display:flex;justify-content:space-between;align-items:center;padding:12px 0;font-size:13px;color:#718096}
.pagination button{padding:6px 16px;background:#fff;border:1px solid #e2e8f0;border-radius:6px;cursor:pointer;font-size:13px}
.pagination button:disabled{opacity:.4;cursor:default}
.topnav{background:#1a365d;color:rgba(255,255,255,.7);padding:8px 32px;font-size:13px;display:flex;align-items:center;gap:12px}
.topnav a{color:#fff;text-decoration:none;font-weight:600}
.topnav a:hover{text-decoration:underline}
.topnav span{color:rgba(255,255,255,.5);font-size:12px}
</style>
</head>
<body>
<div class="topnav"><a href="../index.html">返回首页</a><span>医疗机构数据查询系统</span></div>
<div class="header"><h1>重庆市医疗机构数据查询系统</h1><p>三甲医院 / 二甲医院 / 社区医院 / 乡镇卫生院 / 专科医院</p></div>
<div class="container">
<div class="query-panel"><h2>查询条件</h2>
<div class="query-grid">
<div class="query-item"><label>区县</label><select id="districtFilter"><option value="">全部区县</option></select></div>
<div class="query-item"><label>区域</label><select id="regionFilter" onchange="updateDistricts()"><option value="">全部区域</option>'''
    html += region_opts
    html += '''</select></div>
<div class="query-item"><label>机构类型</label><select id="typeFilter"><option value="">全部类型</option>'''
    html += type_opts
    html += '''</select></div>
<div class="query-item"><label>最低床位数</label><input type="number" id="minBeds" min="0" placeholder="不限"></div>
<div class="query-item"><label>最低医生数</label><input type="number" id="minDoctors" min="0" placeholder="不限"></div>
<div class="query-item"><label>关键词</label><input type="text" id="keyword" placeholder="搜索名称"></div>
</div>
<div class="query-actions"><button class="btn btn-primary" onclick="query()">查询</button><button class="btn btn-outline" onclick="resetQuery()">重置</button><button class="btn btn-success" onclick="exportCSV()">导出CSV</button></div>
</div>
<div class="stats-grid" id="statsGrid"></div>
<div class="chart-grid">
<div class="chart-container"><div class="chart-box"><canvas id="typeChart"></canvas></div></div>
<div class="chart-container"><div class="chart-box"><canvas id="regionChart"></canvas></div></div>
</div>
<div class="chart-grid">
<div class="chart-container"><div class="chart-box"><canvas id="levelChart"></canvas></div></div>
<div class="chart-container"><div class="chart-box"><canvas id="bedDistChart"></canvas></div></div>
</div>
<div class="table-container">
<div style="padding:12px 14px;font-size:14px;font-weight:600;color:#2d3748;border-bottom:1px solid #e2e8f0;">查询结果 <span id="resultCount" style="font-weight:400;color:#718096;font-size:13px;"></span></div>
<table><thead><tr>
<th onclick="sortTable(0)">区县</th><th onclick="sortTable(1)">区域</th><th>名称</th><th onclick="sortTable(3)">类型</th>
<th onclick="sortTable(4)">床位数</th><th onclick="sortTable(5)">医生数</th><th onclick="sortTable(6)">护士数</th><th onclick="sortTable(7)">科室数</th><th>年门诊量</th><th>联系电话</th>
</tr></thead>
<tbody id="tableBody"></tbody></table>
<div class="pagination"><span id="pageInfo"></span><div><button id="prevBtn" onclick="prevPage()">上一页</button><button id="nextBtn" onclick="nextPage()" style="margin-left:8px;">下一页</button></div></div>
</div>
</div>
<script>
var DATA = ''' + data_json + ''';

function regClass(r){if(r=="中心城区")return"rc";if(r=="主城新区")return"rn";if(r=="渝东北")return"re";return"rs"}
var DISTRICTS = [];DATA.forEach(function(d){if(DISTRICTS.indexOf(d["区县"])<0)DISTRICTS.push(d["区县"])});DISTRICTS.sort();
var filteredData = [];var currentPage = 1;var PG = 15;var sortCol = -1;var sortAsc = true;

document.getElementById("districtFilter").innerHTML = '<option value="">全部区县</option>'+DISTRICTS.map(function(d){return"<option value=\\""+d+"\\">"+d+"</option>"}).join("");

function updateDistricts(){var r=document.getElementById("regionFilter").value;var s=document.getElementById("districtFilter");var ds=r?[...new Set(DATA.filter(function(d){return d["区域"]===r}).map(function(d){return d["区县"]}))].sort():DISTRICTS;s.innerHTML='<option value="">全部区县</option>'+ds.map(function(d){return"<option value=\\""+d+"\\">"+d+"</option>"}).join("")}

function query(){var df=document.getElementById("districtFilter").value;var rf=document.getElementById("regionFilter").value;var tf=document.getElementById("typeFilter").value;var mb=parseInt(document.getElementById("minBeds").value)||0;var md=parseInt(document.getElementById("minDoctors").value)||0;var kw=document.getElementById("keyword").value.trim().toLowerCase();filteredData=DATA.filter(function(d){if(df&&d["区县"]!==df)return false;if(rf&&d["区域"]!==rf)return false;if(tf&&d["类型"]!==tf)return false;if(d["床位数"]<mb)return false;if(d["医生数"]<md)return false;if(kw&&d["名称"].toLowerCase().indexOf(kw)<0)return false;return true});currentPage=1;render()}

function resetQuery(){document.querySelectorAll(".query-panel select,.query-panel input").forEach(function(e){e.value=""});query()}

function render(){renderStats();renderCharts();renderTable()}

function renderStats(){var n=filteredData.length;var tb=filteredData.reduce(function(s,d){return s+d["床位数"]},0);var td=filteredData.reduce(function(s,d){return s+d["医生数"]},0);var tn=filteredData.reduce(function(s,d){return s+d["护士数"]},0);var ap=filteredData.reduce(function(s,d){return s+d["年门诊量"]},0);var l3=filteredData.filter(function(d){return d["类型"]==="三甲医院"}).length;document.getElementById("statsGrid").innerHTML='<div class="stat-card" style="border-left:4px solid #3182ce"><div class="label">机构总数</div><div class="value">'+n+'</div><div class="sub">'+l3+'家三甲</div></div><div class="stat-card" style="border-left:4px solid #38a169"><div class="label">总床位数</div><div class="value">'+tb.toLocaleString()+'</div><div class="sub">医生'+td.toLocaleString()+'人</div></div><div class="stat-card" style="border-left:4px solid #d69e2e"><div class="label">医护比</div><div class="value">'+(td?(tn/td).toFixed(2):0)+'</div><div class="sub">护士'+tn.toLocaleString()+'人</div></div><div class="stat-card" style="border-left:4px solid #e53e3e"><div class="label">年门诊总量</div><div class="value">'+(ap/10000).toFixed(1)+'万</div><div class="sub">'+n+'家机构</div></div>'}

var charts={};
function renderCharts(){
var c1=document.getElementById("typeChart").getContext("2d");if(charts.type)charts.type.destroy();var g1={};filteredData.forEach(function(d){g1[d["类型"]]=(g1[d["类型"]]||0)+1});charts.type=new Chart(c1,{type:"bar",data:{labels:Object.keys(g1),datasets:[{data:Object.values(g1),backgroundColor:["#3182ce","#63b3ed","#90cdf4","#bee3f8","#ebf8ff","#2b6cb0"]}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},title:{display:true,text:"各类型机构数量",color:"#2d3748"}},scales:{y:{beginAtZero:true,ticks:{stepSize:1}}}}});
var c2=document.getElementById("regionChart").getContext("2d");if(charts.region)charts.region.destroy();var g2={};filteredData.forEach(function(d){g2[d["区域"]]=(g2[d["区域"]]||0)+1});var rl=["中心城区","主城新区","渝东北","渝东南"].filter(function(r){return g2[r]});charts.region=new Chart(c2,{type:"pie",data:{labels:rl,datasets:[{data:rl.map(function(r){return g2[r]}),backgroundColor:["#3182ce","#38a169","#d69e2e","#805ad5"]}]},options:{responsive:true,maintainAspectRatio:false,plugins:{title:{display:true,text:"各区域机构分布",color:"#2d3748"}}}});
var c3=document.getElementById("levelChart").getContext("2d");if(charts.level)charts.level.destroy();var lvls={1:"一级",2:"二级",3:"三级"};var g3={};filteredData.forEach(function(d){var l=lvls[d["等级"]]||"其他";g3[l]=(g3[l]||0)+1});charts.level=new Chart(c3,{type:"doughnut",data:{labels:Object.keys(g3),datasets:[{data:Object.values(g3),backgroundColor:["#bee3f8","#63b3ed","#3182ce"]}]},options:{responsive:true,maintainAspectRatio:false,plugins:{title:{display:true,text:"等级分布",color:"#2d3748"}}}});
var c4=document.getElementById("bedDistChart").getContext("2d");if(charts.bed)charts.bed.destroy();var bins=[0,50,200,500,1000,3000];var blbls=["<50","50-200","200-500","500-1000","1000+"];var cnts=[0,0,0,0,0];filteredData.forEach(function(d){var b=d["床位数"];for(var i=0;i<5;i++){if(b>=bins[i]&&b<bins[i+1]){cnts[i]++;break}}});charts.bed=new Chart(c4,{type:"bar",data:{labels:blbls,datasets:[{data:cnts,backgroundColor:"#3182ce"}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},title:{display:true,text:"床位规模分布",color:"#2d3748"}},scales:{y:{beginAtZero:true,ticks:{stepSize:1}}}}})}

function sortTable(col){if(sortCol===col){sortAsc=!sortAsc}else{sortCol=col;sortAsc=true}var keys=["区县","区域","名称","类型","床位数","医生数","护士数","科室数"];var key=keys[col];filteredData.sort(function(a,b){var va=a[key],vb=b[key];if(typeof va==="number")return sortAsc?va-vb:vb-va;return sortAsc?String(va).localeCompare(String(vb),"zh"):String(vb).localeCompare(String(va),"zh")});renderTable()}

function renderTable(){var start=(currentPage-1)*PG;var end=Math.min(start+PG,filteredData.length);var pd=filteredData.slice(start,end);var tp=Math.ceil(filteredData.length/PG)||1;document.getElementById("resultCount").textContent="（共"+filteredData.length+"条）";document.getElementById("pageInfo").textContent="第"+currentPage+"/"+tp+"页";document.getElementById("prevBtn").disabled=currentPage<=1;document.getElementById("nextBtn").disabled=currentPage>=tp;var h="";for(var i=0;i<pd.length;i++){var d=pd[i];var lv=d["等级"]>=3?"#e53e3e":d["等级"]>=2?"#d69e2e":"#718096";h+="<tr><td style=\\"font-weight:600\\">"+d["区县"]+'</td><td><span class="region-badge '+regClass(d["区域"])+'">'+d["区域"]+'</span></td><td>'+d["名称"]+'</td><td>'+d["类型"]+'</td><td>'+d["床位数"].toLocaleString()+'</td><td>'+d["医生数"].toLocaleString()+'</td><td>'+d["护士数"].toLocaleString()+'</td><td>'+d["科室数"]+'</td><td>'+(d["年门诊量"]/10000).toFixed(1)+'万</td><td style=\\"color:#718096\\">'+d["联系电话"]+'</td></tr>'}document.getElementById("tableBody").innerHTML=h}

function prevPage(){if(currentPage>1){currentPage--;renderTable()}}
function nextPage(){if(currentPage*PG<filteredData.length){currentPage++;renderTable()}}
function exportCSV(){var hd=["区县","区域","名称","类型","等级","床位数","医生数","护士数","科室数","年门诊量","联系电话"];var rows=filteredData.map(function(d){return hd.map(function(h){return"\\""+(d[h]||"")+"\\""}).join(",")});var csv="\\uFEFF"+hd.join(",")+"\\n"+rows.join("\\n");var blob=new Blob([csv],{type:"text/csv;charset=utf-8"});var a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="医疗机构数据.csv";a.click()}
query();
</script>
</body>
</html>'''

    outpath = 'output/医疗机构数据查询系统.html'
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"OK {os.path.basename(outpath)} ({os.path.getsize(outpath)/1024:.0f}KB)")

if __name__ == '__main__':
    gen_elderly()
    gen_medical()
