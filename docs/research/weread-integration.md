# 微信读书接入说明

> 核验日期：2026-08-04。本文只记录腾讯官方微信读书 Skill及当前项目的接入边界，
> 不包含其他项目的信息或实现。

## 固定来源

- 官方仓库：`Tencent/WeChatReading`
- 固定 commit：`315698a8da1810fab0bbf24a52b38a6960e54cdc`
- Skill版本：`1.0.4`
- 许可证：Apache-2.0
- 项目内副本：`.agents/skills/weread-skills/`
- 完整来源和逐文件 SHA-256：`.agents/skills/weread-skills/SOURCE.json`

项目使用安全 wrapper `SKILL.md` 作为唯一入口。官方原始说明保存在
`UPSTREAM_SKILL.md`，只用于版本和字段核验，不能绕过项目策略直接执行。

## 调用边界

统一网关：

```text
POST https://i.weread.qq.com/api/agent/gateway
Authorization: Bearer $WEREAD_API_KEY
Content-Type: application/json
```

每次请求必须在 JSON顶层提供 `api_name`、业务参数和 `skill_version`。API Key只允许从本地
环境变量读取，不进入 Markdown、日志、命令参数、部署清单或远程服务器。

第一版只允许五个公开资料接口：

| 接口 | 用途 |
| --- | --- |
| `/store/search` | 按书名搜索并获得候选 `bookId`。 |
| `/book/info` | 获取确认版本的元数据和封面 URL。 |
| `/book/chapterinfo` | 获取目录和章节标识。 |
| `/book/bestbookmarks` | 获取公开热门划线。 |
| `/review/list` | 获取公开点评作为研究信号。 |

禁止读取私人书架、个人笔记、阅读进度、阅读统计和个性化资料，也禁止调用未列入 allowlist
的接口。收到 `upgrade_info` 时必须阻塞，由本地 Codex生成版本差异清单，经人工选择后升级；
不得自动更新固定 Skill。

## 书籍确认流程

1. 用户提供书名；作者、ISBN和推荐方向选填。
2. 调用 `/store/search` 获取候选记录。
3. 使用作者、译者、出版社、出版时间和 ISBN消除版本歧义。
4. 只有唯一记录得到确认后，才允许调用详情、目录、热门划线和公开点评接口。
5. 标准化结果保留来源 `bookId`、查询接口、查询时间和内容哈希，不长期保存原始响应。

同名书籍存在无法排除的版本歧义时必须阻塞，不能默认选择第一条记录。

## 封面处理

第一版只使用已确认 `/book/info` 记录返回的封面 URL。封面下载是独立资产步骤，必须记录：

- 来源 URL和 `bookId`
- 获取时间
- HTTP状态和 MIME类型
- 像素尺寸
- 文件大小和 SHA-256

接口返回封面 URL不等于获得永久存储或再发布授权，正式发布前仍应确认素材使用边界。

## 尚未实现

当前项目已固定 Markdown Skill、来源版本、allowlist和安全策略，但尚未实现确定性查询适配器、
请求重试分类、标准化 `book_record.json`、封面下载器和真实 API测试。Gate 1在这些能力完成前
必须保持阻塞，不能使用占位数据冒充查询成功。
