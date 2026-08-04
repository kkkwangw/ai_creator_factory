---
name: memory_monitor
description: 检查项目 Markdown 交接边界与 GPU 内存证据，不修改或轮换记忆文件。
---

# Memory Monitor

## 输入

控制文件大小、历史数量、当前任务引用、GPU 指标和保留策略。

## 工作流程

1. 区分 Markdown 交接、JSON 执行结果、媒体证据和 GPU 显存。
2. 检查 `CURRENT.md` 16 KiB、历史单份 16 KiB/最多20份、任务 32 KiB、TODO 8 KiB。
3. 检查控制 Markdown 是否粘贴日志、原始 API响应、长提示词或秘密。
4. 对 GPU 只报告释放、降级和停止建议，不执行删除或模型切换。
5. 把需要概括或轮换的建议交给本地主 Codex；Python和远程不得修改 Markdown。

## 输出

风险摘要、建议动作、证据路径和限制检查。不得自动删除、截断或重写任何记忆文件。
