# CC_STEP2_FIX2_PROMPT.md — Step 2, round 3: logo (still broken) + header (overshot the other way)

Two earlier fix attempts happened: your own previous pass (`CC_STEP2_FIX_PROMPT.md`) fixed the `|`
prefix on the "No. files"/"Status" column headers correctly, but the logo swap did **not** take effect
— it's still the placeholder lightning-bolt-circle icon, confirmed by screenshot. A separate attempt in
Cursor's agent made zero code changes (ran out of quota before writing anything), so nothing there to
account for. This round needs to actually land both remaining items, with explicit verification at each
step so we can see exactly what happened if something still doesn't work.

## 0. Before touching anything

Run and paste the raw output of:
```
ls -la web_demo/UI/Logo.png
```
Confirm the exact filename and casing that exists on disk. If this doesn't return the file, stop and
say so — don't guess a different path.

## 1. Logo (this failed silently last time — be defensive)

- Copy `web_demo/UI/Logo.png` (read-only source, never modify the original) into wherever
  `web_demo/frontend/` actually serves static assets from — look at how the current placeholder icon is
  referenced in the header/login components first, and follow that exact same convention (same folder,
  same import style) rather than inventing a new pattern.
- After wiring it in, run `grep -rn "lightning\|placeholder" web_demo/frontend/src` (or whatever term
  matches the old icon's component/class name) to confirm no leftover reference to the old icon remains
  in either the header (Database/Analysis screens) or the Log in screen.
- State explicitly in your report: the exact new file path you created/copied to, and the exact
  component file(s) you edited to reference it.

## 2. Header sizing — precise numeric target, no guessing this time

Measured directly from screenshots (pixel-counted, not eyeballed): the mockup's header occupies **12.9%**
of the total page height on the Database screen (`UI/A0a`). Your previous attempt overshot to **15.7%** —
about 18% too tall relative to the target. Before this attempt undershot to 10.8%. Both were guesses from
visual inspection; this time, don't guess a third value — instead:

1. Find the exact CSS/Tailwind classes or explicit height/padding values currently controlling the
   header container's vertical size in `web_demo/frontend/src`.
2. Report those exact current values in your response.
3. Reduce them by approximately 18% (e.g. if it's `py-8`, that's not a linear scale in Tailwind's spacing
   steps, so pick the nearest step down and say which one and why; if it's an explicit px/rem height,
   compute the reduced value directly and use that).
4. Report the exact new values you set, so the actual percentage can be re-measured against a fresh
   screenshot afterward.

You don't have browser tooling this session — that's fine, this step is a calculation from known
numbers, not a visual guess.

## Boundaries (same as before)

- Never write to anything under `web_demo/UI/` — read/copy only.
- Only touch `web_demo/frontend/` — no backend changes.
- Don't start Create New / search wiring or anything else — still out of scope.

## Stop condition

Report, in this exact order: (a) the `ls -la` output from step 0, (b) the old and new logo file paths
and which component files you edited, (c) the grep confirmation output, (d) the old and new header
CSS values with your reasoning for the reduction, (e) `git status` output. Do not start Step 3.
