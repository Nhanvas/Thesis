# SzScan Step 3 — exploratory expert review with Dr. An: protocol (chat C5c, written before any clip is selected)

Status: **approved by the author 27/11 10:30** (with the review page of §8 recording the time per clip). Committed
before `src/c5_step3_clips.py` runs; any later change is logged here with what had been seen. Basis: `results/c5_szscan/C5_HANDOFF.md` §6 (layout and literature), the author's decisions of 26/11
(C5c prompt: (a) 8 anchor clips, 4 Siena + 4 CHB-MIT test patients; (b) 24 clips if about 1 h, otherwise 12 + 6;
(c) no reading-time comparison — time per clip recorded descriptively, usual reading time asked in the interview),
`EUREKA_PLAN.md` §13, integrity rules 7, 8 and 10.

## 1. Question and what the session can and cannot show

- **Question:** how does an experienced epileptologist classify the segments SzScan flags on two real hospital
  recordings, compared with segments it does not flag — and does she want such segments shown to her?
- **Level:** one reader, two recordings, one session → **exploratory expert review** (descriptive counts). No
  sensitivity, no specificity, no claim of clinical validation (integrity rule 10; DECIDE-AI stage: early, Vasey et al.
  2022, DOI 10.1038/s41591-022-01772-9). Inter-rater agreement on single experts is moderate even for ictal patterns
  (Halford et al. 2015, DOI 10.1016/j.clinph.2014.11.008), so one reader's label is an opinion, not a reference.
- **Anchors** (annotated public data) show how her labels relate to an existing annotation on the same screen; they are
  not used to estimate her accuracy.

## 2. Session order (about 60 min; 40 min if she has less time)

1. Consent and data use (§6), 5 min.
2. **Blinded clip review** (§3–§4), 30 min (24 clips) or 15 min (18 clips).
3. **Demo of SzScan** on a hospital recording (private study clin01, session mode), 10 min — after the clip review, so
   the review is not unblinded by the demo.
4. **Semi-structured interview** (§5), 15 min.

## 3. Clips — selection rules (deterministic; seed 20261127 only for the random parts)

All clips are **60 s**, the 18 bipolar derivations of the application's filtered signal (0.5–60 Hz band-pass and the
study's notch, the values verified by G9), in µV. An event clip starts **15 s before the event's onset** (the onset is
visible); a seizure clip starts 15 s before the annotated onset; clips are moved inward to stay inside the file, and a
clip never contains signal loss. Events and scores come from the application's database (session mode, the default),
the peak score of an event = the maximum of the file's `{stem}.score.npy` over the event's windows.

**Hospital clips** (private studies clin01 13.2 h, clin02 1.25 h; C3 of clin02 interpolated as in the thesis run):

| set | 24-clip version | 18-clip version | rule |
|---|---|---|---|
| flagged, highest score | 5 | 4 | the AI events of both recordings pooled, ranked by peak score, the top ones |
| flagged, random | 5 | 3 | uniformly at random among the remaining AI events (seed) |
| control | 6 | 5 | random 60-s segments at least 5 min from any AI event, in the two recordings in proportion to their duration (rounded, at least 1 per recording), not in the first or last minute (seed) |

If a recording has fewer events than a set needs, the set takes what exists and the controls make up the count.

**Anchor clips** (public, annotated; session-mode studies of the 8 CHB-MIT test patients and the 14 Siena patients).
Matching as SzCORE's tolerance: an AI event overlapping [annotated onset − 30 s, offset + 60 s] finds that seizure.

| category | 24-clip version (8) | 18-clip version (6) | rule within the category and dataset |
|---|---|---|---|
| seizure found | 2 Siena + 1 CHB-MIT | 1 + 1 | the found seizure whose duration is closest to the median duration of the found seizures of that dataset |
| seizure missed | 1 Siena + 1 CHB-MIT | 1 + 1 | the same rule among the missed seizures |
| false alarm | 1 Siena + 2 CHB-MIT | 1 + 1 | the false-alarm events of that dataset ranked by peak score, the highest |

