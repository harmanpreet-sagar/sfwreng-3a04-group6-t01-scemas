/**
 * ThresholdTable — displays the filtered list of threshold rules.
 *
 * Responsibilities:
 *  - Render a responsive table of threshold rows with severity badges.
 *  - For ADMIN users: show an active/inactive toggle switch per row,
 *    and Edit / Delete action buttons.
 *  - For OPERATOR users: show a read-only status badge; no action column.
 *  - Guard the delete action behind a ConfirmDialog to prevent accidental
 *    permanent deletion.
 *  - Track in-flight toggle and delete requests per row so the appropriate
 *    button shows a disabled state while waiting — prevents double-submit.
 *
 * The component is purely presentational: it calls onToggle / onDelete
 * callbacks and lets ThresholdsPage own the actual API calls and state updates.
 * This separation means the table can be tested in isolation with mock handlers.
 *
 * The `pendingDelete` state stores the full Threshold object (not just its id)
 * so the ConfirmDialog can display a meaningful human-readable description of
 * exactly which rule will be removed (zone, metric, condition, value).
 */
import { useState } from 'react';
import type { Threshold } from '../types';
import SeverityBadge from './SeverityBadge';
import ConfirmDialog from './ConfirmDialog';

// Human-readable operator symbols for the rule column (e.g. "gte" → "≥ 50")
const CONDITION_LABEL: Record<string, string> = {
  gt:  '>',
  gte: '≥',
  lt:  '<',
  lte: '≤',
  eq:  '=',
};

interface Props {
  thresholds: Threshold[];
  isAdmin: boolean;
  onEdit:   (t: Threshold) => void;
  onToggle: (t: Threshold) => Promise<void>;
  onDelete: (id: number)   => Promise<void>;
}

export default function ThresholdTable({ thresholds, isAdmin, onEdit, onToggle, onDelete }: Props) {
  // null means no delete is in progress; non-null means the confirm dialog is open for that row.
  const [pendingDelete, setPendingDelete] = useState<Threshold | null>(null);
  // Track which row's toggle is in-flight so we can disable it until the request completes.
  const [togglingId,    setTogglingId]    = useState<number | null>(null);
  // Track which row's delete is in-flight (after confirmation) to disable repeated clicks.
  const [deletingId,    setDeletingId]    = useState<number | null>(null);

  async function handleToggle(t: Threshold) {
    setTogglingId(t.id);
    try { await onToggle(t); } finally { setTogglingId(null); }
  }

  async function handleDelete() {
    if (!pendingDelete) return;
    setDeletingId(pendingDelete.id);
    try {
      await onDelete(pendingDelete.id);
    } finally {
      // Always clear state — even on error — so the dialog doesn't get stuck open.
      setDeletingId(null);
      setPendingDelete(null);
    }
  }

  // Empty state — shown when there are no rules matching the current filter,
  // or when the database has no thresholds at all.
  if (thresholds.length === 0) {
    return (
      <div className="text-center py-16 text-gray-400">
        <svg className="mx-auto w-12 h-12 mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
        </svg>
        <p className="font-medium">No thresholds found</p>
        <p className="text-sm mt-1">Create one to get started.</p>
      </div>
    );
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead>
            <tr className="bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Zone</th>
              <th className="px-4 py-3">Metric</th>
              <th className="px-4 py-3">Rule</th>
              <th className="px-4 py-3">Severity</th>
              <th className="px-4 py-3">Status</th>
              {/* Actions column is hidden entirely for operators to reduce visual clutter */}
              {isAdmin && <th className="px-4 py-3 text-right">Actions</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {thresholds.map(t => (
              <tr key={t.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-gray-400 font-mono">#{t.id}</td>

                <td className="px-4 py-3">
                  <span className="inline-flex items-center gap-1.5 font-medium text-gray-800">
                    <span className="w-2 h-2 rounded-full bg-blue-500 opacity-70 shrink-0" />
                    {t.zone}
                  </span>
                </td>

                <td className="px-4 py-3 capitalize text-gray-700">{t.metric}</td>

                {/* "Rule" column renders the threshold as a readable expression, e.g. "≥ 150" */}
                <td className="px-4 py-3 font-mono text-gray-800">
                  {CONDITION_LABEL[t.condition] ?? t.condition}{' '}
                  <span className="font-semibold">{t.threshold_value}</span>
                </td>

                <td className="px-4 py-3">
                  <SeverityBadge severity={t.severity} />
                </td>

                <td className="px-4 py-3">
                  {isAdmin ? (
                    /*
                      Toggle switch uses role="switch" + aria-checked for accessibility.
                      Disabled while a toggle request is in-flight (togglingId === t.id)
                      to prevent duplicate PATCH calls to /activate or /deactivate.
                    */
                    <button
                      role="switch"
                      aria-checked={t.is_active}
                      disabled={togglingId === t.id}
                      onClick={() => handleToggle(t)}
                      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent
                        transition-colors duration-200 focus:outline-none disabled:opacity-60
                        ${t.is_active ? 'bg-blue-600' : 'bg-gray-300'}`}
                    >
                      <span
                        className={`inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform duration-200
                          ${t.is_active ? 'translate-x-4' : 'translate-x-0'}`}
                      />
                    </button>
                  ) : (
                    // Operators see a static badge — the toggle switch is not rendered at all,
                    // not just disabled, so there is no ambiguity about whether they can interact.
                    <span className={`badge ${t.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500'}`}>
                      {t.is_active ? 'Active' : 'Inactive'}
                    </span>
                  )}
                </td>

                {isAdmin && (
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      {/* Edit opens the form modal pre-populated with this row's values */}
                      <button
                        onClick={() => onEdit(t)}
                        className="btn-ghost p-1.5 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                        title="Edit threshold"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round"
                            d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125" />
                        </svg>
                      </button>

                      {/* Delete sets pendingDelete to open ConfirmDialog; the actual DELETE
                          request only fires after the user confirms in the dialog. */}
                      <button
                        onClick={() => setPendingDelete(t)}
                        disabled={deletingId === t.id}
                        className="btn-ghost p-1.5 text-red-500 hover:text-red-700 hover:bg-red-50"
                        title="Delete threshold"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round"
                            d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                        </svg>
                      </button>
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ConfirmDialog is rendered outside the table so it doesn't inherit the
          table's overflow:hidden and can fill the screen correctly. */}
      {pendingDelete && (
        <ConfirmDialog
          title="Delete threshold?"
          message={`Rule #${pendingDelete.id}: ${pendingDelete.metric} in ${pendingDelete.zone} (${CONDITION_LABEL[pendingDelete.condition]} ${pendingDelete.threshold_value}) will be permanently removed.`}
          onConfirm={handleDelete}
          onCancel={() => setPendingDelete(null)}
        />
      )}
    </>
  );
}
