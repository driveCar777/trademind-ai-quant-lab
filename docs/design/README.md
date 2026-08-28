# docs/design

给 Stitch 用的设计源文件。

## DESIGN.md

Stitch 设计系统的输入文件，**文件名必须保持 `DESIGN.md`**（网页端上传时 Stitch 认这个名字）。

带 YAML front-matter。这一点是关键：项目里原先那份 DESIGN.md 只有散文，Stitch 会忽略正文里写的色值，改用项目标题「炒股」派生出的酒红色盘（`#310008`）。只有 front-matter 里的 `colors:` 才是机器可读的 token。

落地色盘：

| 用途 | 色值 |
|------|------|
| 页面底 | `#070b12` |
| 卡片 | `#111827` |
| 边框 | `#243044` |
| 正文 | `#e2e8f0` |
| 次要文字 | `#94a3b8` |
| 主按钮蓝 | `#3b82f6` |
| AI 紫 | `#7c5cfc` |
| 在线绿 | `#10b981` |
| 离线/错误徽章 | `#f43f5e` |

## 已知限制

`upload_design_md` 能通过 MCP 上传成功，但 `create_design_system_from_design_md` 对本项目（`TEXT_TO_UI_PRO`）只返回空，API 里看不到新的设计系统。要让色盘真正生效，需要在 Stitch 网页端手动上传这份 DESIGN.md 并应用设计系统。
