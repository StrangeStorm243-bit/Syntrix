# Syntrix Final Scope — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship Syntrix as a complete open-source product with DM outreach, auto-scheduled pipeline, and a polished landing page that guides users to self-host via Docker Compose.

**Architecture:** Three independent workstreams with zero file overlap. T1 adds DM as a new sequence action type. T2 adds auto-pipeline scheduling via APScheduler. T3 updates the Next.js landing page content to reflect Docker-first setup and new features.

**Tech Stack:** Python 3.11+, SQLAlchemy, twikit, APScheduler, FastAPI, React 19, Next.js 16, Tailwind CSS 4

---

## Terminal 1: DM Feature (Backend + Frontend)

Files touched: `src/signalops/connectors/base.py`, `src/signalops/connectors/twikit_connector.py`, `src/signalops/pipeline/sequence_engine.py`, `src/signalops/config/schema.py`, `dashboard/src/pages/Onboarding.tsx`, `tests/unit/test_twikit_connector.py`, `tests/unit/test_sequence_engine.py`

---

### Task 1: Add send_dm to Connector ABC

**Files:**
- Modify: `src/signalops/connectors/base.py:74-86`
- Test: `tests/unit/test_twikit_connector.py`

**Step 1: Add send_dm abstract method to Connector ABC**

In `src/signalops/connectors/base.py`, add after the `follow` method (line 82) and before `health_check`:

```python
    @abstractmethod
    def send_dm(self, user_id: str, text: str) -> bool:
        """Send a direct message to a user. Returns True if successful."""
        ...
```

**Step 2: Verify mypy passes**

Run: `cd /c/GitHubProjects/Syntrix && python -m mypy src/signalops/connectors/base.py --strict`
Expected: FAIL — subclasses don't implement `send_dm` yet (that's OK, we fix in next task)

**Step 3: Commit**

```bash
git add src/signalops/connectors/base.py
git commit -m "feat: add send_dm to Connector ABC"
```

---

### Task 2: Implement send_dm in TwikitConnector

**Files:**
- Modify: `src/signalops/connectors/twikit_connector.py:154-158`
- Test: `tests/unit/test_twikit_connector.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_twikit_connector.py` in `TestTwikitConnector`:

```python
    def test_send_dm_success(self) -> None:
        """send_dm() should call client.send_dm and return True."""
        connector = TwikitConnector(username="test", password="pass")
        mock_client = MagicMock()
        mock_client.send_dm = AsyncMock(return_value=MagicMock())
        connector._client = mock_client
        connector._logged_in = True

        result = connector.send_dm("user123", "Hey, check this out!")
        assert result is True
        mock_client.send_dm.assert_called_once_with("user123", "Hey, check this out!")

    def test_send_dm_failure(self) -> None:
        """send_dm() should return False on failure."""
        connector = TwikitConnector(username="test", password="pass")
        mock_client = MagicMock()
        mock_client.send_dm = AsyncMock(side_effect=Exception("DM failed"))
        connector._client = mock_client
        connector._logged_in = True

        result = connector.send_dm("user123", "Hello")
        assert result is False
```

**Step 2: Run tests to verify they fail**

Run: `cd /c/GitHubProjects/Syntrix && python -m pytest tests/unit/test_twikit_connector.py::TestTwikitConnector::test_send_dm_success tests/unit/test_twikit_connector.py::TestTwikitConnector::test_send_dm_failure -v`
Expected: FAIL — `send_dm` not defined

**Step 3: Implement send_dm in TwikitConnector**

Add after the `follow` method (line 154) and before `health_check`:

```python
    def send_dm(self, user_id: str, text: str) -> bool:
        """Send a direct message to a user."""
        client = self._ensure_client()
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(client.send_dm(user_id, text))
            return True
        except Exception:  # noqa: BLE001
            logger.warning("Failed to send DM to user %s", user_id)
            return False
        finally:
            loop.close()
```

**Step 4: Run tests to verify they pass**

Run: `cd /c/GitHubProjects/Syntrix && python -m pytest tests/unit/test_twikit_connector.py::TestTwikitConnector::test_send_dm_success tests/unit/test_twikit_connector.py::TestTwikitConnector::test_send_dm_failure -v`
Expected: PASS

**Step 5: Add send_dm stub to other connectors**

