# Jason Alpha Daily V5 Template V1.0

固定 HTML/CSS 模板，数据与排版分离。

## 文件
- `template_v1.0.html.j2`：固定视觉模板
- `sample_data_v1.0.json`：标准数据示例
- `render_v1.0.py`：渲染脚本

## 使用
```bash
python render_v1.0.py --data sample_data_v1.0.json --html output.html --png output.png
```

页面尺寸固定为 1440×1880。后续每天只更新 JSON，不修改模板。
