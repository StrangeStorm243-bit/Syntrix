# Remotion Demo Video — Design Doc

**Goal:** Create a 60-second programmatic demo video using Remotion (Approach A — standalone `video/` project), embedded top-center on the syntrix.app landing page via `@remotion/player`. The video must function as a **lead generation asset** — it should make visitors immediately understand the value, build trust, and drive them to try Syntrix or star the repo.

**Style:** Hybrid cinematic — starts dark/dramatic (cyberpunk), transitions to clean product shots, ends with over-the-top "getting rich" moment.

**Lead gen strategy:** Problem → Solution → Proof → Aspiration → CTA. Every scene answers a buyer objection: "What is this?" → "How does it work?" → "Does it actually work?" → "What could this mean for me?" → "How do I start?"

**Output formats:** 1080p MP4 (social), 720p MP4 (landing embed), plus 9:16 and 1:1 variants for stories/reels.

---

## Architecture

```
video/                      ← New Remotion project (standalone)
├── src/
│   ├── index.ts            ← registerRoot() entry point
│   ├── Root.tsx            ← Composition registration (60s @ 30fps, 1920x1080)
│   ├── DemoVideo.tsx       ← Main composition, sequences all scenes
│   ├── scenes/
│   │   ├── TheProblem.tsx      ← Scene 1: Frustrated tweets floating in
│   │   ├── EnterSyntrix.tsx    ← Scene 2: Logo slam + tagline typewriter
│   │   ├── ThePipeline.tsx     ← Scene 3: 8 stages lighting up sequentially
│   │   ├── TheDashboard.tsx    ← Scene 4: Stylized dashboard UI
│   │   ├── TheResults.tsx      ← Scene 5: Notification feed + acceleration
│   │   ├── GettingRich.tsx     ← Scene 6: Money rain, counters, hockey stick
│   │   └── CTA.tsx             ← Scene 7: Logo + syntrix.app + GitHub star
│   ├── components/
│   │   ├── TweetBubble.tsx     ← Animated tweet card
│   │   ├── PipelineStage.tsx   ← Single pipeline node with glow
│   │   ├── Counter.tsx         ← Spinning number counter
│   │   ├── Notification.tsx    ← Slide-in notification row
│   │   ├── MoneyRain.tsx       ← Dollar sign / confetti particle system
│   │   ├── HockeyStick.tsx     ← Exponential revenue chart
│   │   ├── Typewriter.tsx      ← Character-by-character text reveal
│   │   ├── Scanlines.tsx       ← CRT scanline overlay
│   │   └── ParticleBurst.tsx   ← Radial particle explosion
│   └── lib/
│       ├── colors.ts           ← Brand palette constants
│       ├── fonts.ts            ← Font loading (JetBrains Mono, IBM Plex Sans)
│       └── easing.ts           ← Custom spring configs
├── public/
│   ├── audio/
│   │   └── bgm.mp3            ← Royalty-free synthwave track
│   └── fonts/                  ← Self-hosted font files
├── package.json
└── tsconfig.json

landing/src/components/
├── DemoEmbed.tsx               ← @remotion/player wrapper for landing page
```

The `video/` project is fully independent — no imports from `landing/` or `dashboard/`. The landing page imports `@remotion/player` and the video composition to embed it.

---

## Storyboard (60s @ 30fps = 1800 frames)

### Scene 1: "The Problem" (0s–8s, frames 0–239)

