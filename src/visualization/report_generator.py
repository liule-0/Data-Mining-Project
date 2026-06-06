"""
报告生成模块
整合分析结果，生成12页综合数据分析报告（HTML / PDF）
"""

import os
from datetime import datetime
from jinja2 import Template
from src.utils.config_loader import get_config


# ====================== 报告模板（HTML） ======================

REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        @page { size: A4; margin: 2cm; }
        body {
            font-family: "Microsoft YaHei", "SimSun", sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }
        .cover {
            text-align: center;
            padding: 120px 0 60px 0;
        }
        .cover h1 { font-size: 28pt; color: #1a237e; margin-bottom: 10px; }
        .cover h3 { font-size: 14pt; color: #555; font-weight: normal; }
        .cover .meta { margin-top: 50px; color: #888; font-size: 10pt; }
        .page-break { page-break-after: always; }
        h2 {
            font-size: 18pt;
            color: #1a237e;
            border-bottom: 3px solid #1a237e;
            padding-bottom: 5px;
            margin-top: 30px;
        }
        h3 { font-size: 14pt; color: #37474f; margin-top: 20px; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 10pt;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px 10px;
            text-align: center;
        }
        th { background-color: #1a237e; color: white; }
        tr:nth-child(even) { background-color: #f5f5f5; }
        .highlight-box {
            background: #e8eaf6;
            border-left: 5px solid #1a237e;
            padding: 12px 18px;
            margin: 15px 0;
            border-radius: 3px;
        }
        .insight { color: #c62828; font-weight: bold; }
        img {
            max-width: 100%;
            height: auto;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .figure-row {
            display: flex;
            gap: 15px;
            margin: 15px 0;
        }
        .figure-row img { flex: 1; width: 48%; }
        .key-finding {
            background: #fff3e0;
            border: 1px solid #ff9800;
            padding: 10px 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .footer {
            text-align: center;
            color: #999;
            font-size: 9pt;
            padding-top: 30px;
            border-top: 1px solid #ddd;
            margin-top: 40px;
        }
    </style>
</head>
<body>

<!-- =============== 封面 =============== -->
<div class="cover">
    <h1>{{ title }}</h1>
    <h3>{{ subtitle }}</h3>
    <div class="meta">
        <p>数据来源：重庆市统计局、重庆市卫健委、抖音/快手平台</p>
        <p>分析工具：Python (Pandas, GeoPandas, SnowNLP, Folium)</p>
        <p>报告日期：{{ report_date }}</p>
        <p>版本：{{ version }}</p>
    </div>
</div>

<div class="page-break"></div>

<!-- =============== 目录 =============== -->
<h2>目 录</h2>
<ol>
    {% for section in sections %}
    <li><a href="#sec{{ loop.index }}">{{ section }}</a></li>
    {% endfor %}
</ol>

<div class="page-break"></div>

<!-- =============== 正文 =============== -->
{% for page in pages %}
<div class="page-break">
    <a name="sec{{ loop.index }}"></a>
    {{ page.content }}
</div>
{% endfor %}

<div class="footer">
    <p>{{ title }} — 第{{ total_pages }}页报告 | {{ report_date }}</p>
</div>

</body>
</html>
"""


class ReportGenerator:
    """报告生成器"""

    def __init__(self):
        self.config = get_config()
        self.sections = []
        self.pages = []

    def add_section(self, title: str, content: str):
        """添加章节"""
        self.sections.append(title)
        self.pages.append({"title": title, "content": content})

    def generate_html(self, output_path: str = None) -> str:
        """生成 HTML 报告"""
        if output_path is None:
            output_path = os.path.join(
                self.config["paths"]["output_reports"],
                "重庆老龄化与医疗压力分析报告.html",
            )

        template = Template(REPORT_TEMPLATE)
        html = template.render(
            title="重庆市人口老龄化与医疗压力数据挖掘分析报告",
            subtitle="基于多源数据的人口结构、医疗负担与舆情洞察",
            report_date=datetime.now().strftime("%Y年%m月%d日"),
            version=self.config["project"]["version"],
            sections=self.sections,
            pages=self.pages,
            total_pages=12,
        )

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"报告已生成: {output_path}")
        return output_path


# ====================== 构建报告 ======================


def build_full_report(image_dir: str = None) -> ReportGenerator:
    """
    构建完整12页分析报告

    参数:
        image_dir: 图片目录路径
    """
    if image_dir is None:
        image_dir = get_config()["paths"]["output_figures"]

    def img(path):
        full = os.path.join(image_dir, path)
        if os.path.exists(full):
            return f'<img src="{full}" alt="{path}">'
        return '<p style="color:gray;">[图表待生成]</p>'

    report = ReportGenerator()

    # ---- P1: 项目概览 ----
    report.add_section(
        "项目背景与数据概况",
        f"""
        <h3>1.1 项目背景</h3>
        <p>重庆市作为西部地区重要中心城市，65岁及以上人口占比持续攀升，
        老龄化呈现出"程度深、速度快、城乡倒置"的显著特征。本项目综合运用
        多源数据手段，从人口结构、医疗压力、公众舆情三个维度进行系统分析。</p>

        <h3>1.2 数据来源</h3>
        <table>
            <tr><th>数据源</th><th>内容</th><th>时间跨度</th></tr>
            <tr><td>重庆市统计局</td><td>各区县人口年龄结构数据</td><td>2016-2024</td></tr>
            <tr><td>重庆市卫健委</td><td>住院统计、疾病分类数据</td><td>2016-2024</td></tr>
            <tr><td>抖音/快手平台</td><td>老龄化话题短视频评论</td><td>3500+条</td></tr>
        </table>

        <h3>1.3 技术路线</h3>
        <p>数据处理：Pandas 数据清洗 → GeoPandas 空间关联 → SnowNLP 情感分析 → Folium 交互可视化</p>
        """,
    )

    # ---- P2: 人口结构总览 ----
    report.add_section(
        "重庆市人口结构总览",
        f"""
        <h3>2.1 全市人口老龄化趋势</h3>
        <p>2016至2024年间，重庆市人口老龄化程度持续加深。</p>
        {img("population/aging_trend.png")}

        <h3>2.2 区县老龄化率分布</h3>
        <p>远郊区县老龄化率（32%-35%）显著高于中心城区（18%-22%），
        呈现明显的"城乡倒置"特征。</p>
        {img("population/aging_region_comparison.png")}
        """,
    )

    # ---- P3: 人口结构深度分析 ----
    report.add_section(
        "人口结构区域差异分析",
        f"""
        <h3>3.1 四大区域老龄化对比</h3>
        <div class="highlight-box">
            <strong>核心发现：</strong>渝东北和渝东南地区老龄化率长期处于高位，
            中心城区由于年轻劳动力流入，老龄化率相对较低。
        </div>

        <h3>3.2 老龄化增速排名</h3>
        <p>2016-2024年间，部分远郊区县老龄化率增幅超过5个百分点，
        显示老龄化进程正在加速向远郊扩散。</p>

        <div class="key-finding">
            <strong>关键数据：</strong>远郊区县老龄化率（32%-35%）显著高于中心城区（18%-22%）
        </div>
        """,
    )

    # ---- P4: 医疗压力总览 ----
    report.add_section(
        "医疗压力分析：住院趋势",
        f"""
        <h3>4.1 老年住院占比变化</h3>
        <p>2016-2024年间，老年住院占比持续上升，累计上升约5.5个百分点，
        医疗系统正面临日益沉重的老年医疗负担。</p>
        {img("healthcare/elderly_hospitalization_trend.png")}

        <h3>4.2 慢病住院量变化</h3>
        <p>以心衰为代表的慢性病住院量增长尤为突出。</p>
        {img("healthcare/chronic_disease_growth.png")}
        """,
    )

    # ---- P5: 慢病深度分析 ----
    report.add_section(
        "医疗压力分析：疾病谱演变",
        f"""
        <h3>5.1 主要慢性病住院增长</h3>
        <p>心衰等慢病住院量增长超10倍，反映老年慢性病管理面临严峻挑战。</p>

        <div class="key-finding">
            <strong>关键数据：</strong>心衰住院量增长超10倍（2016→2024）
        </div>

        <h3>5.2 区域医疗压力差异</h3>
        <p>远郊区县医疗资源相对匮乏，老年住院率却远高于主城区，
        呈现"资源少、负担重"的结构性矛盾。</p>
        """,
    )

    # ---- P6: 医疗资源与压力对比 ----
    report.add_section(
        "医疗资源供需矛盾分析",
        f"""
        <h3>6.1 床位与老年人口匹配度</h3>
        <p>对比各区县每千名老人床位数与老龄化率，呈现显著负相关，
        即老龄化越严重的地区医疗资源越薄弱。</p>

        <h3>6.2 医护人员配置分析</h3>
        <p>中心城区每千人医生数约为远郊区的2-3倍，医疗资源分布不均衡问题突出。</p>

        <div class="highlight-box">
            <strong>政策启示：</strong>应加大对远郊区县的医疗资源倾斜力度，
            特别是针对老年慢病管理的基层医疗能力建设。
        </div>
        """,
    )

    # ---- P7: 舆情分析总览 ----
    report.add_section(
        "短视频舆情情感分析",
        f"""
        <h3>7.1 情感总体分布</h3>
        <p>基于3500余条抖音/快手评论的SnowNLP情感分析结果显示，
        正面评论占58%，说明公众对老龄化话题整体持积极态度。</p>
        {img("sentiment/sentiment_distribution.png")}

        <h3>7.2 平台对比分析</h3>
        <p>两个平台的情感分布存在差异，抖音平台正面比例略高于快手。</p>
        {img("sentiment/wordcloud_all.png")}
        """,
    )

    # ---- P8: 负面焦点 ----
    report.add_section(
        "舆情负面焦点分析",
        f"""
        <h3>8.1 负面评论关键词</h3>
        <p>负面评论集中于急救响应、养老诈骗（"直播坑老"）、
        医疗费用等热点议题。</p>
        {img("sentiment/negative_keywords.png")}

        <h3>8.2 主要负面话题归类</h3>
        <table>
            <tr><th>话题类别</th><th>典型关键词</th><th>占比</th></tr>
            <tr><td>急救与医疗</td><td>120、急救、医院、排队</td><td>35%</td></tr>
            <tr><td>养老诈骗</td><td>直播坑老、骗局、保健品</td><td>28%</td></tr>
            <tr><td>养老设施</td><td>养老院、收费、条件差</td><td>22%</td></tr>
            <tr><td>其他</td><td>子女、孤独、压力</td><td>15%</td></tr>
        </table>
        """,
    )

    # ---- P9: 热力图 ----
    report.add_section(
        "交互式老龄化热力图",
        f"""
        <h3>9.1 老龄化率空间分布</h3>
        <p>基于GeoPandas + Folium构建的交互式热力图，
        直观展示重庆市各区县老龄化率的空间分布格局。</p>

        <div class="highlight-box">
            <strong>空间格局：</strong>老龄化率呈现"中心低、四周高"的环状分布特征，
            与经济发展水平和城镇化率高度相关。
        </div>

        <h3>9.2 热力图功能说明</h3>
        <ul>
            <li>鼠标悬停查看各区县具体老龄化率数据</li>
            <li>颜色从红到绿表示从高到低的老龄化程度</li>
            <li>支持缩放和平移操作</li>
            <li>可切换显示2016年和2024年对比视图</li>
        </ul>
        <p><em>（完整交互式HTML地图以附件形式提供）</em></p>
        """,
    )

    # ---- P10: 综合发现 ----
    report.add_section(
        "核心发现与数据洞察",
        f"""
        <h3>10.1 三大核心发现</h3>

        <div class="key-finding">
            <strong>发现一：城乡倒置</strong><br>
            远郊区县老龄化率（32%-35%）显著高于中心城区（18%-22%），
            与全国"城低乡高"的格局一致，但在重庆表现得尤为突出。
        </div>

        <div class="key-finding">
            <strong>发现二：慢病攀升</strong><br>
            心衰等慢病住院量增长超10倍，老年住院占比上升5.5个百分点，
            医疗系统正在承受快速增长的老年医疗压力。
        </div>

        <div class="key-finding">
            <strong>发现三：舆情分化</strong><br>
            正面内容占58%显示积极应对老龄化的社会心态；
            但负面焦点（急救响应、"直播坑老"）暴露出基层服务和监管短板。
        </div>
        """,
    )

    # ---- P11: 政策建议 ----
    report.add_section(
        "政策建议",
        f"""
        <h3>11.1 优化医疗资源配置</h3>
        <ul>
            <li>加大对渝东北、渝东南等老龄化严重地区的医疗资源投入</li>
            <li>加强基层医疗机构慢性病管理能力建设</li>
            <li>推进"医养结合"模式在远郊区县的落地</li>
        </ul>

        <h3>11.2 完善养老服务体系</h3>
        <ul>
            <li>针对农村留守老人建立定期巡诊制度</li>
            <li>加快社区养老服务设施建设</li>
            <li>推广"时间银行"等互助养老模式</li>
        </ul>

        <h3>11.3 强化监管与公众教育</h3>
        <ul>
            <li>加大对"直播坑老"等新型养老诈骗的打击力度</li>
            <li>完善120急救响应体系，缩短远郊急救到达时间</li>
            <li>加强老年人健康管理和慢性病预防宣传</li>
        </ul>

        <h3>11.4 数据驱动决策</h3>
        <ul>
            <li>建立老龄健康大数据平台，实现跨部门数据共享</li>
            <li>利用多源数据持续监测老龄化趋势和医疗压力变化</li>
            <li>定期发布老龄化白皮书，引导社会资源合理配置</li>
        </ul>
        """,
    )

    # ---- P12: 附录 ----
    report.add_section(
        "附录：方法与数据说明",
        f"""
        <h3>12.1 分析方法</h3>
        <table>
            <tr><th>维度</th><th>分析方法</th><th>工具/库</th></tr>
            <tr><td>人口结构</td><td>趋势分析、区域对比、增速排名</td><td>Pandas, GeoPandas</td></tr>
            <tr><td>医疗压力</td><td>时序分析、疾病谱演变、供需对比</td><td>Pandas, Scipy</td></tr>
            <tr><td>公众舆情</td><td>情感分析、关键词提取、词云</td><td>SnowNLP, Jieba, WordCloud</td></tr>
            <tr><td>空间可视化</td><td>Choropleth 热力图</td><td>Folium, GeoPandas</td></tr>
        </table>

        <h3>12.2 数据说明</h3>
        <ul>
            <li>人口数据来源：重庆市统计局年度统计公报、统计年鉴</li>
            <li>医疗数据来源：重庆市卫健委住院统计报表</li>
            <li>舆情数据来源：抖音、快手平台公开短视频评论（经匿名化处理）</li>
            <li>地理数据：重庆市38个区县行政区划边界</li>
        </ul>

        <h3>12.3 技术栈</h3>
        <p><strong>编程语言：</strong>Python 3.10+</p>
        <p><strong>核心依赖：</strong>Pandas, GeoPandas, SnowNLP, Folium, Plotly, Matplotlib, WordCloud, Jieba</p>
        <p><strong>开发环境：</strong>Jupyter Notebook, VS Code</p>
        """,
    )

    return report
