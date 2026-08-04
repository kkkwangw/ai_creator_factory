# AI Creator Factory

AI Creator Factory 是个人使用的 AI 创作模板。第一版聚焦一个可审计的垂直流程：

```text
一本书 -> 一个实际项目目录 -> 一条 45--60 秒竖屏书单视频
```

模板不是 SaaS，也不绑定 OpenAI、Claude、ComfyUI 或任何单一模型。外部能力只能通过项目级
Skill、插件或基础设施适配器进入；当前候选模型必须完成真实租赁 GPU 基准后才能进入批准清单。

## 第一版范围

- 书籍资料：本地腾讯微信读书 Skill，书名必填。
- 文案与分镜：本地 Codex，默认 20--40 岁中文短视频受众。
- 语音：本地 MiMo V2.5 TTS，固定“冰糖”音色，WAV 为主时间轴。
- 图片候选：FLUX.2 Klein 4B Base FP8。
- 图生视频候选：Wan2.2-TI2V-5B，704x1280、24fps、121 帧。
- 口型候选：MuseTalk 1.5，独立远程 UV 插件环境。
- 合成：远程 FFmpeg，固定 `book-list-v1`、ASS 字幕、H.264/AAC。
- 交付：成片、1080x1920 封面、发布文案和证据清单；不自动发布平台。

候选模型目前均为 `candidate`。没有真实 24GB 实例基准时，本模板不能声称已经具备生产视频
能力；准入标准见 [open-video-model-stack.md](docs/research/open-video-model-stack.md)。

## 本地与远程

本地运行 Codex、微信读书、MiMo、Whisper、部署工具和控制类 Markdown。远程运行预装
ComfyUI、候选开源模型、MuseTalk、FFmpeg 和确定性 Runner。Codex 不在远程安装或运行。

本地脚本只使用现有 Conda `codex`（Python 3.11.x）：

```bash
conda run -n codex python scripts/validate_project.py
conda run -n codex python -m pytest
conda run -n codex ruff check .
```

禁止使用系统 Python 3.9 或向其安装包。SSH/SFTP 功能需要时，只能在 Conda `codex`
环境安装可选依赖：

```bash
conda run -n codex python -m pip install -e '.[ssh]'
```

不要在尚未需要 SSH 时安装它，也不要在模板初始化阶段安装模型或重量级生成依赖。

## 创建实际项目

1. 复制整个模板目录到新目录，不复制 `.git/`。
2. 由本地 Codex 初始化 `PROJECT.md`、`TODO.md`、`memory/CURRENT.md` 和第一个任务。
3. 在 `.local/tools.toml` 填写本机工具路径，在本地 `.env` 填写必要凭据。
4. 从上一实际项目显式复制已批准角色包；不使用项目外全局角色库。
5. 项目开始生产后锁定 `template_version`。升级时只生成差异清单，人工选择文件。

实际项目不要求 Git。本地和远程目录结构相同，但模型、缓存、运行产物和机器配置不自动同步。

## 控制文件

- `PROJECT.md`：稳定项目事实与锁定模板版本。
- `TODO.md`：简短当前任务索引。
- `tasks/<task-id>.md`：准备做什么，由本地 Codex维护。
- `memory/CURRENT.md`：有上限的当前交接快照；历史最多 20 份。
- `config/`：机器无关生产策略、候选模型和固定模板。
- `deployments/`：显式部署清单与回执，不允许递归上传。
- `runs/`：远程任务 JSON、日志、证据和暂存产物。
- `deliverables/current/`：原子激活的当前有效交付物。

## 当前可运行工具

- `scripts/validate_project.py`：检查控制文件大小、项目身份与基础配置。
- `scripts/build_task_envelope.py`：从 TOML frontmatter 任务 Markdown 生成不可变 JSON envelope。
- `scripts/build_deployment_manifest.py`：从显式文件计划生成带 SHA-256 的部署清单。
- `scripts/verify_delivery.py`：核对当前交付文件、哈希与 ffprobe 技术规格；当前不会越权推导
  `ready_for_download`，该状态要等远程 Runner和 Gate 1--6重验器实现后才能产生。
- `scripts/doctor.py`：只读检查 Python、FFmpeg、Whisper、UV 和 GPU 环境。
- `scripts/transfer.py`：通过可选 Paramiko 执行清单限定的 SSH/SFTP 传输。

上传计划示例见 `deployments/plan.example.json`，下载规格示例见
`deployments/download.example.json`。两者都只接受逐文件条目，不扫描或递归传输目录。

远程 ComfyUI/MuseTalk 生产适配器仍需在第一台租赁实例上完成基准和锁定；脚本不会用占位结果
假装生成成功。
