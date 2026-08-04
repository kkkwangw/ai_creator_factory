+++
schema_version = 1
project_id = "uninitialized"
project_status = "template"
project_type = "book_video"
template_version = "0.2.0"
book_title = ""
author = ""
isbn = ""
recommendation_direction = ""
audience = "20-40岁中文短视频用户"
character_version = "uninitialized"
visual_template = "book-list-v1"
+++

# 项目说明

这是模板控制文件。复制为实际项目后，由本地 Codex填写书籍信息，生成唯一 `project_id`，
导入已批准角色包，并把 `project_status` 改为 `active`。项目开始生产后锁定
`template_version`，禁止自动升级。

## 固定目标

- 45--60 秒，9:16，1080x1920，24fps。
- 电影感写实书单短视频。
- 开头和结尾为固定虚构人物口播，中段为 8 个氛围镜头。
- 自动化到 `ready_for_download` 停止，不自动发布平台。
