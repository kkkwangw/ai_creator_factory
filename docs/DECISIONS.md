# 已确认决策

本文汇总模板 0.2.0 的稳定产品决策。详细证据见 `docs/research/`。

- 一个实际目录只生产一本书的一条视频，不做多项目管理。
- 实际项目不使用 Git；公共模板使用 GitHub。项目生产后锁定模板版本。
- 本地主 Codex唯一主控；远程没有 Codex，只运行确定性工具。
- 控制 Markdown只在本地修改，远程副本采用带哈希的一向同步。
- 记忆为有上限 Markdown：CURRENT 16 KiB，历史最多20份。
- 本地 Conda `codex` 与远程 UV统一 Python 3.11；系统 Python 3.9不使用。
- 自动部署单文件64 MiB、单次256 MiB，所有上传必须经过清单。
- MiMo本地生成冰糖 WAV；FFmpeg与Whisper强制验真。
- 默认角色为18--25岁虚构成年中国女性，同一账号复用固定角色包。
- 首选候选栈为 FLUX.2 Klein 4B Base FP8、Wan2.2-TI2V-5B、MuseTalk 1.5。
- `allow_paid_image_fallback` 固定为 false，付费回退必须未来显式开启。
- `book-list-v1`首次样片人工准入，之后参数冻结。
- 全自动运行到 `ready_for_download`，不自动登录或发布平台。
