# Generate Book Video

1. 读取启动与恢复文件，核验当前没有活动 Run。
2. 确认书名，使用项目固定微信读书 Skill 生成脱敏书籍资料；歧义时阻塞。
3. 本地生成文案、分镜、提示词、MiMo WAV、字幕真文和发布文案，并完成本地音频校验。
4. 生成任务 envelope 与显式部署清单，核对远程项目 marker 后上传。
5. 提交固定远程 Runner；SSH 断开后任务继续。远程不得修改 Markdown。
6. 依据真实证据查询 Gate 结果，到 `ready_for_download` 或异常阻塞结束。
7. Python 拉取当前交付物和必要质检证据；本地 Codex检查真实产物并更新 Markdown交接。

禁止自动发布平台、递归上传、启用付费图片回退或把候选模型伪装为已批准。
