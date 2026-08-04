# 架构

## 控制面与数据面

```text
本地 Codex
  |-- Markdown 控制面
  |-- 微信读书 / MiMo / Whisper
  |-- task envelope / deployment manifest
  `-- Paramiko SSH/SFTP
             |
             v
远程持久化项目目录
  |-- 确定性 Runner
  |-- 预装 ComfyUI（localhost）
  |-- 临时 UV 3.11 环境中的 MuseTalk / 自动化工具
  |-- 模型、缓存、证据和媒体产物
  `-- deliverables/current
```

本地是唯一决策与 Markdown 写入端。远程没有 Codex、LLM 或自由文本规划能力，只执行已签入
envelope 的参数。SSH 负责提交、查询和精确取消，不承担远程进程生命周期。

## 可信度层级

从高到低：真实媒体与文件哈希、工具原始探测结果、结构化执行结果、状态 JSON、Markdown
交接文字。恢复时必须从高可信证据向上重建，不允许 `done` 覆盖坏文件。

## 插件边界

- `audio.text_to_speech`：MiMo只是一个本地插件实现。
- `image.generate_and_edit`：首个候选实现为 ComfyUI + FLUX.2 Klein。
- `video.image_to_video`：首个候选实现为 ComfyUI + Wan2.2。
- `video.lip_sync`：首个候选实现为独立 UV + MuseTalk。
- `storage.transfer`：首个实现为 Paramiko SFTP。

候选名称只出现在插件配置和模型清单中，核心任务按能力引用。

## 非目标

第一版不做 SaaS、多用户、并发 Run、自动平台发布、远程 Codex、自动模板升级、模型自动替代
或跨项目全局记忆。
