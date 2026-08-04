# 项目结构说明

本文记录模板 `0.2.0` 的源码与控制文件。`.git/`、Python缓存、测试缓存、密钥、模型、媒体
产物和运行期目录内容不进入模板文件清单。

## 完整目录树

```text
ai_creator_factory/
├── .agents/
│   └── skills/
│       └── weread-skills/
│           ├── LICENSE
│           ├── SKILL.md
│           ├── SOURCE.json
│           ├── UPSTREAM_SKILL.md
│           ├── book.md
│           ├── discover.md
│           ├── notes.md
│           ├── profile.md
│           ├── readdata.md
│           ├── review.md
│           ├── search.md
│           └── shelf.md
├── .ai/
│   ├── agents/
│   │   ├── architect.md
│   │   ├── coder.md
│   │   ├── critic.md
│   │   ├── designer.md
│   │   ├── director.md
│   │   ├── generalist.md
│   │   ├── gpu-engineer.md
│   │   ├── planner.md
│   │   ├── researcher.md
│   │   ├── reviewer.md
│   │   ├── workflow-engineer.md
│   │   └── writer.md
│   ├── commands/
│   │   ├── generate.md
│   │   ├── optimize.md
│   │   └── review.md
│   ├── rules/
│   │   ├── architecture.md
│   │   ├── coding.md
│   │   ├── content.md
│   │   ├── gpu.md
│   │   └── security.md
│   ├── skills/
│   │   ├── memory_monitor/
│   │   │   └── SKILL.md
│   │   ├── prompt_optimizer/
│   │   │   └── SKILL.md
│   │   ├── quality_check/
│   │   │   └── SKILL.md
│   │   └── workflow_optimizer/
│   │       └── SKILL.md
│   └── settings.json
├── .local/
│   ├── project-marker.example.json
│   └── tools.example.toml
├── config/
│   ├── fonts/
│   │   └── fonts.json
│   ├── models/
│   │   ├── candidates.json
│   │   └── source-policy.json
│   ├── music/
│   │   └── library.json
│   ├── providers/
│   │   ├── mimo.json
│   │   └── weread.json
│   ├── templates/
│   │   └── book-list-v1.json
│   ├── character-profile.json
│   ├── content-profile.json
│   ├── retention-policy.json
│   └── runtime-policy.json
├── data/
│   ├── characters/
│   │   ├── .gitkeep
│   │   └── current/
│   │       └── README.md
│   ├── knowledge/
│   │   └── .gitkeep
│   ├── prompts/
│   │   └── .gitkeep
│   ├── references/
│   │   ├── .gitkeep
│   │   └── video/
│   │       └── README.md
│   └── worlds/
│       └── .gitkeep
├── deployments/
│   ├── download.example.json
│   └── plan.example.json
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DECISIONS.md
│   ├── PROJECT_STRUCTURE.md
│   ├── REMOTE_RUNBOOK.md
│   ├── WORKFLOW.md
│   └── research/
│       ├── book-video-weread.md
│       ├── open-music-sources.md
│       └── open-video-model-stack.md
├── experiments/
│   └── .gitkeep
├── memory/
│   ├── CURRENT.md
│   └── history/
│       └── .gitkeep
├── models/
│   └── README.md
├── outputs/
│   └── .gitkeep
├── plugins/
│   ├── audio/
│   │   ├── .gitkeep
│   │   └── mimo/
│   │       └── plugin.json
│   ├── image/
│   │   ├── .gitkeep
│   │   └── comfyui/
│   │       └── plugin.json
│   ├── llm/
│   │   └── .gitkeep
│   ├── storage/
│   │   └── .gitkeep
│   └── video/
│       ├── .gitkeep
│       ├── musetalk/
│       │   └── plugin.json
│       └── wan/
│           └── plugin.json
├── schemas/
│   ├── delivery-manifest.example.json
│   ├── deployment-manifest.schema.json
│   ├── project-marker.schema.json
│   └── task-envelope.schema.json
├── scripts/
│   ├── _bootstrap.py
│   ├── build_deployment_manifest.py
│   ├── build_task_envelope.py
│   ├── doctor.py
│   ├── transfer.py
│   ├── validate_project.py
│   └── verify_delivery.py
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── executor.py
│   │   └── registry.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── event_bus.py
│   │   ├── plugin_manager.py
│   │   └── runtime.py
│   ├── deployment/
│   │   ├── __init__.py
│   │   ├── manifest.py
│   │   └── ssh.py
│   ├── media/
│   │   ├── __init__.py
│   │   └── delivery.py
│   ├── memory/
│   │   └── README.md
│   ├── prompt/
│   │   ├── __init__.py
│   │   ├── builder.py
│   │   └── templates.py
│   ├── remote/
│   │   ├── __init__.py
│   │   └── process.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── frontmatter.py
│   │   ├── hashing.py
│   │   └── paths.py
│   └── workflow/
│       ├── __init__.py
│       ├── engine.py
│       ├── scheduler.py
│       └── task.py
├── tasks/
│   ├── README.md
│   └── example-task.md
├── tests/
│   ├── test_contracts.py
│   ├── test_delivery.py
│   ├── test_deployment_manifest.py
│   ├── test_frontmatter.py
│   ├── test_paths.py
│   ├── test_ssh_contracts.py
│   └── test_workflow_contracts.py
├── workflows/
│   ├── image/
│   │   └── .gitkeep
│   ├── novel/
│   │   └── .gitkeep
│   └── video/
│       ├── .gitkeep
│       └── book-list-v1/
│           ├── README.md
│           └── gates.json
├── .env.example
├── .gitignore
├── AGENTS.md
├── CLAUDE.md
├── PROJECT.md
├── README.md
├── TODO.md
├── pyproject.toml
└── template.json
```