In `src/signalops/connectors/x_api.py`, add to the XApiConnector class:

```python
    def send_dm(self, user_id: str, text: str) -> bool:
        """Send DM — not supported via X API v2 free tier."""
        raise NotImplementedError("DMs require twikit connector")
```

In `src/signalops/connectors/linkedin.py`, add to LinkedInConnector class:

```python
    def send_dm(self, user_id: str, text: str) -> bool:
        """Send DM — not supported for LinkedIn."""
        raise NotImplementedError("LinkedIn DMs not supported")
```

**Step 6: Verify mypy passes**

Run: `cd /c/GitHubProjects/Syntrix && python -m mypy src/signalops/connectors/ --strict`
Expected: PASS

**Step 7: Commit**

```bash
git add src/signalops/connectors/twikit_connector.py src/signalops/connectors/x_api.py src/signalops/connectors/linkedin.py tests/unit/test_twikit_connector.py
git commit -m "feat: implement send_dm in TwikitConnector"
```

---

### Task 3: Add DM action type to sequence engine

**Files:**
- Modify: `src/signalops/pipeline/sequence_engine.py:27-30,192-215`
- Modify: `src/signalops/config/schema.py:201`
- Test: `tests/unit/test_sequence_engine.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_sequence_engine.py`:

```python
    def test_dm_step_executes(self) -> None:
        """DM action type should call connector.send_dm."""
        connector = _make_connector()
        connector.send_dm = MagicMock(return_value=True)
        engine = SequenceEngine(self.session, connector)

        # Create a DM-only sequence
        seq = Sequence(project_id="test", name="Cold DM")
        self.session.add(seq)
        self.session.flush()
        self.session.add(
            SequenceStep(
                sequence_id=seq.id,
                step_order=1,
                action_type="dm",
                delay_hours=0,
                config_json='{"dm_text": "Hey, saw your tweet and wanted to reach out!"}',
            ),
        )
        self.session.commit()

        enrollment = engine.enroll(self.norm_id, seq.id, "test")
        enrollment.next_step_at = datetime.now(UTC) - timedelta(minutes=1)
        self.session.commit()

        count = engine.execute_due_steps()
        assert count == 1
        connector.send_dm.assert_called_once()

    def test_dm_rate_limit(self) -> None:
        """DM actions should respect max_dms_per_day rate limit."""
        connector = _make_connector()
        connector.send_dm = MagicMock(return_value=True)
        engine = SequenceEngine(self.session, connector, max_dms_per_day=1)

        seq = Sequence(project_id="test", name="DM Seq")
        self.session.add(seq)
        self.session.flush()
        self.session.add(
            SequenceStep(
                sequence_id=seq.id,
                step_order=1,
                action_type="dm",
                delay_hours=0,
            ),
        )
        self.session.commit()

        # Seed one existing DM execution in the last 24h
        enrollment_prev = engine.enroll(self.norm_id, seq.id, "test")
        exec_record = StepExecution(
            enrollment_id=enrollment_prev.id,
            step_id=1,
            action_type="dm",
            status="executed",
            executed_at=datetime.now(UTC) - timedelta(hours=1),
        )
        self.session.add(exec_record)
        self.session.commit()

        # Create a second normalized post for the new enrollment
        raw2 = RawPost(project_id="test", platform="x", platform_id="tw2", raw_json={})
        self.session.add(raw2)
        self.session.flush()
        norm2 = NormalizedPost(
            raw_post_id=raw2.id,
            project_id="test",
            platform="x",
            platform_id="tw2",
            author_id="u2",
            author_username="user2",
            text_original="Help",
            text_cleaned="Help",
            created_at=datetime.now(UTC),
        )
        self.session.add(norm2)
        self.session.flush()

        enrollment_new = engine.enroll(norm2.id, seq.id, "test")
        enrollment_new.next_step_at = datetime.now(UTC) - timedelta(minutes=1)
        self.session.commit()

        count = engine.execute_due_steps()
        assert count == 0  # Rate limited
```

**Step 2: Run tests to verify they fail**

Run: `cd /c/GitHubProjects/Syntrix && python -m pytest tests/unit/test_sequence_engine.py::TestSequenceEngine::test_dm_step_executes tests/unit/test_sequence_engine.py::TestSequenceEngine::test_dm_rate_limit -v`
Expected: FAIL

