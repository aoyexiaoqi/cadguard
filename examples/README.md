# 示例 / Examples

## rules.example.yaml

一份带注释的规则配置示例，演示如何覆盖白名单、字体表、线型表与标题栏判定。用法：

```bash
cadguard check drawing.dxf --rules examples/rules.example.yaml --out report.md
```

## 演示图纸与预期结果（cadguard --demo）

`cadguard --demo` 用 ezdxf 程序化生成 `cadguard_demo.dxf`，图里只有少量干净几何，其余都是故意埋的违规，一条规则一个：

| 埋点 | 图中实体 | 预期规则 | 预期条数 |
| --- | --- | --- | --- |
| 直线放在 `SCRATCH` 图层 | LINE @ y=50 | `layer.nonstandard` (error) | 1 |
| 样式 `FANCY` 用 `papyrus.ttf` | STYLE 表定义 | `text_style.nonstandard_font` (warning) | 1 |
| 自定义线型 `MYLINE` | LTYPE 定义 + 一条使用它的 LINE @ y=60 | `linetype.nonstandard` (warning) | 2 |
| 尺寸文本改成 `999`（实测 50） | DIMENSION | `dimension.text_override` (error) | 1 |
| 两条完全重合的直线 | LINE @ y=70 ×2 | `geometry.duplicate` (warning) | 1 |
| 全图没有标题栏 | — | `title_block.missing` (error) | 1 |

预期汇总：**7 条问题，error 3 / warning 4**。干净几何（`OUTLINE` 层上的矩形边线与圆、正常尺寸）不产生任何问题 — 测试套件中的 `tests/test_rules.py::test_clean_drawing_has_no_issues` 用一张完整的干净图纸（带标题栏）验证了六条规则全部静默。
