"""Detached remote task processes with exact identity verification."""

from __future__ import annotations

import json
import os
import signal
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from workflow.task import TaskIdentity, validate_identifier


@dataclass(frozen=True)
class ProcessRecord:
    """Evidence needed to query or cancel one detached Linux process group."""

    identity: TaskIdentity
    attempt_id: str
    pid: int
    process_group_id: int
    process_start_ticks: int
    command_token: str

    def __post_init__(self) -> None:
        validate_identifier(self.attempt_id, field_name="attempt_id")
        if self.pid <= 0 or self.process_group_id <= 0 or self.process_start_ticks <= 0:
            raise ValueError("process identifiers and start ticks must be positive")

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible record."""
        value = asdict(self)
        value["identity"] = self.identity.as_dict()
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> ProcessRecord:
        """Create a record from decoded JSON."""
        identity_value = value["identity"]
        if not isinstance(identity_value, Mapping):
            raise ValueError("identity must be an object")
        return cls(
            identity=TaskIdentity(
                run_id=str(identity_value["run_id"]),
                task_id=str(identity_value["task_id"]),
                prompt_id=str(identity_value["prompt_id"]),
            ),
            attempt_id=str(value["attempt_id"]),
            pid=int(value["pid"]),
            process_group_id=int(value["process_group_id"]),
            process_start_ticks=int(value["process_start_ticks"]),
            command_token=str(value["command_token"]),
        )


def linux_process_start_ticks(pid: int) -> int:
    """Read Linux `/proc/<pid>/stat` starttime (field 22)."""
    raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    closing = raw.rfind(")")
    if closing < 0:
        raise ValueError("malformed /proc stat record")
    fields_after_comm = raw[closing + 2 :].split()
    return int(fields_after_comm[19])


def linux_process_cmdline(pid: int) -> tuple[str, ...]:
    """Read a Linux process command line as separate arguments."""
    raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    return tuple(part.decode("utf-8", errors="replace") for part in raw.split(b"\0") if part)


def spawn_detached(
    *,
    command: Sequence[str],
    identity: TaskIdentity,
    attempt_id: str,
    command_token: str,
    cwd: Path,
    log_path: Path,
    record_path: Path,
    environment: Mapping[str, str] | None = None,
) -> ProcessRecord:
    """Start a fixed worker command in a new session and persist its identity record."""
    validate_identifier(attempt_id, field_name="attempt_id")
    if not command or command_token not in command:
        raise ValueError("fixed command_token must appear as one complete command argument")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("ab", buffering=0) as log:
        process = subprocess.Popen(
            list(command),
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
            env=dict(environment) if environment is not None else None,
        )
    record = ProcessRecord(
        identity=identity,
        attempt_id=attempt_id,
        pid=process.pid,
        process_group_id=os.getpgid(process.pid),
        process_start_ticks=linux_process_start_ticks(process.pid),
        command_token=command_token,
    )
    temporary = record_path.with_suffix(f"{record_path.suffix}.tmp")
    temporary.write_text(
        json.dumps(record.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(record_path)
    return record


def verify_exact_process(record: ProcessRecord, expected: TaskIdentity) -> None:
    """Verify PID reuse, process group, command token, and the exact task identity."""
    if record.identity != expected:
        raise ValueError("requested identity does not match process record")
    if linux_process_start_ticks(record.pid) != record.process_start_ticks:
        raise ValueError("PID was reused or process start time changed")
    if os.getpgid(record.pid) != record.process_group_id:
        raise ValueError("process group does not match record")
    cmdline = linux_process_cmdline(record.pid)
    required = {
        record.command_token,
        expected.run_id,
        expected.task_id,
        expected.prompt_id,
        record.attempt_id,
    }
    if not required.issubset(set(cmdline)):
        raise ValueError("live process command does not contain the exact recorded identity")


def cancel_exact_process(record: ProcessRecord, expected: TaskIdentity) -> None:
    """Send SIGTERM only after exact process identity verification."""
    verify_exact_process(record, expected)
    os.killpg(record.process_group_id, signal.SIGTERM)