**Step 3: Implement DM support in sequence engine**

In `src/signalops/pipeline/sequence_engine.py`:

Add default constant at line 30 (after `DEFAULT_MAX_REPLIES_PER_DAY`):

```python
DEFAULT_MAX_DMS_PER_DAY = 20
```

Add `max_dms_per_day` parameter to `__init__`:

```python
    def __init__(
        self,
        session: Session,
        connector: Any,
        max_likes_per_hour: int = DEFAULT_MAX_LIKES_PER_HOUR,
        max_follows_per_hour: int = DEFAULT_MAX_FOLLOWS_PER_HOUR,
        max_replies_per_day: int = DEFAULT_MAX_REPLIES_PER_DAY,
        max_dms_per_day: int = DEFAULT_MAX_DMS_PER_DAY,
    ) -> None:
        self.session = session
        self.connector = connector
        self.max_likes_per_hour = max_likes_per_hour
        self.max_follows_per_hour = max_follows_per_hour
        self.max_replies_per_day = max_replies_per_day
        self.max_dms_per_day = max_dms_per_day
```

Add DM rate limit check in `_check_rate_limit` (after the "reply" elif block):

```python
        elif action_type == "dm":
            one_day_ago = now - timedelta(days=1)
            count = (
                self.session.query(StepExecution)
                .filter(
                    StepExecution.action_type == "dm",
                    StepExecution.status == "executed",
                    StepExecution.executed_at >= one_day_ago,
                )
                .count()
            )
            if count >= self.max_dms_per_day:
                logger.warning(
                    "Rate limit: %d/%d DMs in last day",
                    count,
                    self.max_dms_per_day,
                )
                return False
```

Add DM execution in `_execute_step` (after the "check_response" elif block, before `# Record execution`):

```python
        elif step.action_type == "dm":
            # Use config_json for DM text, or fall back to a default
            config = json.loads(step.config_json or "{}")
            dm_text = config.get("dm_text", "")
            if not dm_text:
                # Try to use the approved draft text as the DM content
                draft = self._get_approved_draft(enrollment)
                if draft:
                    dm_text = draft.text_final or draft.text_generated
                else:
                    dm_text = "Hey, I saw your tweet and wanted to connect!"
            success = self.connector.send_dm(post.author_id, dm_text)
            result = {"dm_sent": success, "user_id": post.author_id, "text": dm_text}
```

**Step 4: Add max_dms_per_day to config schema**

In `src/signalops/config/schema.py`, update the `rate_limits` default in `ProjectConfig` (line 201):

```python
    rate_limits: dict[str, Any] = {
        "max_replies_per_hour": 5,
        "max_replies_per_day": 20,
        "max_dms_per_day": 20,
    }
```

**Step 5: Run tests to verify they pass**

Run: `cd /c/GitHubProjects/Syntrix && python -m pytest tests/unit/test_sequence_engine.py -v`
Expected: ALL PASS

**Step 6: Run mypy**

Run: `cd /c/GitHubProjects/Syntrix && python -m mypy src/signalops/pipeline/sequence_engine.py src/signalops/config/schema.py --strict`
Expected: PASS

**Step 7: Commit**

```bash
git add src/signalops/pipeline/sequence_engine.py src/signalops/config/schema.py tests/unit/test_sequence_engine.py
git commit -m "feat: add DM action type to sequence engine with rate limiting"
```

---

### Task 4: Update wizard sequence templates with DM steps

**Files:**
- Modify: `dashboard/src/pages/Onboarding.tsx:57-76`

**Step 1: Update SEQUENCE_TEMPLATES**

Replace the `SEQUENCE_TEMPLATES` array in `Onboarding.tsx`:

```typescript
const SEQUENCE_TEMPLATES = [
  {
    id: 'engage-then-pitch',
    name: 'Engage Then Pitch',
    description: 'Like their tweet, reply with value, then follow up with a DM after engagement.',
    steps: ['Like Tweet', 'Value Reply', 'Follow', 'DM Follow-Up'],
  },
  {
    id: 'direct-value',
    name: 'Direct Value',
    description: 'Lead with a helpful reply that naturally mentions your product, then DM after engagement.',
    steps: ['Value Reply', 'Check Engagement', 'DM Resource'],
  },
  {
    id: 'relationship-first',
    name: 'Relationship First',
    description: 'Build genuine rapport over multiple interactions before any mention of your product.',
    steps: ['Like Tweet', 'Thoughtful Reply', 'Follow', 'Engage Again', 'DM Soft Pitch'],
  },
  {
    id: 'cold-dm',
    name: 'Cold DM',
    description: 'Send a direct message immediately after finding a relevant lead. Lands in message requests for non-followers.',
    steps: ['DM Outreach'],
  },
];
```

