// Channel Attribution Panel (Step 7, CC_STEP7_PROMPT.md Part 3) — head-diagram geometry and
// the teal gradient color mapping (SZSCAN_DESIGN_v2.md §4). Kept separate from eventStyle.js
// since this axis (attribution score) is unrelated to the event source/review-status axes
// eventStyle.js covers.
import tokens from './design-tokens.js'

// 19 distinct electrodes for CHB-MIT's 18 bipolar channels (SZSCAN_SPEC_v5.md §6.7's "18
// electrode positions" read loosely — see the report). Simple 5-row schematic layout
// (proportions taken from UI/B2a, not a true stereographic 10-20 projection — the mockup
// itself uses the same simplified row-grid style), in a 0..200 square viewBox.
export const ELECTRODES = {
  FP1: [78, 45], FP2: [122, 45],
  F7: [38, 72], F3: [80, 74], FZ: [100, 74], F4: [120, 74], F8: [162, 72],
  T7: [20, 110], C3: [65, 110], CZ: [100, 110], C4: [135, 110], T8: [180, 110],
  P7: [38, 148], P3: [80, 146], PZ: [100, 146], P4: [120, 146], P8: [162, 148],
  O1: [78, 175], O2: [122, 175],
}

export const HEAD_CENTER = [100, 100]
export const HEAD_RADIUS = 85

// Pipeline channel order (src/dataprep/preprocessing.py COMMON_CHANNELS) — each split into
// its two electrodes for the "18 straight lines, no dots" requirement.
export const CHANNEL_PAIRS = [
  'FP1-F7', 'F7-T7', 'T7-P7', 'P7-O1',
  'FP1-F3', 'F3-C3', 'C3-P3', 'P3-O1',
  'FP2-F4', 'F4-C4', 'C4-P4', 'P4-O2',
  'FP2-F8', 'F8-T8', 'T8-P8', 'P8-O2',
  'FZ-CZ', 'CZ-PZ',
].map((name) => {
  const [a, b] = name.split('-')
  return { name, a, b }
})

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}
function rgbToHex([r, g, b]) {
  return `#${[r, g, b].map((v) => Math.round(v).toString(16).padStart(2, '0')).join('')}`
}
function lerpRgb(c1, c2, t) {
  return [c1[0] + (c2[0] - c1[0]) * t, c1[1] + (c2[1] - c1[1]) * t, c1[2] + (c2[2] - c1[2]) * t]
}

const LOW = hexToRgb(tokens.colorAttrLow)
const MID = hexToRgb(tokens.colorAttrMid)
const HIGH = hexToRgb(tokens.colorAttrHigh)

// SZSCAN_DESIGN_v2.md §4's 3-stop colorbar (`linear-gradient(to right, low, mid, high)`) as a
// continuous function of t in [0,1] — matches the CSS gradient exactly at t=0/0.5/1.
export function attrColorAt(t) {
  const clamped = Math.max(0, Math.min(1, t))
  return rgbToHex(clamped <= 0.5 ? lerpRgb(LOW, MID, clamped * 2) : lerpRgb(MID, HIGH, (clamped - 0.5) * 2))
}

// Min-max across the event's 18 scores (Part 3: "all-equal -> low"). Returns {channel: hex}.
export function scoreColors(rows) {
  const scores = rows.map((r) => r.score)
  const min = Math.min(...scores)
  const max = Math.max(...scores)
  const colors = {}
  for (const r of rows) {
    const t = max > min ? (r.score - min) / (max - min) : 0
    colors[r.channel] = attrColorAt(t)
  }
  return colors
}
