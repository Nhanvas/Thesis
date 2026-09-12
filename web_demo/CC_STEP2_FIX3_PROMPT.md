# CC_STEP2_FIX3_PROMPT.md — Step 2, round 4: LoginScreen logo source + favicon

Prior rounds fixed `Header.jsx` (Database/Analysis screens) to use `web_demo/frontend/src/assets/logo.png`
(confirmed byte-identical to `web_demo/UI/Logo.png` via `cmp`). The Log in screen still shows the old
placeholder icon — it's very likely using a different source entirely (an inline SVG, or a separate
image import) that was never touched by the earlier fixes. Find it, don't guess.

## 0. Investigate first — write down what you find before changing anything

```
grep -rn "logo\|Logo" web_demo/frontend/src/screens/LoginScreen.jsx web_demo/frontend/src/components/ 2>/dev/null
```
Also check if `LoginScreen.jsx` renders its own inline `<svg>...</svg>` for the head/lightning icon
directly in the JSX, rather than an `<img>` tag — that's the most likely reason it wasn't affected by
swapping the image file. Report exactly what you find.

## 1. Fix the Log in screen logo

Whatever the actual source turns out to be, make the Log in screen use the same
`web_demo/frontend/src/assets/logo.png` that `Header.jsx` now uses — same file, same visual result on
both screens. If it's currently an inline hand-drawn SVG, replace it with an `<img>` tag pointing at that
asset instead (matching the pattern already used in `Header.jsx`), rather than trying to hand-edit SVG
path data to match.

## 2. Favicon (browser tab icon) — separate, smaller issue

`Logo.png` is solid white with transparency (no color) — fine on the purple header, but invisible on a
typical light browser tab background. Not required by any mockup (`UI/A0a`/`A0b`/`A0c` don't show tab
chrome), so keep this quick and don't over-engineer it:

- Check what favicon is currently referenced in `web_demo/frontend/index.html`.
- Generate a simple square version with a solid dark background (reuse the header's own colors —
  `--color-brand: #776399` or the header gradient, check `SZSCAN_DESIGN_v2.md §1`) behind the white logo
  mark, sized appropriately for a favicon (32x32 or similar), save it under `web_demo/frontend/public/`,
  and reference it in `index.html`.
- Don't spend more than a few minutes on this — a simple colored square behind the white mark is enough,
  no need for pixel-perfect favicon design.

## Boundaries (same as every round)

- Never write to anything under `web_demo/UI/` — read/copy only.
- Only touch `web_demo/frontend/` — no backend changes.
- Don't start Create New / search / Step 3 scope.

## Report — write to a file this time, not just terminal output

Write your findings and what you changed to `web_demo/CC_STEP2_FIX3_REPORT.md` (create it), covering:
(a) what you found in step 0 (the actual logo source in LoginScreen.jsx), (b) what you changed and where,
(c) what favicon file you created and where it's referenced, (d) `git status` output. Keep the terminal
reply short — just say the report file is written and stop. Do not start Step 3.
