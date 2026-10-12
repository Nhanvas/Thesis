# CC_PART2_PART4_PROMPT.md — screenshots, Figure 3.6 and timing, on szscan-frozen-v2

Unattended. Do not stop to ask. Work on the current checkout. First confirm that `web_demo/` code is
unchanged against `szscan-frozen-v2` (untracked `.md`, `.log` and `report_handback/` files do not count).
If the code differs, stop and report. Change no code in `web_demo/`. Never open the seizure fields of
`chb*-summary.md` or `results/attribution_v7/labels/`. Delete nothing.

## A. Hardware and software (Part 4.1)

Record in `REPORT_HANDBACK.md` "## 4. Timing":
- CPU model (`wmic cpu get name`, or `Get-CimInstance Win32_Processor` if wmic is missing), cores and
  threads;
- total RAM and OS version;
- Python, PyTorch and NumPy versions;
- the torch device, which must be CPU with CUDA unavailable;
- the runtime environment: pagefile on F:, TMP on F:.

## B. Repeated timing on one reference recording (Part 4.2, 4.4)

Reference recording: the four-hour recording behind the earlier 9.76 s per hour figure, as named in
`web_demo/BUILD_PROGRESS.md` §4. State which file it is.

Process it **5 times**, calling the same processing functions the application uses
(`web_demo/backend/pipeline_demo.py` and the existing per-stage timing instrumentation). Do not go
through the database, so the demo DB is not touched. Close everything else first.

For every run, record the wall time of each stage the instrumentation reports, and the total. Write them
to `web_demo/report_handback/timing_repeated.csv`, with columns `run,stage,seconds,eeg_hours`.

Then report, for each stage and for the total:
- median seconds per hour of EEG;
- min and max seconds per hour of EEG;
- the command used.

## C. Per-file timing of the Tier 2 run (Part 4.3)

If the per-stage instrumentation logged per-file stage times during the `szscan-frozen-v2` Tier 2 run
(check `uvicorn.log`, the backend's own logs and the DB), extract them to
`web_demo/report_handback/timing_tier2.csv`, with columns
`subject,file_name,stage,seconds,eeg_hours`.

If they were not logged, write "not logged". Also compute the end-to-end rate from the per-subject
wall-clock table already in §3: total seconds / total EEG hours, including upload. Do not re-run
anything for C.

## D. Screenshots (Part 2, as revised in REPORT_REPLY_TO_PROJECT2_2.md)

Start the backend on this checkout and log in.

Capture with Playwright:
- viewport 1600 × 1000 CSS px, device scale factor 2;
- light theme, no browser chrome, no cursor;
- output directory `web_demo/report_handback/`.

The screenshots show recording `chb13_62`, or another chb13 file with an AI event if it is absent (name
it). The selected event is **the AI event in that file with the highest maximum fused anomaly score
within its onset–offset interval**; if two events tie, take the earlier one. This choice uses no label.

1. `fig3_6a_import.png`: the import/processing screen during processing, with progress visible. Use a
   throwaway upload of one small chb13 file that you discard before it is processed, or the processing
   screen of a subject still in the list. Do not create or modify any subject that is part of the
   evaluation.
2. `fig3_6b_timeline.png`: `chb13_62` open on the detection timeline, with the selected event
   highlighted and the EEG view visible.
3. `fig3_6c_channel_panel.png`: the channel-level reconstruction-anomaly panel for that same event,
   with its title visible.
4. `fig3_6d_review.png`: the same event in review, with Accept, Reject and Uncertain visible, **before**
   any choice. Do not click any of them.

Before saving each screenshot, check that no calendar date, clock time or metric is visible. In §2 of
the handback, record for each PNG the recording, the event number and its file-relative onset and
offset in seconds.

## E. Figure 3.6

Execute Part B of `web_demo/CC_PROMPT_FIG3_6.md` with these screenshots. That part has its own commit.

## F. Finish

Stop the backend. Write the report to `F:/Study/Thesis/Agent/cc_reports/PART2_PART4.md` and print its
path. Make no other git commit.
