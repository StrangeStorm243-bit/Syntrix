# Terminal B — Component Library → Remaining Pages

**Role:** Build all cyberpunk UI primitives, then upgrade Leads/Queue/Experiments/Settings pages
**Phases:** 2 → 6 (remaining pages portion)
**Waits for:** Terminal A Phase 1 complete

---

## Shared Conventions

See `v03terminalA.md` → "Shared Conventions" section for color palette, typography, file naming, import conventions, architectural rules, and coordination protocol. ALL terminals follow the same conventions.

---

## Phase 2: Cyberpunk Component Library

**Requirements:** CL-01, CL-02, CL-03, CL-04, CL-05, CL-06, CL-07
**Blocks:** Terminal A Phase 4, Terminal B Phase 6, Terminal C Phase 6

### Step 1: Install Dependencies

```bash
cd dashboard
npm install motion augmented-ui
```

Note: `augmented-ui` is CSS-only, imported via `@import 'augmented-ui/augmented-ui.min.css'` in index.css.

### Step 2: Create Animation Presets

**File: `dashboard/src/lib/animation-presets.ts`**
```typescript
import type { Variants } from 'motion/react';

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.4 } },
};

export const slideUp: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } },
};

export const staggerContainer: Variants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.3 } },
};

export const glowPulse: Variants = {
  idle: { boxShadow: '0 0 5px rgba(255,20,147,0.2)' },
  active: {
    boxShadow: [
      '0 0 5px rgba(255,20,147,0.2)',
      '0 0 15px rgba(255,20,147,0.4)',
      '0 0 5px rgba(255,20,147,0.2)',
    ],
    transition: { duration: 2, repeat: Infinity },
  },
};
```

### Step 3: Build Components

**File: `dashboard/src/components/cyber/GlassCard.tsx`**
```typescript
// Props: children, className, augmented (boolean — enables clip-path HUD border)
// Uses: glass class from glassmorphism.css
// If augmented: adds data-augmented-ui="tl-clip br-clip border" attribute
// Wraps children in motion.div with scaleIn variant
```

**File: `dashboard/src/components/cyber/NeonMetricCard.tsx`**
```typescript
// Props: title, value (number), icon, color ('pink'|'orange'|'gold'), prefix, suffix
// Features:
//   - Animated number counter (count from 0 to value on mount using motion)
//   - Neon glow border matching color prop
//   - Monospace font for value (--font-mono)
//   - Icon with matching glow
//   - GlassCard as wrapper
```

**File: `dashboard/src/components/cyber/NeonSidebar.tsx`**
```typescript
// Replace existing Sidebar component
// Features:
//   - Active link has neon glow indicator (left border glow)
//   - Hover state with subtle background glow
//   - Logo/brand area at top with neon text
//   - Glass background
//   - Navigation links with lucide icons (keep existing icons)
//   - Add "Pipeline" link for Phase 5's new page
```

**File: `dashboard/src/components/cyber/NeonBadge.tsx`**
```typescript
// Props: children, variant ('pink'|'orange'|'gold'|'green'|'red'), glow (boolean)
// Replaces: ScoreBadge, JudgmentBadge
// Features: neon border, optional glow animation, color-coded
```

**File: `dashboard/src/components/cyber/NeonButton.tsx`**
```typescript
// Props: children, variant ('primary'|'secondary'|'danger'|'ghost'), size, disabled, onClick
// Features: neon border glow on hover, press animation (scale 0.97), disabled state dims glow
```

**File: `dashboard/src/components/cyber/NeonTable.tsx`**
```typescript
// Props: columns, data, onRowClick, sortable
// Replaces: DataTable
// Features:
//   - Glass header row with neon bottom border
//   - Hover row glow (subtle pink background + border glow)
//   - Monospace for numeric columns
//   - Pagination controls with NeonButton
//   - Stagger animation on row mount
```

**File: `dashboard/src/components/cyber/NeonInput.tsx`**
```typescript
// Props: standard input props + label, error
// Features: neon border on focus, glass background, monospace for value, error state in red glow
```

**File: `dashboard/src/components/cyber/NeonTooltip.tsx`**
```typescript
// Props: content, children, side
// Features: glassmorphism popup, neon border, small delay on show
```

### Step 4: Create Index Export

**File: `dashboard/src/components/cyber/index.ts`**
```typescript
export { GlassCard } from './GlassCard';
export { NeonMetricCard } from './NeonMetricCard';
export { NeonSidebar } from './NeonSidebar';
export { NeonBadge } from './NeonBadge';
export { NeonButton } from './NeonButton';
export { NeonTable } from './NeonTable';
export { NeonInput } from './NeonInput';
export { NeonTooltip } from './NeonTooltip';
```

### Step 5: Update CyberpunkLayout Sidebar

Replace `<Sidebar>` import with `<NeonSidebar>` in `CyberpunkLayout.tsx`.

### Step 6: Verify & Commit

- Each component renders in isolation
- Components reference CSS variables from Phase 1
- Motion animations work (enter/exit)
- augmented-ui clip-paths render on GlassCard when `augmented` prop is true

```bash
git commit -m "feat(dashboard): Phase 2 — cyberpunk component library (8 components)"
```

**Signal to Terminal A: Phase 2 complete. Components available for page upgrades.**

---

## Phase 6 (Partial): Remaining Page Upgrades

**Requirements:** RP-01, RP-02, RP-03, RP-04
**Depends on:** Phase 2 complete (this terminal), Phase 3 complete (Terminal C)

### Leads.tsx Upgrade (RP-01)

Replace DataTable with NeonTable. Replace ScoreBadge/JudgmentBadge with NeonBadge. Add stagger animation on row mount. Keep existing data hooks unchanged. Add Motion page transition wrapper.

### Queue.tsx Upgrade (RP-02)

Replace DraftCard styling with GlassCard base. Replace buttons with NeonButton (green=approve, blue=edit, red=reject). Add slide-in animation for new cards. Keep existing approve/edit/reject mutation hooks unchanged.

### Experiments.tsx Upgrade (RP-03)

Replace table with NeonTable. Status badges use NeonBadge with glow for active experiments. Add empty state with cyberpunk styling.

### Settings.tsx Upgrade (RP-04)

Replace input with NeonInput. Replace save button with NeonButton. Add glass panel wrapper. Add "Performance Mode" toggle placeholder (Phase 7 will wire it).

### Commit

```bash
git commit -m "feat(dashboard): Phase 6 — cyberpunk Leads, Queue, Experiments, Settings pages"
```
