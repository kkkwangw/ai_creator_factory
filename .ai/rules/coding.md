# 编码规则

- 自动化统一使用 Python 3.11.x；本地命令通过 `conda run -n codex`，禁止使用系统 Python 3.9。
- 公共函数和协议添加类型提示和简短 docstring，模块保持单一职责。
- 优先标准库；SSH/SFTP 仅通过可选 Paramiko extra，生成模型依赖不进入本地环境。
- 外部 I/O、子进程、网络和文件覆盖必须显式、可超时并返回结构化错误。
- 路径操作使用 `pathlib`，结构化数据使用 JSON/TOML 解析器，禁止临时字符串协议。
- 未实现功能必须抛出明确异常并标注 `TODO`，不得返回占位成功。
- 新行为添加针对性测试；提交前运行 Conda `codex` 中的 pytest、ruff 和编译检查。
- 不修改 Markdown 记忆，不把 API 响应、日志或提示词复制进控制文件。
