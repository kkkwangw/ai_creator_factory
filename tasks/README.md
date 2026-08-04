# Tasks

`tasks/<task-id>.md` 描述准备做什么，只能由本地主 Codex修改。文件使用 TOML frontmatter
（`+++`）声明稳定字段；自由文本只补充目标、限制和验收，不保存执行日志。

提交前运行 `scripts/build_task_envelope.py` 生成不可变 JSON。远程执行器不得从自由文本猜测
关键参数，也不得修改任务 Markdown。

本地主 Codex创建或切换任务时，同步更新 `TODO.md` frontmatter 中的 `current_task_id` 和
`current_run_id`。这些字段只帮助下次启动定位证据，不代表任务或 Gate已经完成。
