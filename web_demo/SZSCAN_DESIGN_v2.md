# SZSCAN_DESIGN_v2.md — visual system (locked for build)

**Status: LOCKED.** Fully replaces `WEB_DEMO_DESIGN_SYSTEM.md` (v1 → `docs/archive/demo_v4/`).

**Authority:** `UI/` (locked PNGs) wins over this file on everything visible. This file records
**measured values** from those exact PNGs plus semantic rules that a static image can't express.
`SZSCAN_SPEC_v5.md` wins on behavior/logic.

**Source of values:** the hex codes below were **read directly by pixel-sampling the locked PNGs**
(2026-09-03), not eyeballed and not inherited from v1. Wherever v1 differs from the image, **the image
wins**, and this is clearly noted.

---

## 0 · Principles

1. **EEG is the central content.** Chrome never competes with the waveform.
2. **Three independent information axes, never mixed:** event source (AI/Human) · review status
   (Accept/Reject/Uncertain/Unseen) · interaction state (selected/playhead).
3. **Never convey meaning through color alone.** Always paired with text/icon — important for
   colorblindness and for projectors (projectors shift colors).
4. **Never over-claim through color.** An unreviewed alert is **not** red by default. Red is reserved
   for `Reject` review status and system errors.
5. **Attribution never uses a red heat scale.** It's interpretability, not a danger/SOZ level.

---

## 1 · Background & brand tokens (measured from the PNGs)

| Role | Hex | Note |
|---|---|---|
| Header gradient | `#624C8A` → `#10182B` | left to right, used on Log in / Database / Analysis alike |
| Brand violet (primary button) | `#776399` | ⚠ **differs from v1** — v1 recorded `#7C3AED`; the real image is noticeably more muted |
| Page background | `#FFFFFF` | ⚠ **differs from v1** — v1 recorded `#F8FAFC` |
| EEG canvas | `#FEFBEF` | **new token**, cream background in the style of an EEG reader |
| Footer bar | `#0F172A` | white text, persistent disclaimer |
| Surface (card/panel/table) | `#FFFFFF` | |
| Border | `#E2E8F0` | card border, divider |
| Border strong | `#CBD5E1` | main grid |
| Text primary | `#0F172A` | |
| Text secondary | `#475569` | |
| Text muted | `#64748B` | hint, empty-state |

### Violet has TWO separate roles — read carefully

v1 specified that violet **only** meant "currently interacting." The real UI uses violet for both the
header and the primary button. Decision: **split it into 2 roles, with no ambiguity because they never
appear in the same context.**

| Role | Color | Appears in |
|---|---|---|
| **Chrome / brand** | `#776399`, header gradient | Outside the content canvas: header, Create new / Save / Log in buttons |
| **Interaction** | more saturated violet, used for the playhead + "selected" outline | Inside the content canvas: playhead, selected-event outline, hovered channel on Attribution |

**Blue `#2563EB` is reserved exclusively for one meaning: Human-sourced events.** Never used for buttons.

---

## 2 · Event & review status (3 axes)

### Axis 1 — source

| Source | Hex | Icon |
|---|---|---|
| AI-detected | `#334155` charcoal | "AI" icon |
| Human-added | `#2563EB` blue | person icon |

### Axis 2 — review status (applies only to AI events)

| Status | Color | Light background |
|---|---|---|
| Accept | `#16A34A` | `#F0FDF4` |
| Reject | `#DC2626` | `#FEF2F2` |
| Uncertain | `#FFE262` (fill) / `#D97706` for text or a thin icon stroke on a light background | `#FFFBEB` |
| Unseen | `#94A3B8` | `#F8FAFC` |

*(CC_STEP6_FIX_PROMPT.md, author's decision: the original `#D97706` amber read too close to Reject
red and sank into the background — changed to `#FFE262`. That fill is illegible as text or a thin
stroke on a light background, so `#D97706` is kept under `--color-uncertain-text` for exactly those
uses.)*

### Axis 3 — interaction

Playhead · selected-event outline · hovered channel on Attribution → **saturated violet**.

**Combination rule:** an Accepted AI event = a green left vertical bar (status) + an "AI" icon (source) +
a very light green card background. If it's currently selected, a violet outline is **added**, **not
replacing** the vertical bar. All three axes always display simultaneously; no axis overrides another.

**On the Event Panel:** a ~4–5 px vertical bar on the left edge of each row. The row background is only
tinted very lightly, avoiding a "blotchy" look.

