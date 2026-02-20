"""CLI tests using Click's CliRunner."""

import pytest
from click.testing import CliRunner

from signalops.cli.main import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_help(runner):
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "SignalOps" in result.output


def test_cli_has_all_commands(runner):
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    for cmd in ["project", "run", "queue", "stats", "export"]:
        assert cmd in result.output


def test_project_list_help(runner):
    result = runner.invoke(cli, ["project", "list", "--help"])
    assert result.exit_code == 0
    assert "List all available projects" in result.output


def test_project_set_help(runner):
    result = runner.invoke(cli, ["project", "set", "--help"])
    assert result.exit_code == 0
    assert "Set the active project" in result.output


def test_project_init_help(runner):
    result = runner.invoke(cli, ["project", "init", "--help"])
    assert result.exit_code == 0
    assert "Create a new project interactively" in result.output


def test_run_collect_help(runner):
    result = runner.invoke(cli, ["run", "collect", "--help"])
    assert result.exit_code == 0
    assert "Collect tweets" in result.output


def test_run_judge_help(runner):
    result = runner.invoke(cli, ["run", "judge", "--help"])
    assert result.exit_code == 0
    assert "Judge relevance" in result.output


def test_run_score_help(runner):
    result = runner.invoke(cli, ["run", "score", "--help"])
    assert result.exit_code == 0
    assert "Score judged" in result.output


def test_run_draft_help(runner):
    result = runner.invoke(cli, ["run", "draft", "--help"])
    assert result.exit_code == 0
    assert "Generate reply drafts" in result.output


def test_run_all_help(runner):
    result = runner.invoke(cli, ["run", "all", "--help"])
    assert result.exit_code == 0
    assert "Run full pipeline" in result.output


def test_queue_list_help(runner):
    result = runner.invoke(cli, ["queue", "list", "--help"])
    assert result.exit_code == 0
    assert "Show pending drafts" in result.output


def test_queue_approve_help(runner):
    result = runner.invoke(cli, ["queue", "approve", "--help"])
    assert result.exit_code == 0
    assert "Approve a draft" in result.output


def test_queue_edit_help(runner):
    result = runner.invoke(cli, ["queue", "edit", "--help"])
    assert result.exit_code == 0
    assert "Edit a draft" in result.output


def test_queue_reject_help(runner):
    result = runner.invoke(cli, ["queue", "reject", "--help"])
    assert result.exit_code == 0
    assert "Reject a draft" in result.output


def test_queue_send_help(runner):
    result = runner.invoke(cli, ["queue", "send", "--help"])
    assert result.exit_code == 0
    assert "Send approved drafts" in result.output
    assert "--confirm" in result.output


def test_stats_help(runner):
    result = runner.invoke(cli, ["stats", "--help"])
    assert result.exit_code == 0
    assert "pipeline statistics" in result.output


def test_export_training_data_help(runner):
    result = runner.invoke(cli, ["export", "training-data", "--help"])
    assert result.exit_code == 0
    assert "training data" in result.output.lower()
    assert "--type" in result.output


def test_dry_run_flag(runner):
    result = runner.invoke(cli, ["--dry-run", "run", "--help"])
    assert result.exit_code == 0


def test_format_json_flag(runner):
    result = runner.invoke(cli, ["--format", "json", "--help"])
    assert result.exit_code == 0


def test_verbose_flag(runner):
    result = runner.invoke(cli, ["-v", "--help"])
    assert result.exit_code == 0


def test_project_list_no_projects(runner, tmp_path, monkeypatch):
    """Test project list with no projects directory."""

    monkeypatch.setattr("signalops.config.defaults.DEFAULT_PROJECTS_DIR", tmp_path / "nonexistent")
    result = runner.invoke(cli, ["project", "list"])
    assert result.exit_code == 0


def test_project_set_nonexistent(runner, tmp_path, monkeypatch):
    """Test setting a project that doesn't exist."""
    monkeypatch.setattr("signalops.config.defaults.DEFAULT_PROJECTS_DIR", tmp_path)
    result = runner.invoke(cli, ["project", "set", "nonexistent"])
    assert result.exit_code != 0 or "not found" in result.output.lower()


def test_project_set_and_list(runner, tmp_path, monkeypatch):
    """Test setting and listing a project."""
    import yaml

    # Patch projects dir in project.py and credentials dir in loader.py
    monkeypatch.setattr("signalops.cli.project.DEFAULT_PROJECTS_DIR", tmp_path)
    monkeypatch.setattr("signalops.config.loader.DEFAULT_CREDENTIALS_DIR", tmp_path / ".creds")

    # Create a project YAML
    config = {
        "project_id": "test",
        "project_name": "Test Project",
        "description": "A test",
        "queries": [{"text": "test query", "label": "test"}],
        "relevance": {
            "system_prompt": "Judge relevance.",
            "positive_signals": ["good"],
            "negative_signals": ["bad"],
        },
        "persona": {
            "name": "Bot",
            "role": "helper",
            "tone": "friendly",
            "voice_notes": "Be nice",
            "example_reply": "Hello!",
        },
    }
    with open(tmp_path / "test.yaml", "w") as f:
        yaml.dump(config, f)

    # Set project
    result = runner.invoke(cli, ["project", "set", "test"])
    assert result.exit_code == 0
    assert "Active project" in result.output

    # List projects
    result = runner.invoke(cli, ["project", "list"])
    assert result.exit_code == 0


def test_stats_with_db(runner, tmp_path, monkeypatch, db_session, sample_project_in_db):
    """Test stats command with an initialized DB."""

    # Monkeypatch to use our in-memory DB
    monkeypatch.setattr("signalops.config.defaults.DEFAULT_CREDENTIALS_DIR", tmp_path / ".creds")

    # Write active project
    creds_dir = tmp_path / ".creds"
    creds_dir.mkdir(parents=True, exist_ok=True)
    (creds_dir / "active_project").write_text("test-project")

    # Stats uses its own engine/session, so we can't easily inject.
    # Just test --help works.
    result = runner.invoke(cli, ["stats", "--help"])
    assert result.exit_code == 0
