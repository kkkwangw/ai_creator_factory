# 第一版开放模型视频栈研究

> 核验日期：2026-08-04。范围限定为租赁单卡 24GB（48GB 可选）、预装 ComfyUI、竖屏 45--60 秒电影感写实书单视频。本文只引用模型/节点项目方和 ComfyUI 官方资料；未下载模型、未安装依赖、未做 GPU 实测。许可证判断是工程准入建议，不是法律意见。

## 结论

第一版建议采用三个主模型，严格串行加载：

| 阶段 | 首选 | 为什么是首选 | 当前结论 |
| --- | --- | --- | --- |
| 关键帧与固定虚构人物 | **FLUX.2 Klein 4B Base FP8** | Apache-2.0；一个 4B 模型统一支持 T2I、单参考和多参考编辑；官方模型卡称约 13GB VRAM，ComfyUI 有 Base 原生工作流 | **24GB 和集成已证实；人物一致性通过率未证实** |
| 3--6 秒图生视频 | **Wan2.2-TI2V-5B** | Apache-2.0；同一 5B 模型支持 T2V/I2V；官方明确支持 704x1280/1280x704、720p、24fps、24GB RTX 4090，并给出 5 秒 720p 低于 9 分钟的结果；ComfyUI 原生集成 | **首版最确定的主视频模型** |
| 开头/结尾中文口型 | **MuseTalk 1.5** | 项目方明确支持中文并声明训练模型可商用；输入视频沿用源 FPS；1.5 主权重约 3.40GB | **需独立插件环境；24GB 峰值和许可元数据差异必须实测/留证** |

这不是“三个模型同时驻留显存”。每个任务结束后必须释放模型、清空 ComfyUI 队列并验证 GPU 空闲，再进入下一阶段。24GB 主路径不应默认加载 FLUX.2 9B/dev、Wan2.2 14B、Wan2.2-S2V-14B 或 Qwen-Image 的多个大权重。

第一版人物策略仍要收窄：FLUX.2 Klein 4B Base 先生成并确认一组标准人物参考图；如果用户提供三视图复合图，先确定性拆成独立参考图，再作为多参考编辑输入。开头和结尾优先从同一组参考图编辑关键帧，中段氛围镜头默认不出现主角。官方只证明模型支持多参考编辑，没有承诺固定人物通过率，因此不能在 GPU 基准前把“跨姿势、跨场景保持同一身份”写成已具备能力。

若 10 镜头基准中人物一致性不达标，再显式增加 Qwen-Image-2512 + Qwen-Image-Edit-2511；不要一开始就把它们加入最小栈。若 MuseTalk 失败，再评估 LatentSync 1.6。所有备用项也必须通过许可证、固定版本和实机基准后才能进入 `approved`。

## 首选栈的证据

### 1. FLUX.2 Klein 4B Base FP8：关键帧和固定人物

**已证实**

