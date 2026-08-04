"""Linux-only detached process identity and cancellation helpers."""

from remote.process import ProcessRecord, cancel_exact_process, spawn_detached

__all__ = ["ProcessRecord", "cancel_exact_process", "spawn_detached"]