运行时按需创建 `runs/`、`deliverables/current/`、`cache/` 和 `deployments/DEP-*/`；这些目录
不代表模板源文件，也不由 Git 或递归同步管理。

## 已创建文件分组

- Agent入口：`AGENTS.md`、`CLAUDE.md`、`.ai/` 下的12个角色、5组规则、4个技能和3个命令。
- 项目控制：`PROJECT.md`、`TODO.md`、`memory/CURRENT.md`、`tasks/` 和 `template.json`。
- 生产策略：`config/` 中的视频规格、角色、内容、模型、音乐、字体、保留和运行策略。
- 外部能力：项目内固定微信读书 Skill，以及 MiMo、ComfyUI、Wan、MuseTalk插件清单。
- 传输执行：部署清单、SFTP、远程进程、交付验真模块及7个命令行脚本。
- 证据与研究：工作流 Gate定义、远程手册、架构决策和三份研究报告。
- 契约验证：4个 JSON schema/示例和7个测试模块。

## 核心文件用途

| 文件 | 用途 |
| --- | --- |
| `AGENTS.md` | 所有本地 Codex/Agent共用的项目边界、协作、安全和修改流程。 |
| `CLAUDE.md` | Claude Code兼容入口，复用同一套非供应商专属规则。 |
| `PROJECT.md` | 一本书对应的稳定项目身份；生产开始后锁定模板版本。 |
| `TODO.md` | 有大小上限的当前任务索引，不保存执行证据。 |
| `memory/CURRENT.md` | 下次本地 Codex启动时读取的有界交接快照；历史最多20份。 |
| `tasks/*.md` | 仅描述准备做什么，只允许本地 Codex修改。 |
| `config/runtime-policy.json` | 重试、超时、Markdown上限、上传预算和安全硬限制。 |
| `config/templates/book-list-v1.json` | 10片段、9:16、24fps、字幕和确定性合成规格。 |
| `workflows/video/book-list-v1/gates.json` | Gate 1--6的输入、证据和失效依赖。 |
| `src/workflow/task.py` | 精确任务身份、最多3次重试和 Gate N--6失效规则。 |
| `src/deployment/manifest.py` | 显式非递归部署清单、大小限制、哈希和秘密路径过滤。 |
| `src/deployment/ssh.py` | 密码SSH、TOFU、项目marker、逐文件SFTP上传下载和冲突检测。 |
| `src/remote/process.py` | SSH断开后继续的进程记录，以及精确ID取消协议。 |
| `src/media/delivery.py` | 验证当前交付文件哈希和部分 ffprobe技术规格，不越权判定全部 Gate。 |
| `scripts/doctor.py` | 只读发现本机或远程工具，不安装、不修复环境。 |
| `.agents/skills/weread-skills/SOURCE.json` | 固定微信读书来源commit、版本、许可证和逐文件哈希。 |

## 下一步开发建议

1. 租用第一台24GB预装 ComfyUI实例，确认持久化根并运行只读环境探测。
2. 为三个候选模型建立真实10镜头基准；只有证据达标后才改为 `approved`。
3. 实现最薄的确定性远程 Runner：只读 envelope，逐 Gate写独立 JSON结果和证据。
4. 接入本地微信读书五接口与 MiMo语音，完成脱敏、音频时长和 Whisper验真。
5. 固定 ComfyUI工作流 JSON、MuseTalk调用、ASS模板和 FFmpeg命令后再跑完整样片。
6. 用成片缺陷演练 Gate回溯：从真实产物定位最早错误，并强制失效该 Gate到 Gate 6。

当前模板已具备可验证的控制面和传输骨架，但尚未在真实 GPU、微信读书、MiMo或 SSH服务器
上完成端到端生产验证，因此不能宣称已经能稳定产出成片。
