# `book-video` 项目的微信读书接入研究

> 核验日期：2026-08-04。本文只依据 GitHub 仓库源码、仓库文档和腾讯官方页面。未使用真实 API Key，也未请求任何用户账号数据。引用固定到核验时的 commit，避免后续分支变化导致证据漂移。

## 结论

用户所说的项目**最可能**是 [`Endless1936/book-video`](https://github.com/Endless1936/book-video)：仓库名完全匹配，README 将其描述为通过自然语言完成选书、文案、氛围图、旁白对齐和成片制作的图书短视频工作流，和当前模板的用途高度一致。[来源：README](https://github.com/Endless1936/book-video/blob/af8e28d28a07786a494cdb94fc62d2231898c4cb/README.md)

不过，仅凭“book-video”无法做到绝对唯一识别。GitHub 还有多个同名或派生仓库：

| 候选 | 区分依据 | 微信读书实现情况 |
| --- | --- | --- |
| [`Endless1936/book-video`](https://github.com/Endless1936/book-video) | 精确同名；自然语言书单短视频工作流；本次核验 commit `af8e28d` | 声明依赖腾讯官方 Skill；有通用请求辅助模块，但仓库内没有调用方 |
| [`xionghm/book_video`](https://github.com/xionghm/book_video) | README、版权声明和核心脚本与上项高度一致，最新提交说明包含合并上游 | 同样的 `weread-request.mjs`，同样没有调用方 |
| [`yuguangzsl/book-video-agent`](https://github.com/yuguangzsl/book-video-agent) | 基于相同工作流继续扩展，README 明确写出官方 Skill 和隐藏式本地配置流程 | 配置流程更安全，但业务调用仍主要由 Agent/Skill 驱动 |
| [`wxhBadUser/book-video-factory`](https://github.com/wxhBadUser/book-video-factory) | 名称近似，但定位为 15–20 分钟名著单主播长视频，不是同一个短视频项目 | 内置了较完整的 Python 采集、标准化和测试实现，可作为设计参考 |

因此，当前可以把 `Endless1936/book-video` 作为主候选，但在正式复制实现前，最好由用户补充 owner 或原始链接确认。

## 主候选实际上如何接入微信读书

`Endless1936/book-video` 的规则要求 Agent 在缺失时安装并启用腾讯官方微信读书 Skill，而不是把 Skill 源码复制进仓库；选书和写稿时，优先使用它获取元数据、评分、热门划线和公开点评。[来源：AGENTS.md](https://github.com/Endless1936/book-video/blob/af8e28d28a07786a494cdb94fc62d2231898c4cb/AGENTS.md#L8-L32) [来源：playbook](https://github.com/Endless1936/book-video/blob/af8e28d28a07786a494cdb94fc62d2231898c4cb/docs/book-video-playbook.md#L7-L10)

仓库同时包含 [`scripts/lib/weread-request.mjs`](https://github.com/Endless1936/book-video/blob/af8e28d28a07786a494cdb94fc62d2231898c4cb/scripts/lib/weread-request.mjs#L1-L32)，它完成以下通用工作：

- 从进程环境或项目 `.env` 读取 `WEREAD_API_KEY`。
- 向 `https://i.weread.qq.com/api/agent/gateway` 发送 JSON `POST`。
- 使用 `Authorization: Bearer <key>` 鉴权。
- 自动附加 `skill_version: "1.0.4"`。
- 在 HTTP 错误、`upgrade_info` 或非零 `errcode` 时抛错，并对错误字符串中的 Bearer token 和 `wrk-...` 形式密钥做脱敏。

但源码搜索显示，`wereadRequest()` 只在定义文件中出现，没有被搜索、详情或采集脚本导入。因此主候选目前是“**Agent 按官方 Markdown Skill 调用外部 API**”，而不是已经拥有一个端到端、可测试的项目内微信读书采集器。不能因为辅助文件存在就判定生产链路已经接通。

初始化脚本会检查 `WEREAD_API_KEY`，并可将其写入项目根目录 `.env`；`.gitignore` 排除了 `.env`、本地候选池、模型和 episode 产物。[来源：init.mjs](https://github.com/Endless1936/book-video/blob/af8e28d28a07786a494cdb94fc62d2231898c4cb/scripts/init.mjs#L26-L51) [来源：.gitignore](https://github.com/Endless1936/book-video/blob/af8e28d28a07786a494cdb94fc62d2231898c4cb/.gitignore#L1-L23)

## 腾讯官方 Skill 和 API 契约

微信读书官方页面给出的安装命令是 `npx skills add Tencent/WeChatReading -g`，对应的一手仓库为 [`Tencent/WeChatReading`](https://github.com/Tencent/WeChatReading)。本次核验版本为 `1.0.4`、commit `315698a`。[来源：微信读书官方配置页](https://weread.qq.com/r/weread-skills) [来源：官方 README](https://github.com/Tencent/WeChatReading/blob/315698a8da1810fab0bbf24a52b38a6960e54cdc/README.md)

官方 Skill 本体由 Markdown 文档组成，没有 Python 包或 Node 运行时代码。它要求 Agent 使用 HTTP 客户端调用统一网关，因此“主要依靠 Markdown Skill”是可行的；最低运行依赖只是网络访问、API Key 和一个 HTTPS 客户端。项目若以后需要确定性落盘、重试和证据清单，再由薄执行插件负责，不需要把记忆管理写进 Python。[来源：官方 Skill](https://github.com/Tencent/WeChatReading/blob/315698a8da1810fab0bbf24a52b38a6960e54cdc/skills/SKILL.md)

统一调用规则如下：[来源：官方调用规范](https://github.com/Tencent/WeChatReading/blob/315698a8da1810fab0bbf24a52b38a6960e54cdc/skills/SKILL.md#L27-L88)

```text
POST https://i.weread.qq.com/api/agent/gateway
Authorization: Bearer $WEREAD_API_KEY
Content-Type: application/json

{
  "api_name": "/store/search",
  "keyword": "书名",
  "scope": 10,
  "skill_version": "1.0.4"
}
```

关键约束：

- API Key 格式为 `wrk-...`，绑定用户身份；需要用户身份的接口由网关注入身份，不应在 body 中手动传 `vid`。
- `api_name`、`skill_version` 和所有业务参数必须位于 body 顶层，不能包进 `params`。
- JSON 回包中的 `errcode != 0` 表示错误。
- 出现 `upgrade_info` 时必须停止当前操作，升级 Skill 后重试。
- `{"api_name":"/_list"}` 可查询网关当前公开的接口定义；正式实现应在首次配置或版本变化时用它校验能力，而不是永久相信旧文档。

## 适合书单视频的最小查询流程

第一版只需要五个公开资料接口：

1. `/store/search`：传 `keyword=<书名>`、`scope=10`；从各 `results[].books[].bookInfo` 中选择书籍。搜索结果是分页片段，不代表全量结果；下一页使用末项 `searchIdx` 作为 `maxIdx`。[来源：search.md](https://github.com/Tencent/WeChatReading/blob/315698a8da1810fab0bbf24a52b38a6960e54cdc/skills/search.md)
2. `/book/info`：传 `bookId`，获取经确认版本的完整元数据和封面 URL。[来源：book.md](https://github.com/Tencent/WeChatReading/blob/315698a8da1810fab0bbf24a52b38a6960e54cdc/skills/book.md#L7-L33)
3. `/book/chapterinfo`：传 `bookId`，获取目录和 `chapterUid`，用于给热门划线补充章节定位。[来源：book.md](https://github.com/Tencent/WeChatReading/blob/315698a8da1810fab0bbf24a52b38a6960e54cdc/skills/book.md#L35-L60)
4. `/book/bestbookmarks`：传 `bookId`、`chapterUid=0`、`synckey=0`，获取全书热门划线。服务端固定返回热度最高的 20 条，不支持分页。[来源：notes.md](https://github.com/Tencent/WeChatReading/blob/315698a8da1810fab0bbf24a52b38a6960e54cdc/skills/notes.md#L160-L192)
5. `/review/list`：传 `bookId`、`reviewListType=0`、`count`、`maxIdx`、`synckey`，获取公开点评；翻页使用最后一条 `idx` 和回包 `synckey`。[来源：review.md](https://github.com/Tencent/WeChatReading/blob/315698a8da1810fab0bbf24a52b38a6960e54cdc/skills/review.md#L14-L64)

### 需要保留的字段

| 数据 | 官方返回路径 | 第一版用途 |
| --- | --- | --- |
| 唯一书籍 ID | `bookInfo.bookId` / `/book/info.bookId` | 锁定微信读书记录和后续查询 |
| 书名、作者 | `title`, `author` | 书籍确认和文案事实 |
| 译者、出版社、出版时间、ISBN | `/book/info.translator`, `publisher`, `publishTime`, `isbn` | 版本消歧 |
| 简介、分类、字数 | `intro`, `category`, `wordCount` | 内容研究信号 |
| 评分 | `newRating`, `newRatingCount`, `newRatingDetail` | 书籍资料和推荐方向；评分为百分制 |
| 封面 | `/book/info.cover`，搜索结果也有 `bookInfo.cover` | 获取首版封面 |
| 阅读跳转 | `deepLink` | 来源追溯；不得自行拼接链接 |
| 目录 | `chapters[].chapterUid`, `chapterIdx`, `title`, `level`, `wordCount` | 划线章节定位 |
| 热门划线 | `items[].markText`, `totalCount`, `chapterUid`, `range`, `bookmarkId` | 情绪入口和研究证据 |
| 公开点评 | 双层路径 `reviews[].review.review.content`, `star`, `createTime`, `author` | 读者反馈信号，不能当作书籍事实 |

### 封面获取边界

官方接口只提供 `cover` URL，没有在 Skill 中定义“封面下载接口”，也没有承诺永久 URL、固定尺寸、MIME 类型或再发布许可。因此可以复用的逻辑是：先由 `/store/search` 选中记录，再以 `/book/info.cover` 为权威 URL；实际下载应由独立资产步骤完成，校验 HTTP 状态、MIME、像素尺寸和 SHA-256，并记录来源 URL、`bookId` 和获取时间。

封面来自已确认记录并不自动等于获得商业再发布权。模板应把“来源一致性”和“使用权”分成两个字段；找不到封面或下载失败时，按已确认策略回退到书名文字卡，不伪造官方封面。

## 可复用设计

以下设计可以直接吸收进 `ai_creator_factory` 的后续 TODO：

- **官方 Skill 作为契约来源**：使用腾讯仓库的 Markdown 接口说明，不依赖第三方逆向接口。
- **统一网关适配器**：固定网关、Bearer 鉴权、顶层平铺参数、Skill 版本上报、`upgrade_info` 阻塞。
- **两阶段消歧**：先搜索，再用书名和作者筛选，之后以 `/book/info` 的 ISBN、出版社、译者和出版时间确认版本。
- **来源字段不被展示名覆盖**：保留 `source_book_id`、`source_title`、`source_channel=weread`；主候选的候选池已经采用这些字段。[来源：候选池 schema](https://github.com/Endless1936/book-video/blob/af8e28d28a07786a494cdb94fc62d2231898c4cb/data/book-pipeline.example.csv)
- **研究信号分层**：元数据、热门划线和公开点评必须分开；点评不能作为原著事实，长划线不能直接复制成文案。
- **原始证据与标准化记录分离**：近名仓库的实现把搜索、详情、目录、热门划线、点评分别保存，并生成 `book_source_pack.json` 和采集清单，这个模式适合当前项目的证据驱动 Gate。[来源：weread.py](https://github.com/wxhBadUser/book-video-factory/blob/55c7dfb39a5bdde521573df650fc129ace35df5a/book_video_factory/src/book_video_factory/weread.py#L166-L330)

对近名仓库的无网络模拟验证使用 Conda `codex` 执行，未安装依赖：其现有 3 个 `WeReadTests` 均通过，覆盖书名/作者精确匹配、热门划线与公开点评分层、原始/标准化资料和项目状态落盘。这个结果只证明本地转换逻辑按测试样例工作，不证明真实网关当前可用。

## 不应原样复制的风险

1. **主候选并没有完整采集链路。** `weread-request.mjs` 无调用方，只有规则要求 Agent 使用外部 Skill。模板若需要 unattended 模式，仍需补上确定性的任务输入、标准化 JSON、重试和证据输出。
2. **旧版主候选要求把 Key 发到对话。** 其 `AGENTS.md` 明确让用户把 Key 发给 Agent，再写 `.env`，这与当前项目“禁止暴露”冲突，不能复制。[来源：AGENTS.md](https://github.com/Endless1936/book-video/blob/af8e28d28a07786a494cdb94fc62d2231898c4cb/AGENTS.md#L12-L15) 较新的派生项目改为本地 TTY 隐藏输入，并拒绝命令行参数传 Key，方向更合适。[来源：派生项目 init.mjs](https://github.com/yuguangzsl/book-video-agent/blob/f9ffa3a0f63becceae69a1325677b293e3de2917/scripts/init.mjs#L181-L201)
3. **全局安装不满足项目内可复现。** 官方页面推荐 `-g` 安装，版本可能随机器和时间漂移。当前模板应记录 Skill 仓库、commit、文档版本和 SHA-256；是否复制到项目内，等用户提供既有 Skill 后再定。
4. **同名同作者仍可能有多个版本。** 近名仓库的选择逻辑在多个精确匹配中直接取第一项，可能锁错译本或出版社。[来源：select_book](https://github.com/wxhBadUser/book-video-factory/blob/55c7dfb39a5bdde521573df650fc129ace35df5a/book_video_factory/src/book_video_factory/weread.py#L119-L147) Gate 1 应使用 ISBN、译者、出版社和出版时间继续消歧。
5. **错误处理不够完整。** 主候选辅助模块没有请求超时、重试、`AbortSignal`、JSON 解析错误分类或速率限制处理；也没有产出请求证据清单。异常最多重试 3 次时，只应重试超时、连接中断、429 和可恢复 5xx，不应重试 401、403、版本升级或书籍歧义。
6. **版本硬编码会失效。** 官方要求收到 `upgrade_info` 立即升级；`1.0.4` 只能作为当前核验值，不能成为永久常量。
7. **原始回包可能包含个人信息。** 官方接口还支持个人书架、笔记、阅读进度，公开点评也可能带昵称、头像和 `userVid`。本项目首版只应 allowlist 上述五个接口，标准化时丢弃无关用户标识，不调用个人笔记和阅读统计接口。
8. **Python 参考实现不跨 Windows。** 近名仓库的 `load_api_key()` 无条件调用 `os.uname()` 再判断 macOS；Windows 上没有该 API，且 macOS Keychain 路径与当前跨平台项目不一致。[来源：weread.py](https://github.com/wxhBadUser/book-video-factory/blob/55c7dfb39a5bdde521573df650fc129ace35df5a/book_video_factory/src/book_video_factory/weread.py#L28-L49) 不能整段复制。
9. **保存完整原始响应与数据最小化冲突。** 参考实现把五个原始回包全部落盘；对个人项目虽便于追溯，但应先裁剪潜在个人标识，或把原始响应设为短期证据并按运行保留策略清理。

## 对当前模板的建议

当前先保留微信读书为 TODO 是合理的。后续用户提供自己正在使用的 Skill 或原始仓库链接后，再做一次精确差异核验；在此之前不要实现猜测性的接口封装。

建议 TODO 最终拆成以下验收项：

1. 锁定 `Tencent/WeChatReading` 来源 commit、Skill 版本和文件校验值。
2. 只在本地读取 `WEREAD_API_KEY`，通过隐藏式交互配置；Key 不进入对话、日志、任务 Markdown、部署清单或远程 `.env`。
3. 实现五接口 allowlist 和结构化错误分类；收到 `upgrade_info` 必须阻塞。
4. 输出标准化 `book_record.json`、最小必要的来源证据和封面资产清单；远程只接收已确认结果，不持有微信读书 Key。
5. 以 `bookId + ISBN/出版社/译者/出版时间` 完成版本确认，再允许封面和文案步骤继续。
6. 对真实 API 做一次脱敏契约测试，再将 Gate 1 从人工确认逐步迁移到 unattended；测试 fixture 中只能使用伪造 key 和脱敏响应。

这个边界符合当前架构：Markdown Skill 负责告诉本地 Codex“如何查询和判断”，薄执行层只负责外部请求、JSON 证据和封面下载，不承担记忆管理，也不需要把微信读书接入部署到远程 GPU 服务器。
