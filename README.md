# Tsinghua Course Skills

为清华课程作业写的可复用 [Claude Code](https://claude.com/claude-code) / Codex skills 集合。希望让重复性的作业(实验报告、习题模板、格式校对…)少花点时间。

> 仓库由清华本科生维护,与清华大学官方无关。所有 skill 仅作参考,**请独立完成自己的作业**。

## 仓库结构

```
tsinghua-course-skills/
├── claude/
│   └── write-biochem-lab-report/    # 装到 ~/.claude/skills/
└── codex/
    └── write-biochem-lab-report/    # 装到 ~/.codex/skills/
```

`claude/` 和 `codex/` 下的 skill 内容基本一致,差别只在 `SKILL.md` 里的安装路径示例(分别指向 `.claude` 和 `.codex`)。挑你用的工具对应那一份装就行。

## 已有 skill

| Skill | 用途 |
|---|---|
| **`write-biochem-lab-report`** | 生化基础实验报告生成器:ElegantPaper LaTeX 模板、三线表、出版风格 matplotlib 标准曲线、整理过的 TA 反馈 checklist。覆盖 ELISA / WB / pull-down / GF / BCA / UV 等实验。 |
| **`yuketang-replay-downloader`** | 雨课堂 / Yuketang 授权回放下载与审计工具:从已登录课程页抓取回放 MP4 链接、下载多分段回放、处理同名课堂、检查旧 manifest 是否漏段。 |

## 安装

### Claude Code

```powershell
# Windows PowerShell
$dest = "$env:USERPROFILE\.claude\skills"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item -Recurse claude\write-biochem-lab-report $dest\
Copy-Item -Recurse claude\yuketang-replay-downloader $dest\
```

```bash
# macOS / Linux
mkdir -p ~/.claude/skills
cp -r claude/write-biochem-lab-report ~/.claude/skills/
cp -r claude/yuketang-replay-downloader ~/.claude/skills/
```

### Codex

```powershell
# Windows PowerShell
$dest = "$env:USERPROFILE\.codex\skills"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item -Recurse codex\write-biochem-lab-report $dest\
Copy-Item -Recurse codex\yuketang-replay-downloader $dest\
```

```bash
# macOS / Linux
mkdir -p ~/.codex/skills
cp -r codex/write-biochem-lab-report ~/.codex/skills/
cp -r codex/yuketang-replay-downloader ~/.codex/skills/
```

安装后 Claude Code / Codex 会自动发现这个 skill。

## 用法

每个 skill 的 `SKILL.md` 是入口。装好后直接用自然语言提需求即可,比如:

> 帮我写一份 ELISA 实验报告,数据在 `data/elisa.csv`

> 用 BCA 法的吸光度数据帮我画一张标准曲线,推出未知样品浓度

> 帮我把这门雨课堂课程的授权回放全部下载下来,并检查有没有漏掉多分段视频

工具会自动读 skill 里的 workflow / format checklist / 模板,然后开始写。

## 依赖

- Python 3.10+(`matplotlib`、`numpy`、`pandas`、`Pillow` 用于绘图与图像脚本;`playwright` 用于雨课堂课程页自动化)
- Chrome / Chromium 与 `curl.exe`(用于雨课堂授权回放抓取与下载)
- LaTeX with XeLaTeX + `latexmk`(Windows 上 MiKTeX 够用,Linux/Mac 上 TeX Live 够用)
- `poppler` 工具集(可选,用 `pdftotext` 验证编译结果)

## 学术诚信

这些 skill 是模板和工具,不是替你写报告的服务:

- 自己的实验数据要自己分析、写结果与讨论。
- 不要复制同学的图、表、文字;非原创的图要在 caption 里注明来源。
- `format_checklist.md` 里整理的格式规范来自真实的 TA 反馈,目的是帮你避开常见格式扣分点,不是绕过写作过程。

请把 skill 当作合规的辅助工具使用,自己对最终交上去的作业负责。

## 贡献新 skill

欢迎 PR。新增 skill 请按以下结构放在 `claude/` 和 `codex/` 下:

```
claude/<skill-name>/
├── SKILL.md          # 入口,带 YAML frontmatter
├── assets/           # 模板、class 文件、样式
├── references/       # checklist / 评分细则
└── scripts/          # 辅助脚本(plot、检查、project 生成)
```

`codex/<skill-name>/` 镜像 `claude/<skill-name>/`,只把 SKILL.md 里的安装路径示例从 `.claude` 改成 `.codex`。

请不要提交个人课程 ID、签名回放 URL、cookies、浏览器 profile、下载 manifest、视频文件或本机绝对路径。

## License

[MIT](LICENSE)
