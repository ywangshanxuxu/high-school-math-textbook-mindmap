# high-school-math-textbook-mindmap

为 Windows Codex 高中数学教师准备的可运行 Skill 项目。面向人教A版的工作方式；未使用或验证真实人教A版 PDF。样例是原创两页简化材料，不是教材完整知识导图。

## 立即使用

直接双击 `examples/sample.offline.html`（Edge/Chrome）。此单文件已嵌入 D3、Markmap、KaTeX 和全部 KaTeX 字体，不依赖同目录文件或网络。选择双模式，点击节点文字查看出处；圆点折叠/展开，滚轮缩放，拖动空白区域移动。工具栏可全部展开、折叠、适应窗口、搜索；搜索当前模式并展开匹配内容，右侧可选结果。跨章连接在右侧列为关系，不绘制图边。

## 安装到 Codex

解压后，将完整 `high-school-math-textbook-mindmap` 文件夹复制到 `$env:USERPROFILE\.codex\skills\`。已有同名目录先备份，不要覆盖个人修改。重启/重新加载 Codex 后通过 `$high-school-math-textbook-mindmap` 调用。也可先直接让 Codex 读取本文件夹 SKILL.md。本交付未修改你的全局 Skill 目录。

## Windows 命令

在本项目目录打开 PowerShell。Python 3.10+、Node 18+；包内 vendor 已备齐，正常构建无需 npm install。

```powershell
python -m venv .venv
$py = '.\.venv\Scripts\python.exe'
& $py -m pip install -r requirements.txt
& $py scripts/mindmap.py extract 'D:\教材\数学选章.pdf' --config examples/config.json --out work/book.draft.json
& $py scripts/mindmap.py validate work/book.draft.json --pdf 'D:\教材\数学选章.pdf'
& $py scripts/mindmap.py build work/book.draft.json --out work/book.draft.html
```

先修改 config 的 title、edition、publisher 和书页偏移。安装 Python 包需要网络；若要离线首次安装，在另一台同平台同 Python 版本电脑准备 wheelhouse，然后 `pip install --no-index --find-links wheelhouse -r requirements.txt`。此包未携带 Python/Node 运行时或 wheels；生成的 HTML 本身无需这些运行时。

按 references/review.md 在 JSON 中逐条核对并签署。示例的 approved 仅适用原创夹具，不得复制到真实教材。

```powershell
& $py scripts/mindmap.py validate work/book.reviewed.json --release --pdf 'D:\教材\数学选章.pdf' > work/validation.json
if ($LASTEXITCODE -ne 0) { throw '校验未通过，保留草稿' }
& $py scripts/mindmap.py build work/book.reviewed.json --release --out work/book.offline.html
```

如果 Node 不在 PATH，追加 `--node 'C:\完整路径\node.exe'`。Codex 可通过 load_workspace_dependencies 获取其捆绑运行时，不要在脚本中固定某台电脑路径。pypdf、reportlab 版本固定在 requirements.txt；后者仅再生 PDF 夹具时需要。

## 测试和再生样例

```powershell
& $py scripts/make_sample.py
& $py -m unittest discover -s tests -v
& $py scripts/mindmap.py build examples/sample.reviewed.json --release --out examples/sample.offline.html
```

测试覆盖提取、页码/指纹、待复核门禁、损坏来源、树循环/順序、坏公式、恶意标签转义和字体嵌入。浏览器测试另需 Node 的 playwright 包和 Chromium（开发依赖，不用于课堂）。若已安装，可执行 `node tests/browser.cjs examples/sample.offline.html`；测试报告说明哪些环境实测。

`scripts/vendor.py` 是显式联网维护脚本，下载固定版本及许可证、所有字体并写 SHA256 manifest；不要在正常生成流程执行它。更新依赖后重新测试和审查许可证。离线 build 验证 vendor 指纹，HTML 还设置 connect-src 'none'。不包含统计、CDN 回退或外部 PDF 链接。

## 边界

这是一条“文本层 PDF → 启发式草稿 → 人工结构/公式复核 → KaTeX 语法检查 → 离线导出”流水线。不是 OCR/复杂公式识别引擎。公式漏检、标题误分级、阅读顺序、图表及数学语义需人工审核。正式门禁检查审核声明，无法证明声明真实。大教材将包含全文且 HTML 较大，建议先选章。页码溯源显示 PDF 页、书页、提取行和原文，不嵌入 PDF 图像，也不自动打开原文件。

实现参考：[Markmap API](https://markmap.js.org/api/classes/markmap-view.Markmap.html)、[KaTeX 选项](https://katex.org/docs/options.html)、[pypdf 提取限制](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)。项目代码采用 MIT，第三方许可证保留于 assets/vendor。
