import { useState } from 'react'
import { ChevronDownIcon, PersonIcon } from './icons.jsx'
import { formatFileTime, formatDurationShort } from '../time.js'
import { listBarColor, listRowBg } from '../eventStyle.js'

// Panel Event (SZSCAN_SPEC_v5.md §6.5) — two-tier filter, event list, expand-in-place
// review UI. "Panel Event là nguồn điều khiển chính": clicking a row is what drives Panel
// EEG + the mini-timeline playhead (see AnalysisScreen's handleSelectEvent) — this
// component only renders and reports clicks/saves/deletes, it holds no sync state itself.

const AI_SUBFILTERS = ['Accept', 'Reject', 'Uncertain', 'Unseen']

function EmptyState({ noEventsAtAll }) {
  if (noEventsAtAll) {
    return (
      <div className="p-4 text-xs text-text-muted">
        No detected events in this file. You can still add an event manually with Select Range.
      </div>
    )
  }
  return <div className="p-4 text-xs text-text-muted">No events match this filter.</div>
}

function AiExpand({ ev, fileMeta, onSave, onClearError }) {
  const [status, setStatus] = useState(ev.review_status)
  const [comment, setComment] = useState(ev.comment)

  const onsetLabel = fileMeta ? formatFileTime(fileMeta.start_time, ev.onset_sec, fileMeta.usable_duration_seconds) : ''
  const offsetLabel = fileMeta ? formatFileTime(fileMeta.start_time, ev.offset_sec, fileMeta.usable_duration_seconds) : ''

  return (
    <div className="px-3 py-2.5 border-t border-border bg-surface text-xs space-y-2">
      <div className="grid grid-cols-2 gap-y-1 font-mono text-text-secondary">
        <span>Onset: {onsetLabel}</span>
        <span>Offset: {offsetLabel}</span>
        <span>Duration: {formatDurationShort(ev.duration_sec)}</span>
      </div>
      <div className="flex gap-1.5">
        {['Accept', 'Reject', 'Uncertain'].map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => {
              setStatus(s)
              // CC_STEP5_FIX2_PROMPT.md item 4: picking a status after the "review_status
              // must be one of Accept/Reject/Uncertain." error is exactly what that error
              // was asking for — clear it here rather than leaving it stuck on screen.
              onClearError?.()
            }}
            className={`flex-1 rounded-control px-2 py-1 text-[11px] font-medium border ${
              status === s
                ? s === 'Accept'
                  ? 'bg-accept text-white border-accept'
                  : s === 'Reject'
                    ? 'bg-reject text-white border-reject'
                    : // CC_STEP6_FIX_PROMPT.md item 4: the new #FFE262 fill is too light for
                    // white text (unlike Accept/Reject's darker fills) — dark text-uncertain-text
                    // instead, the one legibility deviation this fix round makes on its own
                    // judgment rather than by explicit instruction; flagged in the report.
                    'bg-uncertain text-uncertain-text border-uncertain'
                : 'border-border text-text-secondary bg-surface'
            }`}
          >
            {s}
          </button>
        ))}
      </div>
      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="Comment"
        rows={2}
        className="w-full border border-border rounded-control px-2 py-1 text-xs resize-none"
      />
      <button
        type="button"
        onClick={() => onSave(ev.id, { review_status: status, comment })}
        className="w-full bg-brand text-white rounded-control px-2 py-1.5 text-xs font-medium"
      >
        Save
      </button>
    </div>
  )
}

