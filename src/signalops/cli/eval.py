"""Evaluation CLI commands."""

from __future__ import annotations

import click


@click.group("eval")
def eval_group() -> None:
    """Evaluate judge models against test sets."""
