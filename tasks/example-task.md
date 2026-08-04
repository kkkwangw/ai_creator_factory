+++
schema_version = 1
run_id = "run-20260804-example"
task_id = "task-produce-book-video"
prompt_id = "prompt-example-001"
task_type = "book_video"
book_title = "示例书名"
author = ""
isbn = ""
recommendation_direction = ""
mode = "unattended"
+++

# 目标

为已确认的微信读书书籍记录生成一条符合 `book-list-v1` 的书单视频。

# 验收

- Gate 1--6 的真实证据完整。
- 最终交付可从真实文件推导为 `ready_for_download`。
- 不自动发布，不自动启用付费图片回退。