function HumanExpand({ ev, fileMeta, onSave, onDelete, onEdit, isEditing }) {
  const [comment, setComment] = useState(ev.comment)

  const onsetLabel = fileMeta ? formatFileTime(fileMeta.start_time, ev.onset_sec, fileMeta.usable_duration_seconds) : ''
  const offsetLabel = fileMeta ? formatFileTime(fileMeta.start_time, ev.offset_sec, fileMeta.usable_duration_seconds) : ''

  return (
    <div className="px-3 py-2.5 border-t border-border bg-surface text-xs space-y-2">
      <div className="grid grid-cols-2 gap-y-1 font-mono text-text-secondary">
        <span>Onset: {onsetLabel}</span>
        <span>Offset: {offsetLabel}</span>
        <span>Duration: {formatDurationShort(ev.duration_sec)}</span>
      </div>
      {isEditing ? (
        <div className="rounded-control border border-dashed border-interaction px-2 py-1.5 text-[11px] text-interaction">
          Click two points on the EEG grid to redraw this event.
        </div>
      ) : (
        <div className="flex gap-1.5">
          <button
            type="button"
            onClick={() => onDelete(ev.id)}
            className="flex-1 border border-reject text-reject rounded-control px-2 py-1 text-[11px] font-medium"
          >
            Delete
          </button>
          <button
            type="button"
            onClick={() => onEdit(ev)}
            title="Redraw onset/offset via Select Range"
            className="flex-1 border border-border text-text-secondary rounded-control px-2 py-1 text-[11px] font-medium"
          >
            Edit
          </button>
        </div>
      )}
      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="Comment"
        rows={2}
        className="w-full border border-border rounded-control px-2 py-1 text-xs resize-none"
      />
      <button
        type="button"
        onClick={() => onSave(ev.id, { comment })}
        className="w-full bg-brand text-white rounded-control px-2 py-1.5 text-xs font-medium"
      >
        Save
      </button>
    </div>
  )
}

function EventRow({ ev, fileMeta, expanded, onToggle, onSave, onDelete, onEdit, isEditing, onClearError }) {
  const barColor = listBarColor(ev)
  const bg = expanded ? listRowBg(ev) : 'transparent'
  const onsetLabel = fileMeta ? formatFileTime(fileMeta.start_time, ev.onset_sec, fileMeta.usable_duration_seconds) : ''

  return (
    <div className={expanded ? 'ring-2 ring-inset ring-interaction' : ''}>
      <button
        type="button"
        onClick={() => onToggle(ev.id)}
        style={{ borderLeftColor: barColor, background: bg }}
        className="w-full flex items-center gap-2 pl-2 pr-2 py-2 border-l-4 text-left hover:bg-bg"
      >
        <span className="flex-1 text-sm font-medium truncate">{ev.name}</span>
        <span className="text-xs font-mono text-text-secondary shrink-0">{onsetLabel}</span>
        <span className="w-6 flex items-center justify-center shrink-0 text-text-secondary">
          {ev.source === 'AI' ? (
            <span className="text-[10px] font-mono font-semibold">AI</span>
          ) : (
            <PersonIcon className="w-4 h-4" />
          )}
        </span>
        <ChevronDownIcon className={`w-3.5 h-3.5 shrink-0 transition-transform ${expanded ? 'rotate-180' : ''}`} />
      </button>
      {expanded && (
        ev.source === 'AI' ? (
          <AiExpand ev={ev} fileMeta={fileMeta} onSave={onSave} onClearError={onClearError} />
        ) : (
          <HumanExpand ev={ev} fileMeta={fileMeta} onSave={onSave} onDelete={onDelete} onEdit={onEdit} isEditing={isEditing} />
        )
      )}
    </div>
  )
}

