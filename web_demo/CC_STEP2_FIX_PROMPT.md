# CC_STEP2_FIX_PROMPT.md — Step 2 visual fixes after Boti's screenshot comparison

Boti compared the running app against `UI/A0a`/`A0b`/`A0c` and found real gaps. You have no browser
tooling this session, so you can't self-verify the visual result — that's expected, Boti will
screenshot again after this fix. Just make the changes and stop.

**Before editing anything, re-view the mockups fresh** (copy to scratch first, as before — never open
anything under `web_demo/UI/` directly): `web_demo/UI/A0a*.png`, `A0b*.png`, `A0c*.png`. Don't rely on
your memory of viewing them earlier in this session — re-look now, this fix is about catching details
you missed the first pass.

## 1. Logo

Replace the placeholder lightning-bolt-circle icon with the real logo file: `web_demo/UI/Logo.png`.
Use it in both places it appears: the header (Database/Analysis screens) and the Log in screen, at the
size/position shown in the mockups.

## 2. Header sizing

Measured on Boti's screenshot: the header takes up about 12.9% of the viewport height in the mockup,
but only about 10.8% in the running app — visibly smaller than it should be. Don't hardcode a pixel
value from that percentage (it depends on Boti's window size) — instead, re-look at the mockup and
match its **proportions**: logo mark size, "SzScan" wordmark size, avatar circle size, and the padding
above/below them inside the header bar, all relative to each other and to the header's own height.

## 3. Table column headers — literal `|` character, easy to miss

The mockup's column header row renders `| No. files` and `| Status` — with a leading pipe character
**as actual pixel content in the image**, specifically on those two labels only (not on ID, Start date,
Duration, Alert, or Memo). This is not markdown table syntax bleeding through; it's a real character in
the design. Your current build renders `No. files` and `Status` with no pipe. Fix those two column
header labels to match exactly, and re-check with fresh eyes that no other label in that row differs
from the mockup.

## 4. Page / card padding

By eye (not pixel-measured this time — you have the actual mockup, use that, not this description) the
white table-card area in the app sits with less surrounding whitespace and a less visible rounded
boundary than the mockup shows. Cross-check `SZSCAN_DESIGN_v2.md §7` (page padding 24, panel padding
16-20, `--radius-panel: 10px`) against wherever `web_demo/frontend/src` lays out the Database screen,
and confirm those tokens are actually being applied at the right elements, not just defined.

## Stop condition

List exactly what you changed and in which files. Do not start Step 3. Do not touch anything under
`web_demo/UI/` other than reading/copying-to-scratch to view.
