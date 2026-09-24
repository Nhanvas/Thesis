// SZSCAN_DESIGN_v2.md §2 — event color rules, shared by every view that draws an event
// (MiniTimeline's Detections row, EegPanel's Event Time row, PanelEvent's list) so the
// three can't drift out of sync with each other. Three independent axes always show
// simultaneously — source, review-status, interaction — none ever overwrites another.
import tokens from './design-tokens.js'

// Axis 1 (source) + axis 2 (review-status, AI only), combined — used on the mini-timeline
// and Event Time row. CC_STEP6_FIX_PROMPT.md item 3 (Boti's decision): every block is now
// full-opacity solid colour and Reject's hatch is dropped — "AI chưa review = charcoal đặc
// · Human = blue đặc · Accept = green đặc · Reject = red đặc · Uncertain = vàng đặc". This
// relaxes SZSCAN_DESIGN_v2.md principle 3 ("never colour alone") for these blocks
// specifically — status text still appears on the Event Panel row and its badges.
export function blockStyle(event) {
  if (event.source === 'Human') {
    return { color: tokens.colorHuman, opacity: 1, hatch: false }
  }
  switch (event.review_status) {
    case 'Accept':
      return { color: tokens.colorAccept, opacity: 1, hatch: false }
    case 'Reject':
      return { color: tokens.colorReject, opacity: 1, hatch: false }
    case 'Uncertain':
      return { color: tokens.colorUncertain, opacity: 1, hatch: false }
    default: // 'Unseen'
      return { color: tokens.colorAi, opacity: 1, hatch: false }
  }
}

// CC_STEP6_FIX_PROMPT.md item 4: the Event Time strip (EegPanel.jsx) prints the event's own
// name inside its block in white — illegible on the new #FFE262 Uncertain fill (found live
// while verifying this fix round, not called out by name in the prompt's own location list,
// but "Event Time strip block" is). Every other status's fill is dark enough for white text.
export function blockLabelColor(event) {
  if (event.source === 'AI' && event.review_status === 'Uncertain') return tokens.colorUncertainText
  return '#FFFFFF'
}

// Axis 3 (interaction) — "khi đang xem 1 event: các event khác giảm còn opacity ~40%
// (không đổi màu), event đang chọn giữ nguyên độ đậm". Additive: never replaces blockStyle's
// own color/opacity for the selected event, only dims the others.
export function dimOpacity(event, selectedEventId, baseOpacity) {
  if (selectedEventId == null || event.id === selectedEventId) return baseOpacity
  return 0.4
}

// Panel Event list's ~4-5px left bar: review-status color for AI (its own axis), source
// color for Human (no review axis to show instead).
export function listBarColor(event) {
  if (event.source === 'Human') return tokens.colorHuman
  switch (event.review_status) {
    case 'Accept':
      return tokens.colorAccept
    case 'Reject':
      return tokens.colorReject
    case 'Uncertain':
      return tokens.colorUncertain
    default:
      return tokens.colorUnseen
  }
}

// Panel Event list row's "very light" background tint (§2: "Nền dòng chỉ tô rất nhạt").
// No §2 token exists for a Human-specific light tint, so this reuses the same blue-tinted
// "selected row" background the Database screen already uses (SZSCAN_DESIGN_v2.md §5) —
// staying inside the existing palette rather than inventing a new color.
export function listRowBg(event) {
  if (event.source === 'Human') return '#EFF6FF'
  switch (event.review_status) {
    case 'Accept':
      return tokens.colorAcceptBg
    case 'Reject':
      return tokens.colorRejectBg
    case 'Uncertain':
      return tokens.colorUncertainBg
    default:
      return '#F8FAFC'
  }
}