**On the mini-timeline and the Event Time row:** unreviewed AI = solid charcoal · Human = solid blue ·
Accept = solid green · Reject = solid red · Uncertain = solid `#FFE262` · selected = adds a violet
outline, does not change the underlying background color.

*(CC_STEP6_FIX_PROMPT.md, author's decision: all four are now full-opacity solid fills and Reject's
diagonal hatch is dropped, to match the mockup's own solid blocks. This relaxes principle 3 above
("never convey meaning through color alone") for these blocks specifically — status is still conveyed
by text on the Event Panel row and its badges, just not redundantly on these small blocks too.)*

**While one event is being viewed:** other events drop to ~40% opacity (color unchanged); the selected
event keeps full intensity + the violet outline.

---

## 3 · EEG waveform

| Object | Value |
|---|---|
| Canvas background | `#FEFBEF` |
| Raw EEG (filter off, or as background when filter is on) | `#64748B`, 50% opacity |
| Filtered EEG (highlighted when lff/hff/60 is on) | `#0F172A`, 100% opacity |
| Minor grid | `#E2E8F0` |
| Major grid | `#CBD5E1` |
| Playhead | violet |
| AI event background overlay | `#334155`, 8–10% opacity |
| Human event background overlay | `#2563EB`, 8–10% opacity |

**Not used:** red for an abnormal waveform (no clinical threshold justifies it) · a separate color per
channel across the 18 channels (a rainbow hurts legibility and adds no information) · strong gradients
inside the waveform · a full-page black background.

---

## 4 · Channel Attribution — teal scale

| Level | Hex | Note |
|---|---|---|
| Low | `#CBD5E1` | neutral slate |
| Medium | `#2DD4BF` | teal-400 |
| High | `#0F766E` | teal-700 |
| Hovered/selected | violet | |
| Rejected channel | keeps its line, ~35% opacity or dashed | |

Colorbar over the head diagram: `linear-gradient(to right, #CBD5E1, #2DD4BF, #0F766E)`.

**Why teal, and why only 3 levels:**
- Not **red-yellow-green**: implies a danger level/SOZ — wrong nature, attribution is interpretability
  (`docs/ATTRIBUTION_SPEC.md`).
- Not **blue**: gets lost on a white background, and blue already has an owner (Human events).
- Not **purple**: would clash directly with "hovered" — a high-scoring channel would be indistinguishable
  from a hovered channel.
- Teal is the only hue in the current palette **not yet assigned a meaning**.
- 3 levels are enough for a thin-line representation; more levels would be indistinguishable to the eye.

**Two-way interaction** (hovering a table row → highlights the matching line and vice versa): improves
UX, **not required**. Can be dropped if time is tight.

---

## 5 · Database

| Component | Style |
|---|---|
| Table header | `#F1F5F9` background |
| Default / hover row | white / `#F8FAFC` |
| Selected row | `#EFF6FF` background, blue left border |
| Subject row | `font-weight: 600` |
| Child file row | slightly indented, secondary text |

**Status badge:** `View` → text `#475569`, empty-circle icon · `Viewing (x/N)` → `#B45309`, half-filled
icon · `Viewed` → `#15803D`, check icon.

**Alert:** shown in **neutral text color** (`#0F172A`), no amber, no red.
⚠ **Differs from v1** — v1 specified amber when > 0. The real image keeps it plain black; the old rule
existed to ban **red**, and neutral black already serves that purpose while also avoiding noise from
every row being amber.

---

## 6 · Typography

| Role | Font |
|---|---|
| General UI (label, button, table) | Inter |
| Technical data (file name, channel name, timestamp, score) | IBM Plex Mono |

Monospace for technical data is **mandatory**: numeric tables must line up, and `FP1-F7` vs `FP1-F3`
must never be misread. Both fonts are free on Google Fonts.

**Font size:** page title 20–24 · section title 15–16 · body 13–14 · table 12–13 · timestamp 12 ·
button 13–14 · badge 11–12 (px).

---

## 7 · Spacing

Multiples of 4 px. Page padding 24 · gap between panels 16 · panel padding 16–20 · toolbar group gap
12–16 · event row height 48–56 · expanded event row 140–180.

The Analysis screen **is allowed to be long and scroll vertically**. Don't force every panel to fit one
viewport; prioritize breathing room.

---

## 8 · Wording — quick-reference table (anti-overclaiming)

