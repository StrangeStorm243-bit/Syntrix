# v0.2 3-Terminal Parallel Build — Design Summary

**Date:** 2026-02-20
**Status:** Approved
**Full Plan:** See `PLANB_3TERMINAL.md` in project root

## Decision Record

### Terminal Split

| Terminal | Workstream | Rationale |
|----------|-----------|-----------|
| A: Infrastructure | Redis cache, Filtered Stream, engagement polling, multi-project | Foundational — other features build on these. Merge first. |
| B: Learning Loop | Outcome tracking, feedback, eval, export | Coherent closed loop with sequential dependencies. |
| C: UX & Observability | Notifications, enhanced stats, orchestrator hooks | Mostly new files, lowest conflict risk. |

### Key Design Decisions

1. **Redis: Optional with fallback** — InMemoryCache as default, RedisCache when configured and available
2. **Stats: Enhanced Rich panels** — No Textual dependency, ships faster
3. **Filtered Stream: Interface + stub** — Pro tier not assumed, implementation ready to enable
4. **Worktrees over branches** — Full filesystem isolation, no `git checkout` conflicts
5. **Merge order: A -> B -> C** — Infrastructure first, learning loop second, UX last

### File Ownership

38 files touched total (11 new source, 13 modified source, 11 new tests, 2 modified tests, 1 fixture).
Zero file overlap between terminals.
