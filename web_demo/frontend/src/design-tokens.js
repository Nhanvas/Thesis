// SZSCAN_DESIGN_v2.md §9 — same values as the :root CSS block in src/index.css,
// exported as plain JS for anything that needs a raw hex outside a Tailwind class
// name (e.g. canvas drawing code for the EEG waveform).
export const tokens = {
  // nền & chrome
  // Measured #F8FAFC from the current UI PNGs — see index.css :root for the note on the
  // discrepancy with SZSCAN_DESIGN_v2.md §1 (which still says #FFFFFF).
  colorBg: '#F8FAFC',
  colorSurface: '#FFFFFF',
  colorEegCanvas: '#FEFBEF',
  colorFooter: '#0F172A',
  colorBorder: '#E2E8F0',
  colorBorderStrong: '#CBD5E1',

  headerGradient: 'linear-gradient(90deg, #624C8A 0%, #10182B 100%)',
  colorBrand: '#776399', // chrome: header, nút primary
  colorInteraction: '#7C3AED', // playhead + đang chọn (chỉ trong canvas nội dung)

  colorText: '#0F172A',
  colorTextSecondary: '#475569',
  colorTextMuted: '#64748B',

  // nguồn gốc event
  colorAi: '#334155',
  colorHuman: '#2563EB', // độc quyền cho event Human, KHÔNG dùng cho nút

  // review status
  colorAccept: '#16A34A',
  colorAcceptBg: '#F0FDF4',
  colorReject: '#DC2626',
  colorRejectBg: '#FEF2F2',
  colorUncertain: '#D97706',
  colorUncertainBg: '#FFFBEB',
  colorUnseen: '#94A3B8',

  // EEG
  colorEegRaw: '#64748B',
  colorEegFiltered: '#0F172A',
  colorGrid: '#E2E8F0',
  colorGridStrong: '#CBD5E1',

  // attribution (teal)
  colorAttrLow: '#CBD5E1',
  colorAttrMid: '#2DD4BF',
  colorAttrHigh: '#0F766E',

  // layout
  radiusPanel: '10px',
  radiusControl: '6px',
  shadowPanel: '0 1px 3px rgb(15 23 42 / 8%)',

  fontUi: "'Inter', sans-serif",
  fontMono: "'IBM Plex Mono', monospace",
}

export default tokens