**Step 2: Verify TypeScript compiles**

Run: `cd /c/GitHubProjects/Syntrix/dashboard && npx tsc --noEmit`
Expected: PASS

**Step 3: Commit**

```bash
git add dashboard/src/pages/Onboarding.tsx
git commit -m "feat: add DM steps to wizard sequence templates"
```

---

### Task 5: Update default sequences in engine to include DM

**Files:**
- Modify: `src/signalops/pipeline/sequence_engine.py:274-378`

**Step 1: Update create_default_sequences**

Replace the `create_default_sequences` method body to add DM steps to existing sequences and add a "Cold DM" sequence:

Add DM step to the "Full Sequence" (after check_response step, as step 6):

```python
                SequenceStep(
                    sequence_id=full.id,
                    step_order=6,
                    action_type="dm",
                    delay_hours=24,
                    config_json='{"dm_text": ""}',
                ),
```

Update Full Sequence description:

```python
        full = Sequence(
            project_id=project_id,
            name="Full Sequence",
            description="Like -> Follow -> Wait -> Reply -> Check -> DM",
        )
```

Add a new "Cold DM" sequence after the Full Sequence block:

```python
        # Cold DM
        cold_dm = Sequence(
            project_id=project_id,
            name="Cold DM",
            description="Direct message immediately",
        )
        self.session.add(cold_dm)
        self.session.flush()
        self.session.add_all(
            [
                SequenceStep(
                    sequence_id=cold_dm.id,
                    step_order=1,
                    action_type="dm",
                    delay_hours=0,
                    config_json='{"dm_text": ""}',
                ),
            ]
        )
        sequences.append(cold_dm)
```

**Step 2: Run tests**

Run: `cd /c/GitHubProjects/Syntrix && python -m pytest tests/unit/test_sequence_engine.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add src/signalops/pipeline/sequence_engine.py
git commit -m "feat: add Cold DM sequence and DM step to Full Sequence"
```

---

## Terminal 2: Auto-Scheduled Pipeline + Settings

Files touched: `src/signalops/api/app.py`, `src/signalops/api/routes/setup.py`, `dashboard/src/pages/Settings.tsx`, `dashboard/src/hooks/useSetup.ts`

---

### Task 6: Add pipeline auto-run scheduler

**Files:**
- Modify: `src/signalops/api/app.py:29-75`

**Step 1: Add _run_pipeline_tick function**

Add after the `_tick_sequences` function (before the `lifespan` function):

```python
def _run_pipeline_tick(db_url: str) -> None:
    """Auto-run the pipeline for the active project (called by APScheduler)."""
    try:
        from signalops.config.loader import load_project
        from signalops.connectors.factory import ConnectorFactory
        from signalops.models.draft_model import LLMDraftGenerator
        from signalops.models.judge_model import LLMPromptJudge
        from signalops.models.llm_gateway import LLMGateway
        from signalops.pipeline.orchestrator import PipelineOrchestrator
        from signalops.storage.database import Project
        from signalops.storage.database import get_engine as _get_engine
        from signalops.storage.database import get_session

        engine = _get_engine(db_url)
        session = get_session(engine)
        try:
            project = session.query(Project).filter(Project.is_active.is_(True)).first()
            if not project:
                return
            config = load_project(str(project.config_path))
            factory = ConnectorFactory()
            connector = factory.create("x", config)
            gateway = LLMGateway()
            judge = LLMPromptJudge(gateway=gateway, model=config.llm.judge_model)
            drafter = LLMDraftGenerator(gateway=gateway, model=config.llm.draft_model)
            orchestrator = PipelineOrchestrator(
                db_session=session,
                connector=connector,
                judge=judge,
                draft_generator=drafter,
            )
            results = orchestrator.run_all(config)
            logger.info("Auto pipeline completed: %s", results)
        finally:
            session.close()
            engine.dispose()
    except Exception:  # noqa: BLE001
        logger.debug("Pipeline tick skipped — no project or connector not configured")
```

