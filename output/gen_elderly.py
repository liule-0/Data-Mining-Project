# -*- coding: utf-8 -*-
"""Generate elderly care HTML page"""
import json, os

with open('output/elderly_care_data.json', 'r', encoding='utf-8') as f:
    records = json.load(f)

data_json = json.dumps(records, ensure_ascii=False)

inst_types = sorted(set(r['类型'] for r in records))
type_opts = '\n'.join(f'<option value="{t}">{t}</option>' for t in inst_types)
regions = ['中心城区', '主城新区', '渝东北', '渝东南']
region_opts = '\n'.join(f'<option value="{r}">{r}</option>' for r in regions)

with open('output/elderly_template.txt', 'r', encoding='utf-8') as f:
    template = f.read()

html = template.replace('__DATA__', data_json)
html = html.replace('__TYPE_OPTIONS__', type_opts)
html = html.replace('__REGION_OPTIONS__', region_opts)

outpath = 'output/养老机构数据查询系统.html'
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"OK {outpath} ({os.path.getsize(outpath)/1024:.0f}KB)")
