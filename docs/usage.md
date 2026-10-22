# 使用说明 / Usage

## 命令

### 检查图纸

```bash
cadguard check drawing.dxf [--rules rules.yaml] [--out report.md]
                           [--format md|json] [--png preview.png]
```

- 不带 `--out` 时，报告直接打印到标准输出（默认 Markdown）。
- `--out` 后缀为 `.json` 时自动按 JSON 输出；`--format` 可强制指定。
- `--png` 额外渲染一张模型空间预览图（需要安装 `.[render]` 附加依赖，即 matplotlib）；渲染不可用时只打印提示，不影响检查结果与退出码。
- 标准输出会先打印一行汇总：总问题数与按严重度计数，随后是各规则计数。

### 演示

```bash
cadguard --demo [--dxf-out demo.dxf] [--out report.md] [--rules rules.yaml]
# 或 cadguard demo ...
```

生成内置样例 DXF（每条规则埋一个违规）并立即检查，退出码恒为 0。

## 退出码（check）

| 码 | 含义 |
| --- | --- |
| 0 | 无 error 级问题（可以有 warning/info） |
| 1 | 至少一个 error 级问题 |
| 2 | 图纸或规则文件无法读取/解析 |

可据此接入脚本或 CI，例如：`cadguard check drawing.dxf --out report.md || echo "有 error 级制图问题"`。

## 规则文件

YAML 或 JSON，结构为「规则段落 → 键值」，只需写要覆盖的部分：

```yaml
layers:
  enabled: true
  severity: error
  allowed: [OUTLINE, DIM, TEXT]
duplicate_geometry:
  precision: 4
```

段落与键的完整说明见 [rules.md](rules.md)，完整示例见 [../examples/rules.example.yaml](../examples/rules.example.yaml)。

## Python API

```python
import ezdxf
from cadguard import check_document, check_file, load_config, run_checks

# 整个文件
report = check_file("drawing.dxf", load_config("rules.yaml"))
print(report.to_json())

# 已加载的文档对象
doc = ezdxf.readfile("drawing.dxf")
issues = run_checks(doc, load_config())
for issue in issues:
    print(issue.rule_id, issue.handle, issue.location, issue.message)
```