**Step 2: Add the scheduler job in lifespan**

In the `lifespan` function, after the sequence tick `scheduler.add_job(...)` block, add:

```python
        # Auto-run pipeline every 4 hours
        pipeline_hours = int(os.environ.get("SIGNALOPS_PIPELINE_INTERVAL", "4"))
        if pipeline_hours > 0:
            scheduler.add_job(
                _run_pipeline_tick,
                "interval",
                hours=pipeline_hours,
                args=[db_url],
                id="pipeline_tick",
            )
            logger.info("Pipeline auto-run every %d hours", pipeline_hours)
```

**Step 3: Verify it loads**

Run: `cd /c/GitHubProjects/Syntrix && python -c "from signalops.api.app import create_app; print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add src/signalops/api/app.py
git commit -m "feat: add auto-scheduled pipeline run every N hours via APScheduler"
```

---

### Task 7: Add pipeline_interval_hours to settings

**Files:**
- Modify: `src/signalops/api/routes/setup.py`
- Modify: `dashboard/src/hooks/useSetup.ts`
- Modify: `dashboard/src/pages/Settings.tsx`

**Step 1: Update backend settings endpoint**

In `src/signalops/api/routes/setup.py`, add `pipeline_interval_hours` to the settings update logic. In the `SettingsUpdateRequest` Pydantic model (or wherever the settings PUT handler parses the body), add:

```python
    pipeline_interval_hours: int | None = None
```

And in the settings save handler, add to the YAML update logic:

```python
    if req.pipeline_interval_hours is not None:
        # Store in an env var for the scheduler to pick up on next restart
        os.environ["SIGNALOPS_PIPELINE_INTERVAL"] = str(req.pipeline_interval_hours)
```

**Step 2: Update frontend SettingsUpdateRequest**

In `dashboard/src/hooks/useSetup.ts`, add to `SettingsUpdateRequest`:

```typescript
  pipeline_interval_hours?: number | null;
```

**Step 3: Add interval slider to Settings page**

In `dashboard/src/pages/Settings.tsx`, add a new state variable:

```typescript
const [pipelineInterval, setPipelineInterval] = useState(4);
```

Add to the `handleSaveSettings` payload:

```typescript
pipeline_interval_hours: pipelineInterval,
```

Add a new Card section after the Sequence Settings card and before the Save button:

```tsx
        {/* Pipeline Auto-Run */}
        <Card className="glass border-white/10 bg-cyber-surface/80 backdrop-blur-xl">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Clock size={16} className="text-cyber-pink" />
              <CardTitle className="text-cyber-text text-sm">Pipeline Auto-Run</CardTitle>
            </div>
            <CardDescription className="text-cyber-text-dim text-xs">
              How often the pipeline automatically collects and scores new leads.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-cyber-text-dim text-sm">Run Every</Label>
              <span className="rounded-full border border-cyber-pink/30 bg-cyber-pink/10 px-2.5 py-0.5 text-xs font-mono text-cyber-pink">
                {pipelineInterval}h
              </span>
            </div>
            <Slider
              value={[pipelineInterval]}
              onValueChange={(v) => setPipelineInterval(v[0])}
              min={1}
              max={24}
              step={1}
              className="[&_[data-slot=slider-track]]:bg-cyber-surface-bright [&_[data-slot=slider-range]]:bg-cyber-pink [&_[data-slot=slider-thumb]]:border-cyber-pink [&_[data-slot=slider-thumb]]:bg-cyber-void"
            />
            <p className="text-[10px] text-cyber-text-dim/70">
              Pipeline collects tweets, judges relevance, scores leads, and generates drafts automatically.
            </p>
          </CardContent>
        </Card>
```

Add `Clock` to the lucide-react imports.

**Step 4: Verify TypeScript compiles**

Run: `cd /c/GitHubProjects/Syntrix/dashboard && npx tsc --noEmit`
Expected: PASS

**Step 5: Commit**

```bash
git add src/signalops/api/routes/setup.py dashboard/src/hooks/useSetup.ts dashboard/src/pages/Settings.tsx
git commit -m "feat: add pipeline auto-run interval to settings"
```

---

