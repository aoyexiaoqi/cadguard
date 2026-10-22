# CADGuard

机械 CAD 图纸（DXF）自动检查工具：用可配置的规则引擎检查图层、文字样式/字体、线型、尺寸文本覆盖、重复几何与标题栏，输出带实体定位的 Markdown / JSON 报告。

Rule-based checker for DXF engineering drawings — layers, text styles/fonts, linetypes, dimension text overrides, duplicate geometry and title-block presence — with Markdown / JSON reports that locate every finding.

> 定位：出图前自查工具，帮工程师在评审/归档前批量发现制图规范问题。**它不做图纸审批，也不替代人工审图。**
> Positioning: a pre-release self-check for engineers. It does **not** approve drawings or replace human review.

## 功能 / Features

| 规则 Rule ID | 检查内容 | 默认严重度 |
| --- | --- | --- |
| `layer.nonstandard` | 实体落在非标准图层上（白名单 + 命名正则） | error |
| `text_style.nonstandard_font` | 文字样式使用非标准字体 | warning |
| `linetype.nonstandard` | 非标准线型（定义加载、图层指定、实体指定三处都查） | warning |
| `dimension.text_override` | 尺寸显示文本被人工覆盖，而非测量值（含 `<>` 加后缀的格式化覆盖） | error |
| `geometry.duplicate` | 完全相同的重复几何（类型 + 几何签名一致） | warning |
| `title_block.missing` | 标题栏缺失（按图块名或文本标记判定） | error |

每个问题都报告：规则 ID、严重度、实体 handle、实体类型、位置坐标（图形实体）与说明。报告含按规则/严重度的汇总计数。

Every finding reports rule id, severity, entity handle, entity type, location coordinates (for graphical entities) and a message. Reports include summary counts by rule and severity.

## 安装 / Installation

需要 Python ≥ 3.9，完全离线运行（依赖只有 ezdxf 与 PyYAML）。

```bash
pip install -e .
# 可选：PNG 预览渲染 / optional PNG preview rendering
pip install -e ".[render]"
```

## 快速开始 / Quick start

```bash
# 检查一张图纸，生成 Markdown 报告（退出码：有 error 级问题为 1）
cadguard check drawing.dxf --out report.md

# JSON 报告
cadguard check drawing.dxf --format json --out report.json

# 自定义规则（只写需要覆盖的段落，其余用内置默认）
cadguard check drawing.dxf --rules rules.yaml --out report.md

# 演示：生成一张埋了 6 类违规的样例 DXF 并立即检查
cadguard --demo
```

`--demo` 会生成 `cadguard_demo.dxf` 并输出 `cadguard_demo_report.md`：样例图里埋了非标准图层上的直线、`papyrus.ttf` 字体样式、自定义线型 `MYLINE`、被改成 `999` 的尺寸文本、一对重复直线，并且故意不放标题栏 — 六条规则各命中一次（线型命中两条：定义 + 使用）。样例与预期结果的对照见 [examples/README.md](examples/README.md)。

## 规则配置 / Configuration

规则全部可配：每条规则可开关、改严重度；白名单、字体表、线型表、标题栏判定都可改。示例见 [examples/rules.example.yaml](examples/rules.example.yaml)，完整说明见 [docs/rules.md](docs/rules.md)，命令行与退出码见 [docs/usage.md](docs/usage.md)。

```yaml
layers:
  severity: error
  allowed: [OUTLINE, DIM, TEXT, TITLE]   # 图层白名单（不区分大小写）
text_styles:
  allowed_fonts: [simhei.ttf, gbeitc.shx]
title_block:
  block_names: [TITLE_BLOCK]
  text_markers: ["图号"]
```

## 作为库使用 / Library use

```python
from cadguard import check_file, load_config

report = check_file("drawing.dxf", load_config("rules.yaml"))
print(report.total, report.count_by_rule())
print(report.to_markdown())
```

## 局限 / Limitations（请先读）

- **只支持 DXF**。不解析 DWG，不解析 NX 原生文件（.prt）；NX 图纸请先导出 DXF。
- V1 只检查模型空间的实体（标题栏规则同时查所有布局）；图块定义内部的实体不逐个检查。
- 重复几何按「类型 + 几何签名」精确匹配（坐标按可配精度取整），只覆盖 LINE / CIRCLE / ARC / POINT / LWPOLYLINE / POLYLINE / INSERT / TEXT / MTEXT；近似重合（差 0.001 的两条线）默认不算重复。
- 尺寸覆盖判定基于 DXF 的尺寸文本字段：空或 `<>` 视为测量值，其余（包括 `<>` 加前后缀）都会报告 — 「合理加后缀」与「造假改数」由人工在报告基础上裁定。
- 线型规则会报告仅被加载但未使用的非标准线型定义；如只关心实际使用，请在配置中放宽 `allowed` 列表。
- PNG 渲染只是预览（ezdxf drawing 插件 + matplotlib），渲染结果不参与任何判定。

## 开发 / Development

```bash
pip install -e ".[test]"
pytest --cov=cadguard
```

## License

MIT
