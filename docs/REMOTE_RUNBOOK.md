# 远程运行手册

## 首次连接

1. 本地 `.env` 提供 host、port、username、password；不得在命令行传密码。
2. TOFU 自动记录新 host+port；同一 endpoint 指纹变化时阻塞。
3. Codex探测候选持久化目录并让用户首次确认，不回退到临时 `/root`。
4. 本地 `.local/tools.toml` 固定绝对根；远程 marker 的 `project_id` 必须匹配。
5. 运行只读 doctor，记录 GPU、驱动、CUDA、ComfyUI、PyTorch、FFmpeg、UV、磁盘和端口。

## Bootstrap

- 使用预装 ComfyUI Python，不持久化或信任旧 Python/CUDA环境。
- 可切换批准 ComfyUI commit、配置 `extra_model_paths` 和固定轻量节点。
- 自动化脚本和 MuseTalk使用当前实例临时 UV 3.11环境；锁文件和 UV缓存持久化。
- 模型保存在项目持久化 `models/`，按 revision 和哈希校验。
- 禁止自动替换驱动、CUDA、PyTorch或公开 ComfyUI端口。

## 提交与查询

- 上传只读取 `deployments/DEP-*/manifest.json` 中的显式 `auto` 条目。
- `manual` 和 `remote_existing` 条目必须已存在于远端，并逐文件核对大小和 SHA-256。
- 覆盖已有文件只允许使用 SFTP POSIX 原子重命名；服务端不支持时阻塞。
- 相同任务三元组和相同哈希只返回现有任务；相同 ID 不同哈希阻塞。
- 远程每任务启动独立进程组并写 PID、启动时间、ID和日志；SSH断开后继续。
- 取消同时核对三元组、PID、进程启动时间和 `/proc`，禁止按名称 kill。

## 交付与诊断

通过的交付先写暂存目录，验证后原子激活到 `deliverables/current/`。Python可拉取当前交付、
质检证据和定位问题所需的中间片段；模型、缓存和无关运行目录不得自动拉取。

下载同样必须使用显式规格，例如 `deployments/download.example.json`。`local_root` 必须留在当前
项目内；禁止把 `.env`、`.local/`、`models/` 或缓存目录拉回本地。

交付清单固定放在 `runs/<run_id>/evidence/`；验证时同时核对目录中的 `run_id` 和
`PROJECT.md` 中的 `project_id`，不能跨项目或跨 Run复用“已通过”记录。
