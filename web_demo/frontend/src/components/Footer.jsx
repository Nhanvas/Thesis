// Persistent disclaimer bar, every screen except Log in (SZSCAN_SPEC_v5.md §0).
export default function Footer() {
  return (
    <footer className="fixed bottom-0 inset-x-0 bg-footer text-white text-xs text-center px-6 py-3">
      SzScan is an AI-assisted tool designed to support clinicians, not replace them.
    </footer>
  )
}
