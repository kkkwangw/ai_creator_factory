# AI Creator Factory

[English](README.md) | [简体中文](README.zh-CN.md)

AI Creator Factory is a personal AI creation template. Its first version focuses on one auditable
vertical workflow:

```text
One book -> one project directory -> one 45-60 second vertical book-recommendation video
```

This is not a SaaS platform and is not tied to OpenAI, Claude, ComfyUI, or any single model.
External capabilities enter through project-local Skills, plugins, or infrastructure adapters.
Candidate models must pass a real rented-GPU benchmark before they can be approved.

## First-Version Scope

- Book data: local Tencent WeChat Reading Skill; book title is required.
- Script and shot plan: local Codex, targeting Chinese short-video viewers aged 20-40 by default.
- Narration: local MiMo V2.5 TTS using the fixed "Bingtang" voice; WAV is the master timeline.
- Image candidate: FLUX.2 Klein 4B Base FP8.
- Image-to-video candidate: Wan2.2-TI2V-5B at 704x1280, 24fps, 121 frames.
- Lip-sync candidate: MuseTalk 1.5 in an isolated remote UV environment.
- Composition: remote FFmpeg with `book-list-v1`, ASS subtitles, and H.264/AAC output.
- Delivery: final video, 1080x1920 cover, release copy, and evidence manifest; no auto-publishing.

All models currently remain `candidate`. Without a real 24 GB GPU benchmark, this template must not
claim production video capability. See
[open-video-model-stack.md](docs/research/open-video-model-stack.md) for admission criteria.

## Local and Remote Roles

The local machine runs Codex, WeChat Reading, MiMo, Whisper, deployment tools, and control Markdown.
The remote machine runs the preinstalled ComfyUI environment, approved open models, MuseTalk,
FFmpeg, and a deterministic Runner. Codex is never installed or run remotely.

Local scripts use only the existing Conda `codex` environment with Python 3.11:

```bash
conda run -n codex python scripts/validate_project.py
conda run -n codex python -m pytest
conda run -n codex ruff check .
```

Do not use the system Python 3.9 or install packages into it. When SSH/SFTP is actually needed, the
optional dependency may only be installed in Conda `codex`:

```bash
conda run -n codex python -m pip install -e '.[ssh]'
```

Do not install it before SSH is needed. Do not install models or heavyweight generation dependencies
during template initialization.

## Create an Actual Project

1. Copy the complete template directory without copying `.git/`.
2. Let local Codex initialize `PROJECT.md`, `TODO.md`, `memory/CURRENT.md`, and the first task.
3. Configure machine-local tool paths in `.local/tools.toml` and credentials in local `.env`.
4. Explicitly copy an approved character pack from a previous project; no global character library.
5. Lock `template_version` once production starts. Upgrades require a generated diff and manual file
   selection.

An actual project does not require Git. Local and remote directory structures are identical, while
models, caches, runtime artifacts, and machine-local configuration are never automatically synced.

## Control Files

- `PROJECT.md`: stable project facts and locked template version.
- `TODO.md`: compact task index plus non-authoritative current task/run pointers.
- `tasks/<task-id>.md`: planned work, writable only by local Codex.
- `memory/CURRENT.md`: bounded handoff snapshot; at most 20 historical snapshots.
- `config/`: machine-independent production policies, model candidates, and fixed templates.
- `deployments/`: explicit deployment manifests and receipts; recursive upload is forbidden.
- `runs/`: remote task JSON, logs, evidence, and staged artifacts.
- `deliverables/current/`: atomically activated current delivery.

## Available Tools

- `scripts/validate_project.py`: validate control-file limits, identity, and base configuration.
- `scripts/build_task_envelope.py`: compile task Markdown frontmatter into immutable JSON.
- `scripts/build_deployment_manifest.py`: create a SHA-256 deployment manifest from explicit files.
- `scripts/verify_delivery.py`: verify current files, hashes, and partial ffprobe specifications. It does
  not claim `ready_for_download` until the Runner and Gate 1-6 revalidators exist.
- `scripts/doctor.py`: read-only inspection of Python, FFmpeg, Whisper, UV, and GPU tools.
- `scripts/transfer.py`: manifest-bound SSH/SFTP transfer through optional Paramiko.

See `deployments/plan.example.json` for upload planning and `deployments/download.example.json` for
download specifications. Both operate on explicit files only and never scan or recursively transfer
directories.

The remote Runner and ComfyUI/MuseTalk production adapters still require implementation and a real
rented-instance benchmark. Current scripts never use placeholder output to report false success.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Video workflow](docs/WORKFLOW.md)
- [Remote runbook](docs/REMOTE_RUNBOOK.md)
- [Complete project structure](docs/PROJECT_STRUCTURE.md)
- [Architecture decisions](docs/DECISIONS.md)