## Terminal 3: Landing Page + Polish

Files touched: `landing/src/components/*.tsx`, `README.md`, `pyproject.toml`

---

### Task 8: Update Hero to Docker-first CTA

**Files:**
- Modify: `landing/src/components/Hero.tsx`
- Modify: `landing/src/components/Navbar.tsx`

**Step 1: Update Hero.tsx**

Change the version badge from `v0.2` to `v0.3`:

```tsx
v0.3 — Open Source
```

Change the subheadline:

```tsx
<p className="mt-6 max-w-2xl font-body text-lg text-slate-400 sm:text-xl">
  Open-source lead finder that collects tweets, judges relevance via LLM,
  scores leads, drafts outreach, and sends DMs — all from a self-hosted dashboard.
</p>
```

Change the CTA button text and copy action from `pip install signalops` to `docker compose up`:

```tsx
await navigator.clipboard.writeText("git clone https://github.com/StrangeStorm243-bit/Syntrix.git && cd Syntrix && docker compose up");
```

```tsx
<span>docker compose up</span>
```

Update the terminal lines to show Docker output:

```tsx
const TERMINAL_LINES = [
  { prefix: "$ ", text: "git clone https://github.com/StrangeStorm243-bit/Syntrix.git", color: "text-white" },
  { prefix: "$ ", text: "cd Syntrix && docker compose up", color: "text-white" },
  { prefix: "  ", text: "✓ api — FastAPI on port 8400", color: "text-cta-green" },
  { prefix: "  ", text: "✓ dashboard — React UI on port 3000", color: "text-cta-green" },
  { prefix: "  ", text: "✓ ollama — Local LLM ready (llama3.2 + mistral)", color: "text-cta-green" },
  { prefix: "  ", text: "", color: "text-slate-400" },
  { prefix: "  ", text: "Open http://localhost:3000 → Setup wizard guides you through.", color: "text-aurora-cyan" },
];
```

**Step 2: Update Navbar.tsx**

Change the install pill to `docker compose up`:

```tsx
await navigator.clipboard.writeText("docker compose up");
```

```tsx
<span>docker compose up</span>
```

**Step 3: Verify it builds**

Run: `cd /c/GitHubProjects/Syntrix/landing && npm run build`
Expected: PASS

**Step 4: Commit**

```bash
git add landing/src/components/Hero.tsx landing/src/components/Navbar.tsx
git commit -m "feat(landing): update hero to Docker-first CTA with v0.3"
```

---

### Task 9: Update Pipeline with DM stage

**Files:**
- Modify: `landing/src/components/Pipeline.tsx`

**Step 1: Add DM stage and MessageCircle import**

Add `MessageCircle` to the lucide-react import.

Add DM stage to the STAGES array after the Send stage:

```tsx
  {
    icon: MessageCircle,
    name: "DM",
    desc: "Direct message outreach",
    gradient: "from-aurora-magenta/25",
  },
```

Update the section header subtitle:

```tsx
<p className="mt-4 font-body text-lg text-slate-400">
  Eight stages, fully configurable, human-approved at every step.
</p>
```

**Step 2: Commit**

```bash
git add landing/src/components/Pipeline.tsx
git commit -m "feat(landing): add DM stage to pipeline visualization"
```

---

### Task 10: Update Features with DM and Dashboard

**Files:**
- Modify: `landing/src/components/Features.tsx`

**Step 1: Replace two features**

Add `MessageCircle`, `Monitor` to the lucide-react import. Replace `Gauge` and `Target` with them.

Replace the "Rate-Limited Sending" feature with:

```tsx
  {
    icon: MessageCircle,
    title: "DM Outreach",
    desc: "Send direct messages to leads as part of configurable outreach sequences. Reply first, then DM, or go cold — your choice.",
    gradient: "from-aurora-blue to-aurora-magenta",
  },
```

Replace "Outcome Tracking" with:

```tsx
  {
    icon: Monitor,
    title: "Web Dashboard",
    desc: "React dashboard with pipeline stats, lead browser, draft queue, analytics, and real-time updates. No CLI required.",
    gradient: "from-aurora-magenta to-aurora-cyan",
  },
```

**Step 2: Commit**

```bash
git add landing/src/components/Features.tsx
git commit -m "feat(landing): update features with DM outreach and web dashboard"
```

