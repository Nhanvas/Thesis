Clear the Memo of every subject in the app's SQLite DB (szscan.db). The current memos
contain internal build labels ("Step 9 phase 2 - full real dataset", "CC_STEP9_PHASE1B
timing run", ...) and the Database screen is committee-visible.

- Copy szscan.db to a backup inside web_demo/backend/ first (gitignored), print the current
  memos, then UPDATE subjects SET memo = '' and print the after-state. Touch nothing else:
  no files, events, review statuses.
- Confirm GET /api/subjects shows empty memos for all 8 subjects and that the Database
  screen renders the empty Memo column cleanly (no "null"/"undefined").
- Check whether anything else user-visible carries internal labels (export text, page
  titles, file/subject names). Report findings; do not fix silently.
Guards 4/4. Report to CC_FIX_CLEAR_MEMOS_REPORT.md.