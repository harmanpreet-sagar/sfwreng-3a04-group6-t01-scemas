/**
 * ConfirmDialog — a reusable destructive-action confirmation modal.
 *
 * Used wherever a user action cannot be undone (currently: threshold deletion).
 * The two-step pattern (click delete → confirm in dialog) prevents accidental
 * data loss, especially important since the backend has no soft-delete.
 *
 * Design decisions:
 *  - z-[1000] matches ThresholdFormModal so both modals render above Leaflet
 *    map tiles. They are never shown simultaneously, so there is no z-conflict
 *    between them.
 *  - Clicking the backdrop calls onCancel (same as the Cancel button) because
 *    a user who clicks away is expressing intent to abort.
 *  - confirmLabel defaults to 'Delete' but can be overridden for other uses
 *    (e.g. "Deactivate", "Revoke") if the dialog is reused for other actions.
 *  - The component is stateless — all state (which item is pending, whether
 *    deletion is in flight) is managed by ThresholdTable, keeping this
 *    component trivially testable.
 */
interface Props {
  title: string;
  message: string | React.ReactNode;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  title,
  message,
  confirmLabel = 'Delete',
  onConfirm,
  onCancel,
}: Props) {
  return (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center p-4">
      {/* Backdrop — clicking away is equivalent to Cancel */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Dialog panel */}
      <div className="relative z-10 w-full max-w-md bg-parchment rounded-2xl shadow-card-lg border border-ink-200/90 p-6 sm:p-7">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-11 h-11 rounded-xl bg-red-50 ring-1 ring-red-100 flex items-center justify-center">
            <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
          </div>

          <div className="flex-1 min-w-0">
            <h3 className="font-display text-lg font-bold text-ink-950 tracking-tight">{title}</h3>
            <p className="mt-2 text-sm text-ink-600 leading-relaxed">{message}</p>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap justify-end gap-3">
          <button type="button" className="btn-secondary" onClick={onCancel}>Cancel</button>
          <button type="button" className="btn-danger" onClick={onConfirm}>{confirmLabel}</button>
        </div>
      </div>
    </div>
  );
}
