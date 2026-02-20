"""Run judge command — judges relevance of collected tweets."""

import click

from signalops.cli.collect import run_group


@run_group.command("judge")
@click.pass_context
def judge_cmd(ctx):
    """Judge relevance of collected tweets."""
    from signalops.cli.project import load_active_config
    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import get_engine, get_session, init_db

    console = ctx.obj["console"]
    config = load_active_config(ctx)
    dry_run = ctx.obj["dry_run"]

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    # Lazy imports for pipeline stages

    from signalops.models.judge_model import LLMPromptJudge
    from signalops.models.llm_gateway import LLMGateway
    from signalops.pipeline.judge import JudgeStage

    gateway = LLMGateway()
    model_id = config.llm.get("judge_model", "claude-sonnet-4-6")
    judge = LLMPromptJudge(gateway=gateway, model_id=model_id)
    judge_stage = JudgeStage(judge=judge, db_session=session)

    if dry_run:
        console.print("[yellow][DRY RUN] Would judge unjudged normalized posts")
        session.close()
        return

    result = judge_stage.run(project_id=config.project_id, config=config, dry_run=dry_run)

    relevant = result.get("relevant", 0)
    irrelevant = result.get("irrelevant", 0)
    maybe = result.get("maybe", 0)
    total = relevant + irrelevant + maybe

    console.print(
        f"[green]Judged {total} posts: "
        f"Relevant: {relevant} | Irrelevant: {irrelevant} | Maybe: {maybe}"
    )
    session.close()
