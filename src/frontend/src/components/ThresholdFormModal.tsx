/**
 * ThresholdFormModal — modal dialog for creating and editing threshold rules.
 *
 * Dual-mode design:
 *  - When `initial` is null/undefined, the form opens blank and calls
 *    POST /threshold on submit (create mode).
 *  - When `initial` is a full Threshold object, the form pre-populates its
 *    fields and calls PATCH /threshold/{id} on submit (edit mode).
 *  The parent (ThresholdsPage) decides which mode applies by setting editTarget.
 *
 * is_active handling:
 *  The form includes an is_active toggle so a rule can be created as inactive
 *  from the start. However, when in edit mode, the ThresholdsPage handleSave
 *  strips is_active before sending the PATCH body — active state changes must
 *  go through /activate or /deactivate to preserve the audit log. The toggle
 *  is still shown in edit mode because it provides visual feedback about the
 *  current state of the rule the user is editing.
 *
 * z-index:
 *  The modal root uses z-[1000] to ensure it renders above Leaflet map tiles.
 *  Leaflet internally uses z-indices up to ~700; the parent card wrapping the
 *  map uses `isolate` (ThresholdsPage) to contain those, but the modal is
 *  mounted at the root level and must still be above anything on the page.
 *
 * Error surfacing:
 *  Backend validation errors (e.g. unknown zone, threshold_value out of range)
 *  arrive as a FastAPI `detail` string in the 422 response body. We extract
 *  and display that string directly rather than showing a generic message.
 */
import { useEffect, useState } from 'react';
import type { Condition, Severity, Threshold, ThresholdCreate } from '../types';
import { CONDITIONS, KNOWN_METRICS, KNOWN_ZONES, SEVERITIES } from '../types';

interface Props {
  initial?: Threshold | null;
  onSave: (data: ThresholdCreate) => Promise<void>;
  onClose: () => void;
}

// Default form values for the create path — chosen to be sensible starting points:
// 'gt' and 'medium' are the most common new-rule configuration.
const EMPTY: ThresholdCreate = {
  zone:            '',
  metric:          '',
  condition:       'gt',
  threshold_value: 0,
  severity:        'medium',
  is_active:       true,
};