---

### Task 11: Update QuickStart to Docker path

**Files:**
- Modify: `landing/src/components/QuickStart.tsx`

**Step 1: Replace STEPS**

```tsx
const STEPS = [
  {
    number: 1,
    title: "Clone",
    desc: "Grab the repo from GitHub.",
    code: "git clone https://github.com/StrangeStorm243-bit/Syntrix.git\ncd Syntrix",
  },
  {
    number: 2,
    title: "Launch",
    desc: "One command starts everything.",
    code: "docker compose up",
  },
  {
    number: 3,
    title: "Open",
    desc: "Setup wizard guides you through.",
    code: "# Open http://localhost:3000\n# Complete the 5-step wizard\n# Hit 'Run Pipeline' — done!",
  },
];
```

**Step 2: Commit**

```bash
git add landing/src/components/QuickStart.tsx
git commit -m "feat(landing): update quickstart to Docker Compose path"
```

---

### Task 12: Update TrustBar and Footer

**Files:**
- Modify: `landing/src/components/TrustBar.tsx`
- Modify: `landing/src/components/Footer.tsx`

**Step 1: Update TrustBar**

Add `Container` to lucide-react import. Change "CLI-first" badge to:

```tsx
  { icon: Container, label: "Docker Ready" },
```

**Step 2: Update Footer**

Remove "Architecture" link (PLANA.md is outdated). Replace with:

```tsx
  { label: "Dashboard", href: "https://github.com/StrangeStorm243-bit/Syntrix#web-dashboard" },
```

**Step 3: Commit**

```bash
git add landing/src/components/TrustBar.tsx landing/src/components/Footer.tsx
git commit -m "feat(landing): update trust bar and footer for Docker-first"
```

---

### Task 13: Update TerminalShowcase

**Files:**
- Modify: `landing/src/components/TerminalShowcase.tsx`

**Step 1: Add a "docker" tab as first tab**

Add a new tab to the beginning of the TABS array:

```tsx
  {
    label: "docker",
    command: "docker compose up",
    lines: [
      { text: "Creating syntrix-ollama-1  ... done", color: "text-cta-green" },
      { text: "Creating syntrix-api-1     ... done", color: "text-cta-green" },
      { text: "Creating syntrix-dashboard-1 ... done", color: "text-cta-green" },
      { text: "" },
      { text: "ollama    | pulling llama3.2:3b..." },
      { text: "ollama    | pulling mistral:7b..." },
      { text: "api       | INFO:     Uvicorn running on http://0.0.0.0:8400" },
      { text: "dashboard | Ready on http://localhost:3000", color: "text-cta-green" },
      { text: "" },
      { text: "Open http://localhost:3000 to start the setup wizard", color: "text-aurora-cyan" },
    ],
  },
```

**Step 2: Commit**

```bash
git add landing/src/components/TerminalShowcase.tsx
git commit -m "feat(landing): add Docker tab to terminal showcase"
```

---

### Task 14: Final polish — README and dependency check

**Files:**
- Modify: `README.md`
- Modify: `pyproject.toml` (verify deps)

**Step 1: Update README**

In `README.md`:
- Change the top heading from `SignalOps` to `Syntrix`
- Add "DM Outreach" to the Core Pipeline features section:

```markdown
- **DM outreach sequences** — configurable multi-step sequences including direct messages, with rate limiting and human approval
```

- Verify `apscheduler` and `cryptography` are mentioned or present in dependency lists

**Step 2: Verify pyproject.toml has required deps**

Check that `pyproject.toml` includes `apscheduler` and `cryptography` in the `[bridge]` extras.

**Step 3: Run landing page build**

Run: `cd /c/GitHubProjects/Syntrix/landing && npm run build`
Expected: PASS with no errors

**Step 4: Commit**

```bash
git add README.md pyproject.toml
git commit -m "docs: update README with DM outreach and Syntrix branding"
```

---

## Final Verification

After all three terminals complete:

1. **Run full Python CI**: `ruff check src/ tests/ && ruff format --check src/ tests/ && mypy src/signalops --strict && pytest tests/ -v --tb=short`
2. **Run dashboard build**: `cd dashboard && npx tsc --noEmit && npm run build`
3. **Run landing build**: `cd landing && npm run build`
4. **Merge and push**: `git push origin main`
