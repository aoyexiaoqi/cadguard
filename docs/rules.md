# 规则参考 / Rules reference

每条规则对应配置文件中的一个段落。所有段落都支持：

| 键 | 说明 |
| --- | --- |
| `enabled` | `true` / `false`，关闭后该规则不产生任何问题 |
| `severity` | `error` / `warning` / `info`；`check` 命令在存在 error 级问题时退出码为 1 |

未在用户文件中出现的段落/键使用内置默认值（见 `src/cadguard/config.py` 的 `DEFAULT_CONFIG`）。

## layer.nonstandard — 图层检查

- 段落：`layers`
- 检查对象：模型空间全部实体的 `layer` 属性
- 判定：`allowed`（白名单，不区分大小写）非空时，实体图层不在白名单内即报错；若同时配置了 `pattern` 且图层名不匹配正则，说明中会附加提示。`allowed` 为空时只按 `pattern` 判定。
- 默认：白名单 `0, OUTLINE, CENTER, CENTERLINE, HIDDEN, DIM, TEXT, TITLE, FRAME, BORDER, HATCH`；正则 `^[A-Za-z0-9_\-]+$`；严重度 error。

## text_style.nonstandard_font — 文字样式/字体检查

- 段落：`text_styles`
- 检查对象：图纸的文字样式表（STYLE），取其字体文件名（只比对 basename，不区分大小写，路径会被剥离，如 `C:\fonts\simhei.ttf` 按 `simhei.ttf` 计）
- 判定：字体不在 `allowed_fonts` 内即报错。字体为空的样式跳过。
- 默认允许：`txt, txt.shx, romans.shx, simplex.shx, isocp.shx, gbenor.shx, gbeitc.shx, simhei.ttf, simsun.ttc, simfang.ttf, arial.ttf`；严重度 warning。
- 说明：这是样式定义级检查，不定位到具体文字实体，故问题无坐标。

## linetype.nonstandard — 线型检查

- 段落：`linetypes`
- 检查三处：① 线型表里加载的线型定义；② 图层的线型指定；③ 实体自身的线型指定。`ByLayer` / `ByBlock` / `Continuous` 永远允许。
- 判定：名称（不区分大小写）不在 `allowed` 内即报错。
- 默认允许：`CENTER, CENTER2, CENTERX2, HIDDEN, HIDDEN2, HIDDENX2, DASHED, DASHDOT, DOT, PHANTOM, BORDER`；严重度 warning。
- 注意：仅被加载、并未被任何实体使用的非标准线型定义也会被报告（属图纸卫生问题）。若不需要，在 `allowed` 中补齐即可。

## dimension.text_override — 尺寸文本覆盖检查

- 段落：`dimension_text_override`（无额外键）
- 检查对象：模型空间的 DIMENSION 实体
- 判定：尺寸文本字段为空或恰为 `<>` 时显示的是测量值，不报告；其余一律报告：
  - 不含 `<>`（如 `999`）：人工覆盖，说明中附带实测值；
  - 含 `<>` 但带前后缀（如 `<> mm`）：格式化覆盖，同样报告，由人工裁定是否合理。
- 默认严重度：error。

## geometry.duplicate — 重复几何检查

- 段落：`duplicate_geometry`
- 额外键：`precision`（坐标取整的小数位，默认 6）
- 判定：同类型实体的几何签名完全一致即判定重复；每多一份副本报告一条，说明中注明原件的 handle。签名构成：
  - LINE：起终点（无序，方向相反也算重复）
  - CIRCLE：圆心 + 半径；ARC：圆心 + 半径 + 起止角
  - POINT：位置；LWPOLYLINE / POLYLINE：顶点序列 + 闭合标志
  - INSERT：图块名 + 插入点 + 旋转 + 缩放
  - TEXT / MTEXT：插入点 + 文本内容
- 不在上述类型内的实体不参与该规则。默认严重度：warning。

## title_block.missing — 标题栏检查

- 段落：`title_block`
- 额外键：`block_names`（标题栏图块名，不区分大小写）、`text_markers`（标题栏文本标记，子串匹配）
- 判定：任一布局（模型/图纸空间）中存在名称命中的 INSERT，或有 TEXT/MTEXT 包含任一标记，则认为标题栏存在；都没有则报告一条（整图一条，无坐标）。
- 默认：图块名 `TITLE_BLOCK, TITLEBLOCK, TITLE, GB_TITLE, A3_TITLE`；标记 `图号, DWG NO, DWG.NO, 图名`；严重度 error。
