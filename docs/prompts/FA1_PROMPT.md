# FA1 — read-only facts for report version A1 (Track F, chat D25-F, 14/11)

**Task.** Run the committed read-only script `src/fa1_readonly.py`, which answers two requests of report version A1
(`REPORT_REVISION_PLAN.md` rev 6 §0.2): **F-A1.1** facts of the two hospital records, **F-A1.2** the recorded selection
rules of the deck's real-EEG figures. No model, no EEG signal, no score is computed. Expected runtime: under 1 minute for
the script, about 10 minutes for the whole task.

**Privacy (binding).** The hospital EDF files in `F:/Study/Thesis/Dataset/Clinical/` carry patient names in their file
names and headers. **Do not open, list, print or quote** anything from `Dataset/Clinical/` or `Defense/clinical/`
yourself — only the script reads them, and it writes the private part only to `Agent/inbox/FA1_1_CLINICAL_REPORT.md`.
**Never** commit, push, copy or summarise that report anywhere; do not even read it back into this session. If any step
prints a file name of a hospital record, a name, a header field or a date of a hospital record, stop and tell the author.

## Steps (Git Bash, in `F:/Study/Thesis/Code`)

1. `git pull` on `main`. Check that these three files exist and are not yet tracked by git (installed from the chat
   delivery): `src/fa1_readonly.py`, `src/fa1_readonly_test.py`, `docs/prompts/FA1_PROMPT.md`. If one is missing or
   already tracked with other content → STOP and report.
2. Synthetic test (no real data, seconds): `python src/fa1_readonly_test.py`. It must end with `25 / 25 checks PASS`.
   Otherwise STOP, change nothing, report the output.
3. Real run, timed: `time python src/fa1_readonly.py --root F:/Study/Thesis`. Expected console lines:
   `privacy gate: N protected phrases (not shown)`, `part A: …`, `part B: written …FA1_1_CLINICAL_REPORT.md …`,
   `done in … s`. Any `STOP` → change nothing, report the STOP line (it never contains a protected phrase).
4. Check before committing: `git status --porcelain` must show only `src/fa1_readonly.py`, `src/fa1_readonly_test.py`,
   `docs/prompts/FA1_PROMPT.md` and `results/fa1/` (`INVENTORY.md`, `inventory.csv`, `hits.csv`, `defense_copy/…`).
   `du -sh results/fa1` must be below 20 MB. Nothing from `Agent/` and nothing under `Dataset/` is ever added.
5. Commit and push exactly these paths:
   `git add src/fa1_readonly.py src/fa1_readonly_test.py docs/prompts/FA1_PROMPT.md results/fa1`
   message: `FA1: read-only facts for report A1 (F-A1.2 inventory; F-A1.1 private, not committed) (D25-F)`, then
   `git push`.
6. Write `F:/Study/Thesis/Agent/inbox/FA1_RUN_REPORT.md`: test result line, the console lines of step 3, measured time,
   the commit hash, `git show --stat HEAD`. Do not include anything from the private report.
7. Tell the author: (a) the commit hash; (b) to open `Agent/inbox/FA1_1_CLINICAL_REPORT.md` himself, check that it holds
   no name, file name, header field or date, and paste its content into the Track F chat; (c) this prompt file is
   committed — nothing is left to delete in `_tmp/` once the delivery folder is removed.