Within a dataset no two anchors come from the same patient (the next one by the rule is taken); ties → the smaller
patient id, then the earlier time.

**Order and blinding:** the clips are shuffled with the seed and numbered C01 … C24 (or C18); the doctor sees no score,
no event shading, no dataset, no patient, no time of day — only the clip number, the 18 traces with their names, a
100-µV scale bar, 1-s grid lines, the filter ("0.5–60 Hz, notch 50 Hz" or "60 Hz") and, for clin02 clips, the note
"C3 interpolated". She may ask for the gain to be halved (a second page is ready for every clip). The key (which clip is
which) stays in the private folder until the ratings are saved.

## 4. Form per clip (Vietnamese; terms of the IFCN glossary, Kane et al. 2017, DOI 10.1016/j.cnp.2017.07.002)

1. **Class:** seizure (ictal pattern) · interictal epileptiform discharge · artifact (muscle / eye movement / electrode /
   movement / other) · physiological activity or normal variant (incl. sleep) · normal background · uncertain.
2. **Confidence:** 1 (very unsure) … 5 (certain).
3. **"Would you want the system to show you this segment when reading the recording?"** yes / no / not sure.
4. Comment (optional).
**Time per clip:** recorded by the review page (time the clip is on screen, summed if she returns to it) — descriptive
only. (The application's action log cannot time a blinded clip: the application always shades events and shows
scores; the author's decision (c) asked for the time per clip, which the page records instead.)

## 5. Interview guide (topics; the Vietnamese wording is in `vi/HUONG_DAN_PHONG_VAN.md`)

- Workflow (approved 25/11): one file or many per patient; length of a recording session; read during or after the
  recording; her usual time to read a recording of that length.
- Which false alarms disturb most; whether an artifact label on an event would help.
- Acceptable review share: at its default the system shows about 2 % of a recording (57 % of the test seizures);
  6–11 % shows 77–86 % at 4–7 × the false alarms (V1, hand-off item (13)) — which would she choose?
- What the review screen lacks (montages, gain, video, export); what would build trust.
- What Nguyễn Tri Phương Hospital could support next (annotated recordings, a reader study) — information only.

## 6. Consent and data use (points to agree before starting; `vi/DONG_Y.md`)

- Participation is voluntary; she may stop at any time; nothing is recorded except her answers on the form, the times
  per clip and the author's interview notes (no audio unless she agrees).
- How her opinion may be cited (her choice): by name and title / as "an epileptologist at a partner hospital" / not
  cited; on the Euréka slides only at the level the review took place ("exploratory expert review").
- The two recordings: their permission status as recorded in the project (board R233 (d), project files only); whether
  she confirms it in writing, and whether a de-identified copy or an ethics procedure is needed before any further use.
  Hospital data never leave the laptop.

## 7. Report (after the session; `results/c5_szscan/step3/REVIEW.md`, public, counts only)

Counts of her classes by set (flagged high / flagged random / control / anchor category); her "show me" answers by set;
anchors: her class against the annotation (descriptive); median confidence and time per clip; interview notes as
quotes she approved. No hospital time, file name or header field. Handed to C8 at the level it took place.

## 8. Implementation

`src/c5_step3_clips.py` (selection by §3 from the database read only; 60 s of the verified filtered cache; images of
two 30-s pages at two gains; the offline review page `review.html` in Vietnamese, which keeps the answers and the time
per clip and downloads them as CSV; the key) writes only to `F:/Study/Thesis/Eureka/C5_review/` (private; never
committed); `src/c5_step3_report.py` turns the key and the answers into `REVIEW.md` and `anchors.csv` (public, counts
and public anchors only) and a private every-clip table; synthetic test `src/c5_step3_test.py` (T1–T9, every rule of §3
checked against a hand-derived selection) before the real run. Vietnamese material for the session in `vi/`.
