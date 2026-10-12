# CC_FILECOUNT_AUDIT_REPORT.md — real .edf count vs DB file count

Read-only diagnostic. No files or database rows were modified.

- **real_edf_count**: files directly under `F:/Study/Thesis/Dataset/CHB-MIT/{subject}/`
  matching `*.edf` (case-insensitive), one directory level only. `*.edf.seizures` sidecar
  files are excluded — they don't match the `*.edf` pattern (extension is `.seizures`), and
  per CLAUDE.md they're label data the demo must never read anyway.
- **db_file_count**: `SELECT COUNT(*) FROM files WHERE subject_id = ?` against
  `web_demo/backend/szscan.db`.

| subject | real_edf_count | db_file_count | match |
|---------|----------------|---------------|-------|
| chb03   | 38             | 38            | yes   |
| chb06   | 18             | 18            | yes   |
| chb13   | 33             | 2             | no    |
| chb14   | 26             | 26            | yes   |
| chb15   | 40             | 40            | yes   |
| chb16   | 19             | 19            | yes   |
| chb17   | 21             | 21            | yes   |
| chb18   | 36             | 36            | yes   |

7 of 8 subjects match exactly. **chb13 is the one mismatch**: 33 real `.edf` files exist on
disk but only 2 are recorded in the `files` table.

This is consistent with recent commit history (`f34db2c` / `864d170`: "DB cleaned to real
data only (chb13, chb16)") — the `files` table only ever holds what was actually uploaded and
processed through the app's Create New flow, not automatically every `.edf` in the dataset
directory. A mismatch here means chb13 has only had 2 of its 33 recording files run through
the app so far, not that data is missing or corrupted. Flagging it since it's the only
subject where db_file_count is far below real_edf_count — worth confirming with Boti whether
that's the intended demo state for chb13 or whether more of its files were meant to be
processed.
