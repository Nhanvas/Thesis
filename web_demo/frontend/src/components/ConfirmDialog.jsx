import { WarningTriangleIcon } from './icons.jsx'

// Delete confirmation, per UI/A2c and UI/A4b — SZSCAN_SPEC_v5.md §5.6: one wording for
// every case (subject mid-processing or already done), never two separate messages.
export default function ConfirmDialog({ message, onConfirm, onCancel }) {
  return (
    <div className="absolute inset-0 z-20 flex items-center justify-center bg-black/20">
      <div className="bg-brand text-white rounded-panel shadow-panel px-10 py-8 max-w-sm text-center">
        <WarningTriangleIcon className="w-14 h-14 mx-auto mb-4" />
        <p className="text-lg mb-6">{message}</p>
        <div className="flex items-center justify-center gap-3">
          <button
            type="button"
            onClick={onConfirm}
            className="bg-white text-text rounded-control px-5 py-2 text-sm font-medium"
          >
            Yes
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="bg-white text-text rounded-control px-5 py-2 text-sm font-medium"
          >
            No
          </button>
        </div>
      </div>
    </div>
  )
}
