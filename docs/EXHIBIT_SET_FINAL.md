# Exhibit Set — Final

The authoritative list of what the report contains. It **supersedes the Result table of
`docs/EXHIBIT_TRIAGE.md`**, which recorded a decision made before four further changes. The triage's
reasoning is unchanged and still the record of why each cut was made; only its final count is out of
date.

A decision record is not edited after the fact. This file records what changed and why, and the
triage stays as written.

---

# What changed after the triage

| Change | Reason |
|---|---|
| **Figure 1.3 cut** | The reference thesis puts its detailed pipeline in Chapter 2 and has one figure in Chapter 1. Two flow diagrams of the same system, one abridged and one complete, is one too many. |
| **Figure 2.7 merged into Figure 2.6** | Opening the autoencoder inside the pipeline figure shows the latent representation feeding one readout and the two decoders feeding another. A separate architecture figure could not show that relationship. |
| **Figure 2.12 and 2.13 split again** | Merging them saved a line in the list of figures and no space at all. They are also referenced from two sections ten pages apart. |
| **Figure 2.11 cut** | Panel (a) was four equations in four boxes; equations belong in the text. Panel (b) is carried by Table 2.9. |

Net: 51 as the triage projected, reached by a different route.

---

# Figures

Twenty-two exist. One waits on the application.

| Chapter | Figures | Count |
|---|---|---|
| 1 | 1.1 seizure phases · 1.2 connectivity · 1.4 research framework | 3 |
| 2 | 2.1 montage · 2.3 raw against preprocessed · 2.4 graph construction · 2.6 pipeline · 2.8 reconstruction inversion · 2.12 application architecture · 2.13 timeline replay · 2.14 event scoring | 8 |
| 3 | 3.1 separation · 3.3 curves · 3.4 detection output · 3.5 latency · 3.6 operating curve · 3.8 window against event · 3.10 false positive · 3.11 attribution synthetic · 3.13 rank heatmap · 3.15 diffuseness · **3.16 application screen (pending)** | 10 + 1 |
| 4 | 4.1 comparison | 1 |

**Drawn by code, in `src/figures/`:** 1.1, 1.2, 2.3, 2.4, 2.8, 2.12, 2.13, 2.14, 3.1, 3.3, 3.4, 3.5,
3.6, 3.8, 3.10, 3.11, 3.13, 3.15, 4.1. Nineteen. Each carries a numeric self-check against
`docs/VERIFIED_NUMBERS.md` and stops rather than drawing a value it cannot confirm.

**Drawn by hand:** 1.4, 2.1, 2.6. Three.

---

# Tables

Twenty-eight, of which two wait on the application or on the finished chapters.

| Chapter | Tables |
|---|---|
| 1 | 1.1 · 1.2 · 1.3 |
| 2 | 2.1 · 2.3 · 2.4 · 2.6 · 2.7 · 2.8 · 2.9 · 2.10 |
| 3 | 3.2 · 3.3 · 3.4 · 3.5 · 3.6 · 3.8 · 3.9 · 3.10 · 3.12 |
| 4 | 4.1 · 4.2 |
| Appendix | A.1 · A.2 · A.4 · A.5 · A.6 |

Every one is written in `tables/`, except Table 2.1's non-corpus rows, which need each corpus's own
documentation opened and cited, and Table 3.12, which is written last from the finished chapters.

---

# Archived

Nine figures in `figures/archive/`, with the reason for each in its README. Nine tables removed from
the chapter files; what their content becomes is listed at the end of `docs/CAPTIONS.md`.

Archived, not deleted. A cut can be reversed, and re-running a generator puts its figure back at the
root of `figures/`.

---

# Two things still open

**Renumbering.** The cuts leave gaps: there is no Figure 1.3, 2.2, 2.5, 2.7, 2.9, 2.10, 2.11, 3.2,
3.7, 3.9, 3.12 or 3.14, and no Table 2.2, 2.5, 2.11, 2.12, 3.1, 3.7, 3.11, A.3 or A.7. Closing them is
one pass across the figure filenames, `docs/CAPTIONS.md`, and the cross-references in the five table
files. Do it **once**, after the application screen exists, not piecemeal.

**The editable sources are gone.** `figures/drawio_sources/` was deleted. The three hand-drawn figures
exist only as PNG, so a one-word change means redrawing. If the `.drawio` files survive outside the
repository, keep them.
