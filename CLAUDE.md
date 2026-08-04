# AI Creator Factory Agent Entry

本文件是 Claude Code 的项目入口，但规则不属于 Claude 或任何单一平台。

开始工作前必须完整阅读并遵守 [AGENTS.md](AGENTS.md)，再按任务读取 `.ai/rules/` 和对应
Agent 说明。`AGENTS.md` 是唯一通用规则真源；本文件不复制一套可能漂移的专属规则。

核心约束：本地主 Agent 是唯一控制类 Markdown 写入者；所有外部能力通过项目级 Skill、
插件或基础设施适配器接入；远程执行器无 LLM 权限，只读任务并写独立结果。
