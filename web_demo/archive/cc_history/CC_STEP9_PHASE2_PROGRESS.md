# CC_STEP9_PHASE2_PROGRESS.md — per-subject checkpoint log (CC_STEP9_PHASE2_RESUME_PROMPT.md §2)

One line per subject, appended immediately after it finishes (appears in the Database table,
Status `View`) — so a later interruption never has to re-derive anything already recorded here.
Columns: subject id, file count, wall-clock Phase A+B time, wall-clock Process/PELT time, converged
`pen_mult`.

| Subject | Files | Phase A+B (s) | Process/PELT (s) | `pen_mult` | Note |
|---|---|---|---|---|---|
| `chb17` | 21 | 572.84 | 166.82 | 2.0 | Resumed mid-upload after an interrupted session (had reached 21/21 uploaded, `phase_b_done` still false); Phase A+B timing uses a recovered start timestamp from the interrupted run's own poller log (`t=2026-09-26T17:35:31.651`, accurate to ~2 s), not a fresh session start — see `CC_STEP9_PHASE2_REPORT.md` for detail. |
| `chb14` | 26 | 607.01 | 171.87 | 5.0 | Clean, uninterrupted run. |
| `chb18` | 36 | 813.95 | 389.86 | 2.0 | Resumed after a second interrupted session (had reached 36/36 uploaded, `phase_b_done` true, `processing` true — Process had already been clicked); both Phase A+B and Process/PELT timing use recovered timestamps from the interrupted run's own poller log (`t_first_upload_post=2026-09-26T18:02:43.036`, `t_phase_b_done=2026-09-26T18:16:16.984`, `t_process_click=2026-09-26T18:16:18.007`), not resume-time placeholders — see `CC_STEP9_PHASE2_REPORT.md` for detail. |
| `chb03` | 38 | 462.70 | 138.79 | 2.0 | Resumed after a third interruption (38/38 already uploaded, `phase_b_done` false); the initial resume attempt also hit a client-side `ReadTimeout` polling the server under heavy Phase A concurrency (the pipeline itself was fine — a hardened, longer-timeout/retry poll then completed it cleanly). A wrong `--recovered-start-iso` guess was first used and later corrected against the run's own timeline log — see `CC_STEP9_PHASE2_REPORT.md` for both anomalies in full. |
| `chb15` | 40 | 562.69 | 127.65 | 5.0 | Clean, uninterrupted run. |
| `chb06` | 18 | 726.05 | 293.48 | 2.0 | First attempt hit a genuine pipeline bug, not an interruption: Phase B's whole-subject float64 concatenation needed ~6.9 GiB for one array and crashed with `numpy._core._exceptions._ArrayMemoryError` (chb06 has the most hours-per-file of any allowlisted subject: 66.74 h across only 18 files). Fixed in `pipeline_demo.py`'s `process_subject_phase_b` (chunked, bit-identical, not chb06-specific) — see `CC_STEP9_PHASE2_REPORT.md`. Retried from scratch (full 18-file set, no shortcut) after the fix; completed cleanly, no error, no OOM. |
