"""Smoke tests for provider-neutral contracts."""

from core.config import Settings
from core.plugin_manager import ApprovalStatus, PluginKind, PluginMetadata
from workflow.task import Task, TaskStatus


def test_default_settings_are_project_local() -> None:
    settings = Settings.from_environment({})

    assert settings.environment == "development"
    assert str(settings.output_dir) == "outputs"


def test_plugin_defaults_to_unapproved() -> None:
    metadata = PluginMetadata(name="example", kind=PluginKind.VIDEO, version="0.1.0")

    assert metadata.approval_status is ApprovalStatus.PLANNED
    assert metadata.kind is PluginKind.VIDEO


def test_task_starts_as_declarative_input() -> None:
    task = Task(name="draft", capability="content.plan")

    assert task.task_id
    assert TaskStatus.PENDING.value == "pending"