| Situation | Use | Do NOT use |
|---|---|---|
| File has no AI events at all | `No detected events in this file. You can still add an event manually with Select Range.` | `No seizure detected` |
| Unreviewed AI event | `Unseen` badge, neutral color | red color |
| Process running | `Processing subject — combining files and detecting change points...` | fake % |
| Upload file error | `File rejected — unsupported format or channel configuration.` | `Upload failed` |
| Subject outside the allowlist | `This demo is restricted to the held-out test subjects.` | silently ignore |
| Attribution panel title | `Channel-level reconstruction anomaly — Event N` | `Channel contribute to ...` |
| Block label on the Event Time row | `Event N` | `seizure N` |
| Mini-timeline row 2 | `Detections` | `Seizure Detections` |
| Footer on every screen (except Log in) | `SzScan is an AI-assisted tool designed to support clinicians, not replace them.` | — |

---

## 9 · Design tokens — starting point for code

```css
:root {
  /* background & chrome */
  --color-bg:              #FFFFFF;
  --color-surface:         #FFFFFF;
  --color-eeg-canvas:      #FEFBEF;
  --color-footer:          #0F172A;
  --color-border:          #E2E8F0;
  --color-border-strong:   #CBD5E1;

  --header-gradient:       linear-gradient(90deg, #624C8A 0%, #10182B 100%);
  --color-brand:           #776399;   /* chrome: header, primary button */
  --color-interaction:     #7C3AED;   /* playhead + selected (content canvas only) */

  --color-text:            #0F172A;
  --color-text-secondary:  #475569;
  --color-text-muted:      #64748B;

  /* event source */
  --color-ai:              #334155;
  --color-human:           #2563EB;   /* exclusive to Human events, NOT used for buttons */

  /* review status */
  --color-accept:          #16A34A;  --color-accept-bg:    #F0FDF4;
  --color-reject:          #DC2626;  --color-reject-bg:    #FEF2F2;
  --color-uncertain:       #FFE262;  --color-uncertain-bg: #FFFBEB;
  --color-uncertain-text:  #D97706;   /* text / thin icon stroke on a light background only */
  --color-unseen:          #94A3B8;

  /* EEG */
  --color-eeg-raw:         #64748B;
  --color-eeg-filtered:    #0F172A;
  --color-grid:            #E2E8F0;
  --color-grid-strong:     #CBD5E1;

  /* attribution (teal) */
  --color-attr-low:        #CBD5E1;
  --color-attr-mid:        #2DD4BF;
  --color-attr-high:       #0F766E;

  /* layout */
  --radius-panel:          10px;
  --radius-control:        6px;
  --shadow-panel:          0 1px 3px rgb(15 23 42 / 8%);

  --font-ui:               'Inter', sans-serif;
  --font-mono:             'IBM Plex Mono', monospace;
}
```

---

## 10 · What changed from v1 (so it's not used by mistake)

| Item | v1 | v2 (this file) | Why |
|---|---|---|---|
| Page background | `#F8FAFC` | `#FFFFFF` | measured from the locked image |
| Primary button | blue `#2563EB` | violet `#776399` | measured from the locked image |
| EEG canvas background | (no token) | `#FEFBEF` | measured from the locked image; cream is the EEG-reader convention, better contrast for dark strokes |
| Violet's role | only "interacting" | split into chrome / interaction | the image uses violet as the brand color; the two roles never share a context, so no ambiguity |
| Attribution | light blue → dark blue | 3-level teal | blue gets lost on white + blue already has an owner |
| Alert | amber when > 0 | neutral | the locked image; the old rule only aimed to ban red |
| Detection Score Y-axis | auto-scale P1–P99 (with numbers) | auto-scale P1–P99, **no numbers shown**, zero-line only | small box, quick-glance role; a z-score has no absolute meaning worth reading a number for |
| Header | (not described) | gradient `#624C8A → #10182B` | measured from the locked image |
| Footer | (none) | persistent `#0F172A` bar | the author's transparency decision |
| Uncertain status | `#D97706` amber (fill) | `#FFE262` (fill), `#D97706` kept as `--color-uncertain-text` | amber read too close to Reject red and sank into the background (CC_STEP6_FIX_PROMPT.md) |
| Reject block (mini-timeline/Event Time) | solid `#DC2626` at ~55% opacity + diagonal hatch | solid `#DC2626` at full opacity, no hatch | hatch dropped to match the mockup's solid blocks (CC_STEP6_FIX_PROMPT.md) |
| Accept/Uncertain block (mini-timeline/Event Time) | ~75% opacity | full opacity | same mockup-matching decision as the Reject row above |

---

*End of SZSCAN_DESIGN_v2.md.*
