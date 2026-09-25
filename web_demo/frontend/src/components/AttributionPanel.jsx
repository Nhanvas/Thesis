import { useEffect, useState } from 'react'
import { getAttribution, saveAttributionStatus } from '../api.js'
import { ELECTRODES, CHANNEL_PAIRS, HEAD_CENTER, HEAD_RADIUS, scoreColors } from '../attributionStyle.js'
import tokens from '../design-tokens.js'

// Channel Attribution Panel (Step 7, CC_STEP7_PROMPT.md Part 3 / SZSCAN_SPEC_v5.md §6.7).
// XAI for the GAE reconstruction branch — NOT localization, NOT SOZ (THESIS_CONTEXT_FOR_
// DEMO.md §5). Syncs to whichever event Panel Event currently has selected (AI or Human);
// AnalysisScreen passes that event object (or null) in as `event` — this component holds no
// sync state of its own, same division of responsibility as PanelEvent.

const [HEAD_CX, HEAD_CY] = HEAD_CENTER

function StatusPill({ active, tone, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex-1 rounded-control px-2 py-1 text-[11px] font-medium border ${
        active
          ? tone === 'accept'
            ? 'bg-accept text-white border-accept'
            : 'bg-reject text-white border-reject'
          : 'border-border text-text-secondary bg-surface'
      }`}
    >
      {children}
    </button>
  )
}

export default function AttributionPanel({ event }) {
  const [data, setData] = useState(null)
  const [statuses, setStatuses] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [hoveredChannel, setHoveredChannel] = useState(null)

  // Re-fetches when the selected event's id OR range changes (Edit on a Human event) — not
  // on `name`, which is a read-time renumbering derived elsewhere and doesn't affect scores;
  // the title below reads `event.name` straight from the prop so renumbering shows up
  // immediately without a refetch.
  useEffect(() => {
    setHoveredChannel(null)
    if (!event) {
      setData(null)
      setStatuses({})
      setError('')
      return undefined
    }
    let cancelled = false
    setLoading(true)
    setError('')
    getAttribution(event.id)
      .then((d) => {
        if (cancelled) return
        setData(d)
        const init = {}
        if (d.available) {
          for (const r of d.rows) if (r.status) init[r.channel] = r.status
        }
        setStatuses(init)
      })
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [event?.id, event?.onset_sec, event?.offset_sec])

  async function handleSave() {
    if (!event) return
    setSaving(true)
    setError('')
    try {
      await saveAttributionStatus(event.id, statuses)
      const d = await getAttribution(event.id)
      setData(d)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  function handleClearAll() {
    setStatuses({})
  }

  function setChannelStatus(channel, status) {
    setStatuses((s) => ({ ...s, [channel]: status }))
  }

  // CC_STEP7_FIX_PROMPT.md Part B: UI/B2a stacks Event Panel + Attribution Panel in the right
  // column with the column's total height fixed to the EEG card's height, each panel
  // scrolling internally. `h-full` here fills whatever height AnalysisScreen's flex layout
  // gives this component's wrapper (see that file's "absolute inset-0" right-column
  // technique) — every branch below keeps the same `h-full flex flex-col` shell so the
  // column height stays put regardless of which state (empty/loading/unavailable/data) is
  // showing.
  if (!event) {
    return (
      <div className="border border-border bg-surface h-full flex flex-col">
        <div className="p-4 text-xs text-text-muted">Select an event to view attribution</div>
      </div>
    )
  }

  const title = `Channel-level reconstruction anomaly — ${event.name}`
  const colors = data?.available ? scoreColors(data.rows) : {}

  return (
    <div className="border border-border bg-surface h-full min-h-0 flex flex-col">
      {/* Part B item 4: ONE scroll region holds colorbar -> head diagram -> title -> table
          (including its header row); Save/Clear all live outside it, in a pinned footer that
          is never scrolled — see the sibling div below this one. */}
      <div className="flex-1 min-h-0 overflow-y-auto">
        {loading && (
          <>
            <div className="px-3 py-2.5 border-b border-border">
              <h3 className="text-sm font-semibold">{title}</h3>
            </div>
            <div className="p-4 text-xs text-text-muted">Loading…</div>
          </>
        )}
        {!loading && error && (
          <>
            <div className="px-3 py-2.5 border-b border-border">
              <h3 className="text-sm font-semibold">{title}</h3>
            </div>
            <div className="p-4 text-xs text-reject">{error}</div>
          </>
        )}
        {!loading && !error && data && !data.available && (
          <>
            <div className="px-3 py-2.5 border-b border-border">
              <h3 className="text-sm font-semibold">{title}</h3>
            </div>
            <div className="p-4 text-xs text-text-muted">Attribution is not available for this file.</div>
          </>
        )}

        {!loading && !error && data?.available && (
          <>
            <div className="px-3 pt-3">
              <div
                className="h-2 rounded-full mb-2"
                style={{
                  background: `linear-gradient(to right, ${tokens.colorAttrLow}, ${tokens.colorAttrMid}, ${tokens.colorAttrHigh})`,
                }}
              />
              <svg viewBox="0 0 200 200" className="w-full" style={{ maxHeight: 260 }}>
                <circle cx={HEAD_CX} cy={HEAD_CY} r={HEAD_RADIUS} fill="none" stroke={tokens.colorBorderStrong} strokeWidth={1.5} />
                <polygon points="90,17 110,17 100,3" fill="none" stroke={tokens.colorBorderStrong} strokeWidth={1.5} />

                {CHANNEL_PAIRS.map(({ name, a, b }) => {
                  const [x1, y1] = ELECTRODES[a]
                  const [x2, y2] = ELECTRODES[b]
                  const isHovered = hoveredChannel === name
                  const status = statuses[name]
                  const stroke = isHovered ? tokens.colorInteraction : colors[name] || tokens.colorAttrLow
                  const opacity = status === 'Reject' ? 0.35 : 1
                  return (
                    <line
                      key={name}
                      x1={x1}
                      y1={y1}
                      x2={x2}
                      y2={y2}
                      stroke={stroke}
                      strokeWidth={isHovered ? 4.5 : 3.2}
                      strokeOpacity={opacity}
                      strokeLinecap="round"
                      style={{ cursor: 'pointer' }}
                      onMouseEnter={() => setHoveredChannel(name)}
                      onMouseLeave={() => setHoveredChannel(null)}
                    />
                  )
                })}

                {Object.entries(ELECTRODES).map(([name, [x, y]]) => (
                  <g key={name}>
                    <circle cx={x} cy={y} r={9} fill={tokens.colorSurface} stroke={tokens.colorBorder} strokeWidth={1} />
                    <text x={x} y={y + 2.5} fontSize={5.5} textAnchor="middle" fill={tokens.colorTextMuted} fontFamily={tokens.fontMono}>
                      {name}
                    </text>
                  </g>
                ))}
              </svg>
            </div>

            {/* Part B item 5: title sits between the head diagram and the table in UI/B2a,
                not above the colorbar (moved from the old top-of-panel header bar). */}
            <div className="px-3 py-2.5">
              <h3 className="text-sm font-semibold">{title}</h3>
            </div>

            <table className="w-full text-xs">
              <thead>
                <tr className="text-[11px] font-semibold text-text-muted border-t border-b border-border">
                  <th className="text-left px-3 py-1.5 w-10">Rank</th>
                  <th className="text-left px-1 py-1.5">Channel</th>
                  <th className="text-left px-1 py-1.5 w-20">Score</th>
                  <th className="text-left px-1 py-1.5 w-36">Status</th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((r) => (
                  <tr
                    key={r.channel}
                    onMouseEnter={() => setHoveredChannel(r.channel)}
                    onMouseLeave={() => setHoveredChannel(null)}
                    className={`border-b border-border ${hoveredChannel === r.channel ? 'bg-bg' : ''}`}
                  >
                    <td className="px-3 py-1 font-mono">{r.rank}</td>
                    <td className="px-1 py-1 font-mono">{r.channel}</td>
                    <td className="px-1 py-1 font-mono">{r.score.toFixed(2)}</td>
                    <td className="px-1 py-1">
                      <div className="flex gap-1">
                        <StatusPill active={statuses[r.channel] === 'Accept'} tone="accept" onClick={() => setChannelStatus(r.channel, 'Accept')}>
                          Accept
                        </StatusPill>
                        <StatusPill active={statuses[r.channel] === 'Reject'} tone="reject" onClick={() => setChannelStatus(r.channel, 'Reject')}>
                          Reject
                        </StatusPill>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>

      {!loading && !error && data?.available && (
        <div className="flex gap-2 p-3 border-t border-border shrink-0">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="flex-1 bg-brand text-white rounded-control px-3 py-1.5 text-sm font-medium disabled:opacity-60"
          >
            Save
          </button>
          <button
            type="button"
            onClick={handleClearAll}
            className="flex-1 border border-border text-text-secondary rounded-control px-3 py-1.5 text-sm font-medium"
          >
            Clear all
          </button>
        </div>
      )}
    </div>
  )
}
