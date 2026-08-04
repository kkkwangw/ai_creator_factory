# 架构规则

- 第一版唯一可执行项目类型是 `book_video`；未来能力只能通过版本化扩展加入。
- 核心层只依赖 Python 标准库和稳定协议，不导入模型、AI 平台或 SSH 厂商 SDK。
- 本地控制面负责 Markdown、创作决策、微信读书、MiMo 和部署；远程数据面只执行确定性任务。
- 工作流按能力名称选择插件，不按供应商名称在核心逻辑中分支。
- 任务 Markdown 是人类计划真源；不可变 JSON envelope 是远程执行输入。
- 状态只用于观察，真实文件、哈希、媒体探测和依赖链才是恢复证据。
- 跨边界结构必须带 `schema_version`，可 JSON 序列化并拒绝未知危险路径。
- 一个活动 Run、一个 GPU 任务；不引入消息队列、服务端 LLM 或分布式调度。
- Python 不管理 Markdown 记忆。`PROJECT.md`、`TODO.md`、`tasks/` 和 `memory/` 只由本地主
  Codex维护。
