Fix MiniTimeline.jsx for files longer than 1 hour (chb06 files run up to ~4 h). Its time
domain is hardcoded (DOMAIN_SEC = 3600), so once the playhead passes 1:00:00 the score line
and the Detections blocks disappear. SPEC 6.3: default 1 hour, 6 cells x 10 min, view-only.

Implement 1-hour pages that follow the playhead:
- pageStart = floor(playheadSec / 3600) * 3600; pageEnd = min(pageStart + 3600,
  usable_duration_seconds).
- Score line, Detections blocks, cell grid, time labels and playhead marker are all drawn
  for [pageStart, pageEnd). Events straddling a page edge are clipped to it. Labels keep the
  existing format (HH:MM:SS, dN: when >= 24 h, via time.js) and show FILE-relative time.
- Files <= 1 h must render exactly as today (single page) -- verify no visual change.
- The page flips automatically when the playhead crosses an hour boundary (playback, scrub
  bar and Event Panel row clicks already move the playhead). Add no controls and no
  interaction.
- Y-axis auto-scale stays P1-P99 of the WHOLE file's score, not of the page.
Touch nothing else beyond the prop wiring this needs. Add a dated SPEC 6.3 note (C26)
recording the page behaviour.

Guards 4/4. Live-verify via claude-in-chrome on a ~4 h chb06 file (jump to an event after
1 h; play across an hour boundary; click an Event Panel row in another hour) and on a <= 1 h
file (chb16) for no regression. If claude-in-chrome cannot connect, say so and give the
closest alternative -- never skip verification silently.
Report to CC_FIX_MINITIMELINE_REPORT.md.