export default function PanelEvent({ events, fileMeta, selectedEventId, editingEventId, onToggleEvent, onSaveEvent, onDeleteEvent, onEditEvent, onClearError }) {
  const [menuOpen, setMenuOpen] = useState(false)
  const [aiSubmenuOpen, setAiSubmenuOpen] = useState(false)
  const [filter, setFilter] = useState({ kind: 'All', sub: null }) // kind: 'All'|'Human'|'AI'

  const humanEvents = events.filter((e) => e.source === 'Human')
  const aiEvents = events.filter((e) => e.source === 'AI')

  let displayed
  let countLabel
  let filterLabel
  if (filter.kind === 'Human') {
    displayed = humanEvents
    countLabel = `${humanEvents.length}`
    filterLabel = 'Human'
  } else if (filter.kind === 'AI') {
    displayed = aiEvents.filter((e) => e.review_status === filter.sub)
    countLabel = `${displayed.length}/${aiEvents.length}`
    filterLabel = filter.sub
  } else {
    displayed = events
    countLabel = `${events.length}`
    filterLabel = 'All'
  }

  function pick(kind, sub = null) {
    setFilter({ kind, sub })
    setMenuOpen(false)
    setAiSubmenuOpen(false)
  }

  return (
    <div className="border border-border bg-surface flex flex-col h-full min-h-0">
      <div className="flex items-center gap-2 px-3 py-2.5 border-b border-border relative" data-popover>
        <button
          type="button"
          onClick={() => setMenuOpen((o) => !o)}
          className="flex-1 border border-border rounded-control px-2 py-1.5 text-sm flex items-center justify-between"
        >
          <span>Filter: {filterLabel}</span>
          <ChevronDownIcon className="w-3.5 h-3.5" />
        </button>
        <span className="border border-border rounded-control px-3 py-1.5 text-sm font-mono min-w-[3rem] text-center">
          {countLabel}
        </span>

        {menuOpen && (
          <div className="absolute left-3 top-full mt-1 w-40 bg-surface border border-border rounded-control shadow-panel z-50 py-1">
            <button
              type="button"
              onClick={() => pick('All')}
              className={`w-full text-left px-3 py-1.5 text-sm ${filter.kind === 'All' ? 'bg-[#EFF6FF] font-semibold text-interaction' : 'hover:bg-bg'}`}
            >
              All
            </button>
            <button
              type="button"
              onClick={() => pick('Human')}
              className={`w-full text-left px-3 py-1.5 text-sm ${filter.kind === 'Human' ? 'bg-[#EFF6FF] font-semibold text-interaction' : 'hover:bg-bg'}`}
            >
              Human
            </button>
            <button
              type="button"
              onClick={() => setAiSubmenuOpen((o) => !o)}
              className={`w-full text-left px-3 py-1.5 text-sm flex items-center justify-between ${filter.kind === 'AI' ? 'bg-[#EFF6FF] font-semibold text-interaction' : 'hover:bg-bg'}`}
            >
              AI
              <ChevronDownIcon className={`w-3 h-3 transition-transform ${aiSubmenuOpen ? 'rotate-180' : ''}`} />
            </button>
            {aiSubmenuOpen && (
              <div className="pl-3 border-t border-border">
                {AI_SUBFILTERS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => pick('AI', s)}
                    className={`w-full text-left px-3 py-1.5 text-sm ${
                      filter.kind === 'AI' && filter.sub === s ? 'bg-[#EFF6FF] font-semibold text-interaction' : 'hover:bg-bg'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 px-3 py-1.5 text-[11px] font-semibold text-text-muted border-b border-border">
        <span className="flex-1">Event</span>
        <span className="shrink-0">Onset</span>
        <span className="w-6 shrink-0 text-center">Type</span>
        <span className="w-3.5 shrink-0" />
      </div>

      <div className="overflow-y-auto flex-1">
        {displayed.length === 0 ? (
          <EmptyState noEventsAtAll={events.length === 0} />
        ) : (
          displayed.map((ev) => (
            <EventRow
              key={ev.id}
              ev={ev}
              fileMeta={fileMeta}
              expanded={ev.id === selectedEventId}
              onToggle={onToggleEvent}
              onSave={onSaveEvent}
              onDelete={onDeleteEvent}
              onEdit={onEditEvent}
              isEditing={ev.id === editingEventId}
              onClearError={onClearError}
            />
          ))
        )}
      </div>
    </div>
  )
}