- **Background:** Dark (#0F172A), subtle scanline overlay
- **Action:** 5-6 tweet bubbles fly in from screen edges with spring physics. Each shows a pain-point tweet ("Code review is killing us", "Bugs keep slipping through PRs", "Who even reads our tweets?"). Tweets stack center-screen, pulsing red glow.
- **Text overlay:** "Your customers are crying for help on X." fades in at frame ~180
- **Rapport hook:** Uses real pain points founders/growth teams relate to — "I get it, this is me"
- **Vibe:** Tension, chaos, problem awareness

### Scene 2: "Enter Syntrix" (8s–14s, frames 240–419)

- **Transition:** Hard cut, aurora gradient wipe (cyan → magenta)
- **Action:** Syntrix logo spring-bounces to center (overshoot). Radial particle burst on impact. Tagline "Find. Engage. Convert." types out character-by-character below logo. Subtext: "Open-source AI outreach — self-hosted, human-approved."
- **Trust signal:** "Open-source" and "self-hosted" build immediate credibility with technical founders
- **Vibe:** Relief, power, brand moment

### Scene 3: "The Pipeline" (14s–28s, frames 420–839)

- **Background:** Dark gradient, subtle grid pattern
- **Action:** 8 pipeline stages (Collect → Normalize → Judge → Score → Draft → Approve → Send → DM) appear left-to-right. Each stage: icon glows on → connecting line draws → mini animation plays:
  - Collect: tweet icons funnel in
  - Judge: "Relevant" stamp
  - Score: counter spins 0→92
  - Draft: text lines appear
  - Approve: green checkmark stamp
  - Send: paper airplane flies out
- **Timing:** ~1.5s per stage, with overlapping transitions
- **Lead gen:** Shows the product does real work — not vaporware. "Human-in-the-loop" at Approve stage builds trust that it's not spam
- **Vibe:** Technical credibility, smooth automation

### Scene 4: "The Dashboard" (28s–38s, frames 840–1139)

- **Transition:** Dashboard UI slides up from bottom
- **Action:** Stylized neon dashboard (dark bg, cyan/magenta accents):
  - Sidebar with "Syntrix v0.3" badge
  - 4 metric cards animate their numbers (collected: 1,247 / judged: 389 / drafted: 87 / sent: 58)
  - Mini bar chart grows
  - Draft queue: 3 rows with "Approve" buttons clicking green one by one
- **Vibe:** Control, polish, real product

### Scene 5: "The Results" (38s–48s, frames 1140–1439)

- **Layout:** Split screen — left: looping pipeline glow, right: notification feed
- **Action:** Notifications slide in with spring pop:
  - "Reply sent to @techleadSara" (cyan)
  - "DM delivered to @devops_mike" (magenta)
  - "@ctojennifer viewed your profile" (white)
  - "New follower: @ctojennifer" (green)
  - "Inbound DM: 'Hey, can we chat about your product?'" (gold)
- **Acceleration:** Notifications come faster and faster, stacking up
- **Vibe:** Momentum, results compounding

### Scene 6: "Getting Rich" (48s–58s, frames 1440–1739)

- **Transition:** Flash to gold background
- **Action (OVER THE TOP):**
  - Revenue counter: $0 → $1K → $10K → $100K → $1M (exponential easing)
  - Dollar signs rain from top (particle system, 50+ sprites)
  - Confetti explosion burst at $100K milestone
  - MRR chart: hockey stick curve that literally breaks through the top frame border
  - Screen shake intensifies (transform oscillation)
  - Green money particle burst fills screen
  - Bass drop sync point at $1M
- **Vibe:** Maximum hype, memeable, aspirational fun

### Scene 7: CTA (58s–60s, frames 1740–1799)

- **Transition:** Instant cut from gold chaos to clean dark
- **Action:** Syntrix logo springs in, centered. Three CTA options fade in staggered:
  1. "docker compose up" terminal snippet (self-host in 30 seconds)
  2. "syntrix.app" (learn more)
  3. GitHub star icon + star count badge (social proof)
- **Lead capture:** The surrounding landing page section (below the player) includes an email signup: "Get notified when v1.0 launches" — the video ends on the CTA and the page naturally scrolls to the signup
- **Vibe:** Professional close, clear next steps, multiple conversion paths

---

## Landing Page Integration

The video embeds in a new section between Hero and TrustBar:

```
Hero (3D scene)
 ↓
DemoEmbed (NEW — Remotion Player, centered, max-w-4xl)
 ↓
TrustBar (white)
 ↓
Pipeline (white)
...
```

The `<DemoEmbed>` component uses `@remotion/player`'s `<Player>` to render the video inline. It auto-plays on viewport intersection, has play/pause controls, and a "Watch full demo" link that opens the MP4 in a modal or new tab.

**Lead generation wrapper:** The section surrounding the player includes:
- Heading: "See how Syntrix turns tweets into customers"
- Subheading: "60 seconds. Zero fluff."
- Below player: email capture form ("Get notified when v1.0 launches") + "Star on GitHub" button
- Social proof badge: "Used by X founders" or GitHub star count

This creates a complete conversion funnel: Video hooks attention → CTA captures intent → Email/star converts.

---

## Audio

- Royalty-free synthwave/electronic track (user will source or we use a creative-commons track)
- Volume ramps: soft in scenes 1-2, builds in 3-4, driving beat in 5, bass drop in 6, quiet outro in 7
- Implemented via `<Html5Audio>` with `volume` callback using `interpolate()`

---

## Tech Stack

- **remotion** + **@remotion/cli** — core rendering
- **@remotion/player** — landing page embed
- **React 19** — composition components
- **Tailwind** (optional) — styling within Remotion components
- **TypeScript** — type safety

---

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Project location | `video/` at repo root | Clean separation, no dep conflicts |
| Approach | Programmatic (Approach A) | Full animation control, no screenshot deps |
| Duration | 60 seconds @ 30fps | Punchy for social, enough for full story arc |
| Resolution | 1920x1080 primary | Standard HD, scale down for variants |
| Style | Hybrid cinematic | Dramatic intro → clean middle → over-the-top ending |
| Landing embed | @remotion/player | Native React, no iframe, syncs with page |
| Audio | Synthwave BGM | Matches cyberpunk aesthetic, builds energy |
