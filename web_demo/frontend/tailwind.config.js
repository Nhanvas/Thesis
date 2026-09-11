/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: 'var(--color-bg)',
        surface: 'var(--color-surface)',
        'eeg-canvas': 'var(--color-eeg-canvas)',
        footer: 'var(--color-footer)',
        border: 'var(--color-border)',
        'border-strong': 'var(--color-border-strong)',

        brand: 'var(--color-brand)',
        interaction: 'var(--color-interaction)',

        text: 'var(--color-text)',
        'text-secondary': 'var(--color-text-secondary)',
        'text-muted': 'var(--color-text-muted)',

        ai: 'var(--color-ai)',
        human: 'var(--color-human)',

        accept: 'var(--color-accept)',
        'accept-bg': 'var(--color-accept-bg)',
        reject: 'var(--color-reject)',
        'reject-bg': 'var(--color-reject-bg)',
        uncertain: 'var(--color-uncertain)',
        'uncertain-bg': 'var(--color-uncertain-bg)',
        unseen: 'var(--color-unseen)',

        'eeg-raw': 'var(--color-eeg-raw)',
        'eeg-filtered': 'var(--color-eeg-filtered)',
        grid: 'var(--color-grid)',
        'grid-strong': 'var(--color-grid-strong)',

        'attr-low': 'var(--color-attr-low)',
        'attr-mid': 'var(--color-attr-mid)',
        'attr-high': 'var(--color-attr-high)',
      },
      backgroundImage: {
        'header-gradient': 'var(--header-gradient)',
      },
      fontFamily: {
        ui: ['Inter', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
      borderRadius: {
        panel: 'var(--radius-panel)',
        control: 'var(--radius-control)',
      },
      boxShadow: {
        panel: 'var(--shadow-panel)',
      },
    },
  },
  plugins: [],
}
