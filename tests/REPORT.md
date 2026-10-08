# 实测记录 · 2026-10-08

环境：Windows Codex 捆绑 Python 3.12.14、pypdf 6.10.0、reportlab 4.4.9；Node 24.19.0；Playwright 驱动本地 Chromium 153.0.8010.12。测试材料：原创两页 sample.pdf，包含简化章节标题及三条显式 LaTeX 公式。

Python 集成/负例测试：11 项全部通过。覆盖 PDF 实际提取与指纹、章节/公式候选、正式门禁、缺页、伪造原文引用、树循环、教师补充误入严格树、章节顺序逆转、无 LaTeX 候选、缺少公式签署、坏 LaTeX、空页、HTML 转义和字体内嵌。

浏览器：offline=true，HTTP 请求数 0，pageErrors=[]。通过 KaTeX 渲染及内嵌字体加载、全部折叠/展开、圆点折叠、按钮/滚轮缩放、拖动、适应窗口、搜索、双模式、PDF 页码及原文展示、复习关系展示。已检查截图。

正式样例 validate --release --pdf：ok=true，三个公式均语法有效，semantic_verified=false。SHA256 身份检查通过。此测试不证明真实教材公式识别率或数学语义正确。

Skill Creator 的 quick_validate.py：通过。JSON Schema Draft 2020-12 元模式及草稿/复核样例：使用 jsonschema 4.26.0 通过校验。该编辑器形状 schema 与运行期门禁各自负责不同约束。

未测试：真实人教A版 PDF、扫描/OCR、多栏与复杂二维公式、几何图、整册大规模性能、所有 Edge/Chrome 版本、无障碍屏幕阅读器。包未安装到用户全局 Skill 目录；随包提供安装方法。

首次测试遇到 Windows 沙箱临时目录权限及 Playwright 默认浏览器版本路径不匹配，改用工作区测试目录和已有浏览器可执行路径后重测通过。这些不影响单文件课堂 HTML。
