# Reviewer Rules for the Thesis Report

**Purpose:** checkable rules for the final report, drawn from general lessons that also apply to this thesis.
**Use:** checklist per chapter (Step C) and in the final review pass. Status APPLY/ADAPT = must hold in v5; ALREADY = verify only; CONFLICT = do not apply.
**Source:** from reviewer feedback (2 reviewers + editor) on the earlier conference paper (different system, same dataset). Verified project facts and author decisions override reviewer points.

| ID | Tag | Rule | Check | Status |
|---|---|---|---|---|
| R1 | Abstract/Ch1/Ch5 | Back every Abstract, contribution and Conclusion claim with a Ch3 number or exhibit; move anything not measured to Future Work. | Trace claims to Ch3 | APPLY |
| R2 | All | Describe channel-level latent anomaly as XAI concordance with its negative result, never as propagation or SOZ. | Search "propagat", "SOZ" | ADAPT: measured here; report the negative, not a capability |
| R3 | Ch2 | Justify connectivity measures correctly: wPLI ignores zero-lag coupling; AEC does not. | Volume-conduction sentences | ADAPT: claim zero-lag insensitivity for wPLI only |
| R4 | Ch2 | State the bipolar montage, the CAR step, and that bipolar pairs sharing an electrode can couple; never read edges as anatomical links. | Montage named | APPLY |
| R5 | Ch2 | State the notch used for each dataset: CHB-MIT 60 Hz, Siena 50 Hz (confirmed in the pre-registered external-validation code), plus Siena's montage mapping and resampling to 256 Hz. | Notch per dataset | APPLY |
| R6 | Ch2 | Report every parameter needed to reproduce the method: how wPLI/AEC are estimated in one 4 s window, bands, top-k, smoothing, budget, merge, running-median width, CPD settings. | Parameter list complete | APPLY |
| R7 | Ch2 | Count recording cases and individuals separately (chb01 = chb21) and list identifiers per partition. | Split table | ADAPT: both in training; state counts |
| R8 | Ch3/Ch4 | State gains against a fair same-protocol reference, never a weak strawman. | Reference named | ADAPT: earlier system, DynaSD-Siena; no new runs |
| R9 | All | Keep numbers identical across Abstract, text, tables and figures, and label each one (pooled/subject-mean, seed 42/4-seed, held-out/final). | Cross-check Abstract–Ch3–Ch5 | ALREADY |
| R10 | Ch4 | Compare only identically defined metrics, with a protocol note per entry; never rank different protocols. | Comparison table | ALREADY |
| R11 | Ch1/Ch4 | Quote the cited paper's wording for claims about its protocol, or label the claim as inference. | Protocol claims cited | APPLY |
| R12 | Refs | Cite the primary source of every dataset and method (Shoeb 2009, PhysioNet, Siena, wPLI, AEC, GAE, Ledoit–Wolf, kernel CPD, SzCORE); cite every listed entry; each citation supports its own sentence. | Method-to-reference map | APPLY |
| R13 | Ch2/Ch3/Figures | Describe the frozen system only; leave no residue of earlier versions. | Search coherence, GAT, PELT | ALREADY |
| R14 | Ch1/Ch2/Ch4 | Do not claim a design element causes the result unless an existing comparison shows it. | Causal claims have evidence | ADAPT: soften or cite existing evidence |
| R15 | Ch2 | State which recording time is evaluated and every exclusion or label use (skipped files, z-score statistics). | Disclosures present | ALREADY |
| R16 | Ch4 | Test simpler explanations (annotation boundaries, short seizures, drift) before architectural ones; base each diagnosis on evidence shown. | Alternatives per failure | APPLY |
| R17 | Ch3 | Evaluate events on continuous recordings: sensitivity, FP/day, onset/offset error, per-subject table, bootstrap intervals. | Event metrics + intervals | ALREADY |
| R18 | Ch1/Ch5 | Keep the clinical claim at post-hoc review triage, not warning or real time. | Search "real-time", "warning" | ALREADY |
| R19 | Ch3 | Name metrics correctly; precision, F1, FP/day from scorer counts; no "specificity" for recall. | Term vs definition | ALREADY |
| R20 | Ch2 | Describe the normalisation order once, and say how amplitude information survives it. | One description | APPLY |
| R21 | Ch2 | Give a rationale beside every chosen threshold or value. | Rationale per value | APPLY |
| R22 | Ch2/Ch4 | Disclose that non-test selection overestimates test results and that the final step used test information. | Disclosure present | ALREADY |
| R23 | Ch3/Ch5 | State measurements directly, hedge only interpretation, quantify instead of "severe", and say each point once. | Hedge and duplicate scan | APPLY |
| R24 | Figures | Make figure text, dimensions and term names match the body; legends never cover data. | Per-figure check | APPLY |
| R25 | Figures | Make each caption self-explanatory. | Caption content | ADAPT: short title; explain colours in legend or text |
| R26 | All | Define every term at first use and use it the same way everywhere. | Glossary pass | ALREADY |
| R27 | Ch2 | Add one sentence on each dataset's origin, de-identification and licence. | Data-use sentence | APPLY |
| R28 | Front matter | Follow the format template; no template residue; correct affiliation. | vs Report format.md | ADAPT: university format, not Springer |
| R29 | Ch2 | Add a code-availability statement. | — | CONFLICT: author decision: no source-code link, no appendix |
| R30 | Ch3 | Report accuracy, AUC or chance-level AP as main metrics. | — | CONFLICT: event-level SzCORE is the protocol; window metrics not reported |
| R31 | Ch3/Ch4 | Add new baselines, ablations or re-runs (graph-free control, other GNN). | — | CONFLICT: no new experiments; supervised or feature-only system is Future Work |
| R32 | — | GAT attention, beta coherence, preictal classes, old 50 Hz notch, Welch MSC. | — | N/A-OLD-SYSTEM |

## Top risks for this thesis
1. Abstract or Conclusion claiming more than Ch3 shows: attribution, clinical use (R1, R2, R18).
2. Number mix-ups between held-out and final results, seed 42 and 4 seeds, pooled and subject-mean (R9).
3. Comparisons across different protocols (R8, R10, R11).
4. Wrong or incomplete method justifications: wPLI/AEC, montage and CAR, parameters, Siena notch (R3–R6).
5. Missing primary references or uncited entries (R12).
6. Causal claims about the graph or the GAE without evidence (R14).