- BFL 官方模型表明确：4B distilled 和 4B Base 都支持 T2I、单参考和多参考编辑，均为 Apache-2.0；9B、9B Base 和 dev 则是 Non-Commercial，不能因同属 Klein 系列而混用。[官方仓库（固定 commit）](https://github.com/black-forest-labs/flux2/blob/50fe5162777813d869182b139e83b10743caef15/README.md)
- 4B Base 模型卡明确写明约 13GB VRAM，可在 RTX 3090/4070 及以上运行，并允许 Apache-2.0 下的商业使用；模型卡同时列出错误文字、偏差、提示不遵循和违法/有害用途限制。[Base FP8 模型卡（固定 revision）](https://huggingface.co/black-forest-labs/FLUX.2-klein-base-4b-fp8/blob/103db268c10d4d3921101b46057671f9ac460da6/README.md)
- ComfyUI 官方指南提供 T2I、4B Base 编辑、4B distilled 编辑三个原生模板。其 RTX 5090 数据为 distilled 8.4GB/约 1.2 秒、Base 9.2GB/约 17 秒；这只能证明该测试环境，不能外推到租赁 GPU 的时延，但 24GB 容量风险很低。[ComfyUI 官方指南](https://docs.comfy.org/tutorials/flux/flux-2-klein.md)；[Base 编辑模板（固定 commit）](https://github.com/Comfy-Org/workflow_templates/blob/7653f1cdef1d92394b6ef9946018c0a8aa4136b8/templates/image_flux2_klein_image_edit_4b_base.json)
- 第一版选 Base 而不是 distilled，是因为图片阶段不敏感于十几秒时延，优先保留 50 步 Base 的灵活性和输出多样性；这仍是待基准的工程选择，不是官方质量胜负结论。

**磁盘体积（不是峰值显存）**

| 文件 | 官方仓库字节数 |
| --- | ---: |
| `flux-2-klein-base-4b-fp8.safetensors` | 4,089,498,488 |
| `qwen_3_4b.safetensors` | 8,044,982,048 |
| `qwen_3_4b_fp4_flux2.safetensors` | 3,848,213,998 |
| `flux2-vae.safetensors` | 336,211,292 |

24GB 首测采用 **Base FP8 transformer + BF16 文本编码器 + VAE**，文件合计约 12.47GB。文件之和不能推导运行峰值，仍以 BFL 约 13GB 和 ComfyUI 5090 的 9.2GB 为两条官方观测，并在实际租机记录峰值。FP4 文本编码器只作为 OOM/低内存回退实验，不能预先认定画质无损。文件来源为 [BFL Base FP8（固定 revision）](https://huggingface.co/black-forest-labs/FLUX.2-klein-base-4b-fp8/tree/103db268c10d4d3921101b46057671f9ac460da6) 和 [Comfy-Org 共享组件（固定 revision）](https://huggingface.co/Comfy-Org/vae-text-encorder-for-flux-klein-4b/tree/a9e4ca87c16db4c4e1a16406a9ddb300ab0ae246)。

**未证实，必须基准**

- 704x1280 竖屏下的人脸、手、书本和电影感写实质感是否达到发布标准。
- 同一人物参考组经不同构图、背景和机位编辑后，身份、发型和服装是否仍一致；用户三视图是否能改善而不是污染身份。
- Base FP8 与 distilled FP8 的写实质感、人物一致性、提示遵循和单张耗时差异。
- FP4 文本编码器对提示理解的影响。书名和封面文字不由图片模型生成，仍使用微信读书封面和确定性排版。

### 2. Wan2.2-TI2V-5B：所有 I2V 镜头

**已证实**

- 官方 5B 混合模型同时支持文本生成视频和图生视频，输出 720p、24fps；竖屏允许 `704*1280`。`frame_num` 必须满足 `4n+1`，默认 121 帧，即约 5.04 秒。[README（固定 commit）](https://github.com/Wan-Video/Wan2.2/blob/42bf4cfaa384bc21833865abc2f9e6c0e67233dc/README.md)；[参数校验（固定 commit）](https://github.com/Wan-Video/Wan2.2/blob/42bf4cfaa384bc21833865abc2f9e6c0e67233dc/generate.py#L123)
- 官方命令明确写明 24GB（RTX 4090）可运行，参数为模型卸载、转换模型 dtype、T5 放 CPU；官方报告称 5 秒 720p 在单张消费级 GPU 上低于 9 分钟。这里没有给出不同 GPU 型号、竖屏、不同帧数的等价耗时，不能外推成 SLA。[README 的 TI2V 和效率段](https://github.com/Wan-Video/Wan2.2/blob/42bf4cfaa384bc21833865abc2f9e6c0e67233dc/README.md#run-text-image-to-video-generation)
- 模型和代码为 Apache-2.0，官方称不主张生成内容权利，并列出违法、伤害、恶意隐私和虚假信息等使用限制说明。[许可证（固定 commit）](https://github.com/Wan-Video/Wan2.2/blob/42bf4cfaa384bc21833865abc2f9e6c0e67233dc/LICENSE.txt)
- ComfyUI 官方提供原生 5B 工作流，并称通过原生卸载“应可很好地适配 8GB VRAM”。本项目仍以模型方更保守的 24GB 证据做准入，不把 8GB 声明当成本项目验收结果。[ComfyUI 官方教程](https://docs.comfy.org/tutorials/video/wan/wan2_2.md)

**ComfyUI 官方文件**

| 文件 | 字节数 |
| --- | ---: |
| `wan2.2_ti2v_5B_fp16.safetensors` | 9,999,658,848 |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | 6,735,906,897 |
| `wan2.2_vae.safetensors` | 1,409,400,960 |

合计约 18.14GB，来源为 [Comfy-Org 重打包仓库（固定 revision）](https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/tree/fb1388adc906ab39ffc26ee40e96b22886b56bc4)。原始模型仓库 revision 为 [`921dbaf3...`](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B/tree/921dbaf3f1674a56f47e83fb80a34bac8a8f203e)，原始 BF16 权重、BF16 T5 和 VAE 合计约 33.98GB；ComfyUI 拆分版通过 FP8 文本编码器降低了持久化和运行负担。

**帧数策略**

第一版固定生成 121 帧、24fps，即约 5.04 秒；需要 3--5 秒时只在确定性剪辑中取片，不让模型改变帧长。5 秒落在用户允许的 3--6 秒范围内，也是官方配置和效率证据覆盖的唯一长度。73/97/145 帧虽然满足 `4n+1`，但质量、显存和耗时没有官方基准，等主路径跑通后再单独评估。

最终 1080x1920 不直接由模型生成；先生成 704x1280，再由 FFmpeg 等比放大到 1056x1920，并左右各补 12 像素，避免非等比拉伸。是否改用裁切方案由 `book-list-v1` 固定模板基准后确定。

**主要风险**

- 24GB 可运行不等于每镜头在 45 分钟任务上限内稳定完成；预装镜像的 CUDA、PyTorch、xFormers/Flash Attention 和 ComfyUI commit 都会影响结果。
- I2V 仍可能改变人物面部、手指、书本封面和背景文字；书名和封面不得依赖生成视频中的 AI 文字，必须由确定性排版覆盖。
- 官方低于 9 分钟结果是 5 秒 720p 的特定测试，不能据此承诺十镜头总时长。

### 3. MuseTalk 1.5：开头和结尾口型

**已证实**

- 官方明确称支持中文、英文和日文，1.5 提升清晰度、身份一致性和口型同步；修改区域为 256x256 人脸，Tesla V100 上可达到 30fps+。[README（固定 commit）](https://github.com/TMElyralab/MuseTalk/blob/0a89dec45a0192b824e3cf4daf96c239440c5ed8/README.md)
- 输入是视频时，官方代码读取源视频 FPS，并用同一 FPS 调 Whisper 特征和 FFmpeg 输出，因此 Wan 的 24fps 可原样进入，不需要先转成 25fps。[推理代码（固定 commit）](https://github.com/TMElyralab/MuseTalk/blob/0a89dec45a0192b824e3cf4daf96c239440c5ed8/scripts/inference.py)
- 1.5 主权重 `musetalkV15/unet.pth` 为 3,400,074,924 字节，另需 SD VAE、Whisper、DWPose、SyncNet、face parsing 等依赖权重，不能把 3.40GB 误报成完整插件体积。[模型仓库（固定 revision）](https://huggingface.co/TMElyralab/MuseTalk/tree/3ef28bc5cff08c90ad8178a25f1b570cd800170f)
- 官方 README 声明代码 MIT、训练模型可用于任何目的（包括商业），同时要求各依赖分别遵守许可证。Hugging Face 模型卡元数据却标为 `creativeml-openrail-m`；两处都不是“禁止商业”，但许可表达不一致，进入 `approved` 前必须同时保存 README、MIT LICENSE、模型卡和所有依赖许可，不能只记录 MIT。[代码许可证（固定 commit）](https://github.com/TMElyralab/MuseTalk/blob/0a89dec45a0192b824e3cf4daf96c239440c5ed8/LICENSE)

**集成边界**

MuseTalk 官方只链接一个第三方 ComfyUI 节点，并明确说明第三方集成没有经过项目方验证、维护或更新。该节点固定 commit 的 README 仍只布置旧 `musetalk` 权重，早于 1.5，不可作为生产基线。[第三方节点（固定 commit）](https://github.com/chaojie/ComfyUI-MuseTalk/tree/84f4b6dcbb0d87e87687f324092056646582457d)

第一版应调用官方 MuseTalk CLI，使用独立、固定 commit 的远程 UV 插件环境；执行前关闭/卸载 ComfyUI 中的生成模型，执行后只写独立 JSON、日志和产物。不要把 MuseTalk 的旧版 diffusers、transformers、TensorFlow、MMLab 依赖装进云镜像自带的 ComfyUI Python。

**未证实，必须基准**

- 官方没有提供最低显存；V100 存在不同显存型号，不能据“V100 30fps+”推导 24GB 一定足够。
- MiMo“冰糖”中文 WAV 在书名、英文作者名、数字、停顿和快速连读时的同步效果。
- 官方明确列出身份细节可能丢失（胡须、唇形、唇色）、单帧管线可能抖动；是否能通过 1080x1920 成片近景标准必须实测。
- 对头部大幅转动、遮挡、侧脸、过小人脸、已有张嘴动作的稳定性。首版口播镜头必须使用正面或轻微 3/4 角度、脸部无遮挡、低运动量画面。

## 备用组合

### 人物一致性备用：Qwen-Image-2512 + Qwen-Image-Edit-2511

Qwen 官方称 2512 降低人物的 AI 感，2511 显著改善人物一致性和图像漂移并支持多图输入；两者均为 Apache-2.0。[官方仓库（固定 commit）](https://github.com/QwenLM/Qwen-Image/blob/6b5e1f5cec987d404be5ac6657db3b9aacb56a89/README.md#qwen-image-edit-2511-for-image-editing-multiple-image-support-and-improved-consistency)；[Edit 模型卡（固定 revision）](https://huggingface.co/Qwen/Qwen-Image-Edit-2511/blob/6f3ccc0b56e431dc6a0c2b2039706d7d26f22cb9/README.md)

Comfy-Org 已提供 `qwen_image_edit_2511_fp8mixed.safetensors`（20,533,762,817 字节），共享的 FP8 Qwen2.5-VL 7B 文本编码器为 9,384,670,680 字节，VAE 为 253,806,246 字节；磁盘合计约 30.17GB。[Edit 重打包（固定 revision）](https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/tree/e9e85de74a8f48c1e3e2656617626348675a2f21)；[共享组件（固定 revision）](https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/tree/46839d338df81ce625d5fae27d7e370314c0fbc9)

官方 Qwen 仓库提到 DiffSynth-Studio 可层级卸载至 4GB 内推理，但这不是 2511/2512 在 ComfyUI 中的 24GB 峰值证明。故建议 48GB 首测；24GB 只作为 ComfyUI 原生卸载实验，OOM 或单张超过 45 分钟即失败。它只在 FLUX.2 多参考人物方案未达到 70% 可用率时启用。两套模型共享文本编码器/VAE，但各自仍有约 20.5GB FP8 transformer，用户担心模型数量时不能默认同时下载。

### 视频备用：LTX-Video 0.9.8 13B distilled FP8

Lightricks 官方仓库支持 I2V、多关键帧，项目方维护 `ComfyUI-LTXVideo`，13B distilled 推荐 8 步并提供 FP8。FP8 主权重为 15,694,280,140 字节；文本编码器、VAE 和上采样器另计。[官方仓库（固定 commit）](https://github.com/Lightricks/LTX-Video/blob/4b2d053057623ddd4d0a1d3e9cd28890e9ef487f/README.md)；[模型仓库（固定 revision）](https://huggingface.co/Lightricks/LTX-Video/tree/8984fa25007f376c1a299016d0957a37a2f797bb)

代码为 Apache-2.0，但权重为 OpenRAIL-M，明确允许商业使用同时要求遵守用途限制，并对公开生成内容要求清晰披露为机器生成。[权重许可](https://huggingface.co/Lightricks/LTX-Video/blob/8984fa25007f376c1a299016d0957a37a2f797bb/ltx-video-2b-v0.9.5.license.txt)

官方没有给出该 13B FP8 组合在 24GB、704x1280、3--6 秒上的峰值显存和耗时。因此它不是默认主路径，只用于 Wan 运动/一致性不达标后的 A/B；首测优先 48GB。

### 口型质量备用：LatentSync 1.6

LatentSync 1.6 使用 512x512 训练视频以缓解 1.5 的牙齿和嘴唇模糊；官方给出推理最低显存 18GB。1.5 更新明确称改善中文视频，1.6 模型卡说明结构和训练策略未变，仅训练数据分辨率提高。[README（固定 commit）](https://github.com/bytedance/LatentSync/blob/a229c3948406bc2cf6eaf4873e662e70c6a04746/README.md)；[1.6 模型卡（固定 revision）](https://huggingface.co/ByteDance/LatentSync-1.6/blob/c42c7e6c8e9c213626389fa7d9a3c444b8536353/README.md)

推理核心文件 `latentsync_unet.pt` 为 5,072,222,488 字节，`whisper/tiny.pt` 为 75,572,083 字节；SyncNet 和其他辅助权重另计。[模型仓库（固定 revision）](https://huggingface.co/ByteDance/LatentSync-1.6/tree/c42c7e6c8e9c213626389fa7d9a3c444b8536353)

风险是代码仓库为 Apache-2.0，但 Hugging Face 权重仅以元数据标记 `openrail++`，仓库没有提供对应的独立 LICENSE 文件；另外项目方没有维护 ComfyUI 节点。许可证文本未锁定前不能进入 unattended 商业白名单。若人工接受并固定证据，仍应作为独立 CLI/UV 插件 A/B，重点比较 512 人脸清晰度与 MuseTalk 抖动。[代码许可证（固定 commit）](https://github.com/bytedance/LatentSync/blob/a229c3948406bc2cf6eaf4873e662e70c6a04746/LICENSE)

## 明确不进入第一版的候选

| 候选 | 原因 |
| --- | --- |
| Wan2.2-I2V-A14B / S2V-14B | 官方单卡命令要求至少 80GB；24GB/48GB 不满足已证实条件。社区量化可能可加载，但不能替代首版准入证据。[Wan 官方 README](https://github.com/Wan-Video/Wan2.2/blob/42bf4cfaa384bc21833865abc2f9e6c0e67233dc/README.md) |
| InstantID + SDXL | 虽然代码 Apache，但官方明确称发布的 checkpoint 和 InsightFace 人脸模型仅供研究、非商业；不符合面向公开发布/潜在商业内容的许可基线。[InstantID 官方声明](https://github.com/instantX-research/InstantID/blob/2145b67f9607da6234702063692330185f374486/README.md#disclaimer) |
| FLUX.2 Klein 9B/9B Base/dev | BFL 官方模型表明确为 Non-Commercial；只有 Klein 4B/4B Base 是 Apache-2.0，禁止按系列名模糊放行。[BFL 模型表（固定 commit）](https://github.com/black-forest-labs/flux2/blob/50fe5162777813d869182b139e83b10743caef15/README.md#model-overview) |
| FLUX.1-dev 及依赖它的人物插件 | BFL 官方模型表将 dev 权重列为 Non-Commercial；在未逐项核对插件、底模和人脸依赖前不准入。[BFL 官方仓库（固定 commit）](https://github.com/black-forest-labs/flux/blob/802fb4713906133fcbd0d8dc5351620ca4773036/README.md#open-weight-models) |
| Wav2Lip | 官方项目明确开源结果仅限个人、研究和非商业，商业使用严格禁止。[官方声明（固定 commit）](https://github.com/Rudrabha/Wav2Lip/blob/bac9a81e63ecc153202353372e5724b83d9e6322/README.md#license-and-citation) |
| `gpt-image-2` | 不是开源模型，且当前配置 `allow_paid_image_fallback: false`；只能以后由本地主控显式开启，不能 unattended 自动回退。 |

## 24GB 执行与卸载策略

1. **启动探测**：记录 GPU 型号、显存、驱动、CUDA、ComfyUI commit、Python/PyTorch 版本、可用磁盘、FFmpeg 版本和持久化根；不符合固定清单则阻塞。
2. **一次只运行一个阶段**：关键帧、I2V、口型、最终 FFmpeg 不并发；一个活动 Run、一个 GPU 任务。
3. **FLUX.2 Klein**：先 Base FP8 transformer + BF16 Qwen3 4B text encoder；启用 ComfyUI 原生卸载。OOM 才尝试 FP4 text encoder，尝试记录为不同 `model_variant`，结果不可混为同一基准。
4. **Wan2.2**：使用 Comfy 官方 FP16 5B + FP8 UMT5 + VAE；文本编码器放 CPU/原生卸载。不要在同一进程中保留 FLUX.2。
5. **MuseTalk**：停止 ComfyUI 队列并确认 GPU 释放后，由固定 UV 插件环境启动；只处理 5 秒口播片段。不要把它装进云镜像自带 Python。
6. **48GB**：不是自动选择“更大模型”的信号。先用同一主栈重跑基准，比较是否因减少卸载而缩短耗时/提高稳定性；只有主栈失败才测试 Qwen Edit 或 LTX 13B。
7. **缓存与磁盘**：模型按 SHA/仓库 revision 存入项目持久化模型目录，通过 `extra_model_paths` 引用。下载完成后校验官方 LFS OID/SHA256；禁止模糊 `latest`。

## 10 镜头固定基准

### 输入和控制变量

- 固定人物母版：虚构成年中国女性，正面中近景，嘴闭合，五官无遮挡，固定发型、服装、色卡和照明；不得使用真人姓名或真人参考图。
- 固定 10 份提示词、negative prompt、工作流 JSON、尺寸、帧数和 3 个预置 seed。首轮统一 seed A；仅失败镜头依次用 seed B/C，最多 3 次。
- 所有 I2V 固定为 704x1280、24fps、121 帧（约 5.04 秒）；成片需要更短镜头时由确定性剪辑取 3--5 秒。
- 不在生成画面中要求正确书名/封面文字；书籍信息由后续固定模板覆盖。

| # | 镜头 | 成片取用 / 模型生成 | 主要验证项 |
| ---: | --- | --- | --- |
| 1 | 人物正面开场，轻微呼吸和慢推镜 | 5s / 121 帧 | 人脸稳定、闭口母版、低运动 I2V、中文口型 |
| 2 | 雨夜窗边书桌，书页与杯中热气 | 4s / 121 帧 | 写实光影、细小运动、竖屏构图 |
| 3 | 手翻开无可辨文字的书 | 3s / 121 帧 | 手指、书页物理、近景细节 |
| 4 | 图书馆过道缓慢前移 | 5s / 121 帧 | 长镜头、透视、直线稳定、相机运动 |
| 5 | 清晨通勤者在车窗边阅读，不出现主角脸 | 5s / 121 帧 | 多物体、反射、环境运动 |
| 6 | 夜间台灯下的笔记与铅笔 | 3s / 121 帧 | 俯拍、物体边缘、低照度噪点 |
| 7 | 城市天台远景与翻动的外套下摆 | 4s / 121 帧 | 人物小尺度、风、背景稳定 |
| 8 | 书架前取书，只显示手臂与背影 | 5s / 121 帧 | 遮挡、肢体、书脊伪文字控制 |
| 9 | 主角参考组编辑出的 3/4 角度低运动镜头 | 4s / 121 帧 | 跨关键帧身份、侧脸边界 |
| 10 | 主角正面结尾，轻微点头和慢拉镜 | 5s / 121 帧 | 与镜头 1 的身份一致、中文口型、首尾一致性 |

### 自动证据

每次尝试必须保存，不依赖 `done/passed` 状态：

- 输入关键帧、WAV、提示词、seed、完整 ComfyUI workflow/CLI 参数及其 SHA256。
- 模型文件相对路径、字节数、SHA256/LFS OID、模型 revision、代码/node commit、许可证快照。
- `nvidia-smi` 起止快照、峰值显存（可采样）、墙钟耗时、退出码、OOM/节点错误日志。
- `ffprobe` 的宽高、帧率、帧数、时长、视频/音频 codec 和可解码结果。
- 口型镜头的输入台词、Whisper 回转写、书名/作者关键词命中；若后续批准独立口型评估器，再保存其版本、许可证和原始分数。阈值只能在首轮真实样本分布后冻结，不能现在虚构。

### 人工/本地视觉评分

每个镜头按以下六项 0/1 判断：主体与提示相符、无致命人脸/肢体错误、时间连续、相机运动合理、竖屏安全区可用、没有无法被模板遮盖的伪文字/水印。镜头 1、9、10 另加“人物身份与母版一致”；镜头 1、10 另加“口型主观同步、无嘴部闪烁”。任一致命项为 0 即该尝试不可用。

**通过线**：10 个镜头中至少 7 个在最多 3 次内得到可用结果；镜头 1 和 10 必须都通过；单任务不超过 45 分钟；整个基准累计 GPU 时间达到 240 分钟立即停止并报告，不为了凑 70% 绕过预算。重试只换预置 seed，不修改提示词；否则无法比较模型稳定性。

通过后再做第二轮“生产提示词优化”，它不是模型准入基准的一部分。

## 准入决定

第一台 24GB 实例应按以下顺序验证：

1. ComfyUI 原生 FLUX.2 Klein 4B Base FP8 生成标准人物参考组和 10 张关键帧；确认多参考编辑的一致性是否足够。
2. ComfyUI 原生 Wan2.2 TI2V-5B 用固定 121 帧跑 10 镜头。
3. 释放 ComfyUI GPU 后，用独立 UV 插件环境跑 MuseTalk 1.5 的镜头 1、10。
4. 达到 70% 且两个口播镜头必过，锁定三模型 revision、文件哈希、工作流和环境清单。
5. 若仅人物一致性失败，先在 48GB 测 Qwen-Image-2512 + Edit-2511；若仅视频运动失败，A/B LTX-Video；若仅口型失败，锁定权重许可后测 LatentSync 1.6。不要同时替换多个阶段，否则无法定位最早失败 Gate。

因此，模板目前可以把首选模型名写入“候选/待基准”清单，但在真实租赁 GPU 完成上述测试前，不能标记为 `approved`，也不能承诺 unattended 生产质量。
