Do not build anything. Answer one question with a measurement.

Hypothesis: the zero-false-positive result in every seizure-containing chb13 file is an
artefact of `inter_mask=real_inter`, not a property of the system. Mechanism: preprocessing
excludes 4 h after each seizure from the interictal set, so in a seizure-containing file most
non-ictal windows are masked out of the false-positive count.

For each of the 33 chb13 files, using the same timeline construction as
src/figures/find_running_example.py, print: total windows, windows counted as real interictal
under `real_inter`, windows masked out, and whether the file contains a seizure.

Then answer directly: do the eight seizure-containing files have a materially lower share of
countable interictal windows than the twenty-five seizure-free files? Report the two means.

Second question, separate. docs/PROJECT_INSTRUCTIONS §11.1 records a measurement that
preprocessing drops windows and therefore the real interictal scores drift in time by
n_rejected. Quantify it for chb13: how many interictal windows were dropped, and what is the
cumulative time drift in seconds by the end of the recording? Read it from the committed
arrays and the summary files; do not estimate.

Report both answers. Change no figure and no document.