export default function ThresholdFormModal({ initial, onSave, onClose }: Props) {
  const isEdit = !!initial;

  const [form,   setForm]   = useState<ThresholdCreate>(EMPTY);
  const [error,  setError]  = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Re-populate the form whenever the target threshold changes.
  // This handles the edge case where the user edits rule A, closes the modal,
  // then immediately edits rule B — without this effect the form would still
  // show rule A's values.
  useEffect(() => {
    if (initial) {
      setForm({
        zone:            initial.zone,
        metric:          initial.metric,
        condition:       initial.condition,
        threshold_value: initial.threshold_value,
        severity:        initial.severity,
        is_active:       initial.is_active,
      });
    } else {
      setForm(EMPTY);
    }
  }, [initial]);

  // Generic setter that merges a single field update without mutating the rest.
  function set<K extends keyof ThresholdCreate>(key: K, value: ThresholdCreate[K]) {
    setForm(prev => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // Frontend validation for the most likely user error before hitting the API.
    if (!form.zone.trim() || !form.metric.trim()) {
      setError('Zone and metric are required.');
      return;
    }
    setError(null);
    setSaving(true);
    try {
      await onSave(form);
      onClose(); // close only on success so the user sees errors without losing their input
    } catch (err: unknown) {
      // FastAPI returns validation errors as a `detail` field (string or list).
      // We only handle string details here; list details (422 field errors) fall
      // back to the generic message.
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Save failed. Check your input.');
    } finally {
      setSaving(false);
    }
  }

  return (
    /*
      z-[1000]: must be above Leaflet map tiles (internal z-index up to ~700)
      and above the `isolate` stacking context of the map card.
      See ThresholdsPage for the `isolate` explanation.
    */
    <div className="fixed inset-0 z-[1000] flex items-center justify-center p-4">
      {/* Semi-transparent backdrop — clicking it closes the modal */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />

      {/* Modal panel — uses relative z-10 to sit above the absolute backdrop */}
      <div className="relative z-10 w-full max-w-lg bg-parchment rounded-2xl shadow-card-lg border border-ink-200/90 flex flex-col max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-ink-100 bg-gradient-to-r from-parchment-deep to-moss-50/50">
          <h2 className="font-display text-xl font-bold text-ink-950 tracking-tight">
            {isEdit ? 'Edit threshold' : 'New threshold'}
          </h2>
          <button type="button" onClick={onClose} className="btn-ghost p-2 rounded-xl text-ink-500 hover:text-ink-900">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scrollable form body — max-h-[90vh] on the parent prevents it from going off-screen
            on small displays; overflow-y-auto lets users scroll inside the modal instead. */}
        <form id="threshold-form" onSubmit={handleSubmit} className="overflow-y-auto px-6 py-5 space-y-5 flex-1">
          {error && (
            <div className="rounded-xl bg-red-50 border border-red-100 px-4 py-3 text-sm text-red-800 font-medium">
              {error}
            </div>
          )}

          {/* Zone — dropdown populated from KNOWN_ZONES in types/index.ts.
              These match the zones the simulator publishes to, ensuring the frontend
              and backend share the same set of valid zone identifiers. */}
          <div>
            <label className="label" htmlFor="zone">Zone</label>
            <select
              id="zone"
              className="input"
              value={form.zone}
              onChange={e => set('zone', e.target.value)}
              required
            >
              <option value="">Select zone…</option>
              {KNOWN_ZONES.map(z => (
                <option key={z} value={z}>{z}</option>
              ))}
            </select>
          </div>

          {/* Metric — dropdown populated from KNOWN_METRICS in types/index.ts.
              These match VALID_RANGES in the backend's validation_service.py. */}
          <div>
            <label className="label" htmlFor="metric">Metric</label>
            <select
              id="metric"
              className="input"
              value={form.metric}
              onChange={e => set('metric', e.target.value)}
              required
            >
              <option value="">Select metric…</option>
              {KNOWN_METRICS.map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          {/* Condition + Value in a two-column grid so the logical unit "≥ 150"
              stays visually grouped rather than split across separate rows. */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label" htmlFor="condition">Condition</label>
              <select
                id="condition"
                className="input"
                value={form.condition}
                onChange={e => set('condition', e.target.value as Condition)}
                required
              >
                {CONDITIONS.map(c => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="label" htmlFor="threshold_value">Threshold Value</label>
              {/* step="any" allows decimal values (e.g. temperature = 36.5) */}
              <input
                id="threshold_value"
                type="number"
                step="any"
                className="input"
                value={form.threshold_value}
                onChange={e => set('threshold_value', parseFloat(e.target.value))}
                required
              />
            </div>
          </div>

          {/* Severity — pill buttons rather than a dropdown so the colour coding
              is visible during selection, making the choice more intuitive. */}
          <div>
            <label className="label">Severity</label>
            <div className="flex gap-2 flex-wrap">
              {SEVERITIES.map(s => {
                const ACTIVE_STYLES: Record<Severity, string> = {
                  low:      'bg-green-600  border-green-600  text-white',
                  medium:   'bg-yellow-500 border-yellow-500 text-white',
                  high:     'bg-orange-500 border-orange-500 text-white',
                  critical: 'bg-red-600    border-red-600    text-white',
                };
                const selected = form.severity === s;
                return (
                  <button
                    key={s}
                    type="button"
                    onClick={() => set('severity', s as Severity)}
                    className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors capitalize
                      ${selected ? ACTIVE_STYLES[s] : 'border-gray-300 text-gray-600 hover:bg-gray-50'}`}
                  >
                    {s}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active toggle — shown in both create and edit mode.
              In edit mode the parent strips is_active before PATCH so this only
              affects the CREATE path (the initial active state of a new rule). */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              role="switch"
              aria-checked={form.is_active}
              onClick={() => set('is_active', !form.is_active)}
              className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent
                transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-moss-500 focus-visible:ring-offset-2
                ${form.is_active ? 'bg-gradient-to-r from-moss-600 to-moss-800' : 'bg-ink-300'}`}
            >
              <span
                className={`inline-block h-5 w-5 rounded-full bg-white shadow transform transition-transform duration-200
                  ${form.is_active ? 'translate-x-5' : 'translate-x-0'}`}
              />
            </button>
            <span className="text-sm font-medium text-gray-700">
              {form.is_active ? 'Active (evaluator will check this rule)' : 'Inactive (rule is paused)'}
            </span>
          </div>
        </form>

        {/* Footer with cancel and submit.
            Submit uses form="threshold-form" to trigger the form's onSubmit from
            outside the <form> element — necessary because the form is in the
            scrollable body while the button is in the sticky footer. */}
        <div className="flex justify-end gap-3 px-6 py-4 border-t border-ink-100 bg-parchment-deep/60">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button
            type="submit"
            form="threshold-form"
            disabled={saving}
            className="btn-primary min-w-[8rem]"
          >
            {saving ? 'Saving…' : isEdit ? 'Save changes' : 'Create threshold'}
          </button>
        </div>
      </div>
    </div>
  );
}
