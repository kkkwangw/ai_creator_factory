# GPU 规则

- 首选租赁单卡 24GB，48GB 只作受控对照；硬件必须运行时探测，禁止写死型号。
- 模型只有 `candidate` 和 `approved` 两类。用户指定的新模型仍从 `candidate` 开始。
- 准入必须固定仓库 revision、文件哈希、许可证、工作流和环境清单，并通过 10 镜头基准。
- 默认候选为 FLUX.2 Klein 4B Base FP8、Wan2.2-TI2V-5B、MuseTalk 1.5。
- 三个阶段严格串行；每阶段结束后释放模型并验证 GPU 空闲。
- 每任务最多 45 分钟、每 Run 最多 240 GPU 分钟、每任务最多 3 次尝试。
- 首次模型 Bootstrap 最多 120 分钟，开始前至少 100 GiB 持久化空间；Run 前至少 30 GiB。
- OOM 只能采用已记录的批准降级变体，不能自动下载未知量化包或同时替换多个阶段。
- ComfyUI 可切换批准 commit、配置模型路径和固定轻量节点；禁止自动替换驱动、CUDA、
  PyTorch 或镜像核心 GPU 运行时。
- 模型只从批准的官方 GitHub、Hugging Face 或可校验 ModelScope 来源下载。
