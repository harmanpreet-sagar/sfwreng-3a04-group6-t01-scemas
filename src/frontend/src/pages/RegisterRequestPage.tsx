/**
 * RegisterRequestPage — public-facing form where a new user can submit account requests
 * No auth required, this page is publicly accessible from the login screen.
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { submitRegistrationRequest } from '../api/accounts';
import { ScemasLogoMark } from '../components/ScemasLogoMark';

export default function RegisterRequestPage() {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [clearance, setClearance] = useState<'admin' | 'operator'>('operator');
    const [reason, setReason] = useState('');
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setError(null);
        setLoading(true);
        try {
            await submitRegistrationRequest({ name, email, clearance, reason });
            setSuccess(true);
        } catch (err: unknown) {
            const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
            setError(typeof detail === 'string' ? detail : 'Failed to submit request. Please try again.');
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden bg-parchment bg-noise-soft px-4 py-10 sm:px-6 text-ink-900">
            <div className="relative z-10 w-full max-w-md">
                <div className="rounded-2xl border border-ink-200/70 bg-white/90 p-8 shadow-card-lg backdrop-blur-sm">
                    {/* Header */}
                    <div className="text-center border-b border-ink-100 pb-8 mb-8">
                        <Link
                            to="/"
                            className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-moss-700 text-white shadow-md shadow-moss-900/15 ring-2 ring-moss-500/20 mb-5 transition hover:bg-moss-600"
                        >
                            <ScemasLogoMark className="w-8 h-8" />
                        </Link>
                        <h1 className="font-display text-4xl font-bold text-ink-950 tracking-tight">SCEMAS</h1>
                        <p className="text-moss-800 text-xs font-bold uppercase tracking-[0.25em] mt-3">Request access</p>
                    </div>

                    {success ? (
                        /* Success state */
                        <div className="text-center space-y-4">
                            <div className="flex items-center justify-center w-14 h-14 rounded-full bg-moss-100 mx-auto">
                                <svg className="w-7 h-7 text-moss-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                                </svg>
                            </div>
                            <h2 className="font-display text-xl font-bold text-ink-950">Request submitted</h2>
                            <p className="text-sm text-ink-600 leading-relaxed">
                                Your request has been sent to an admin for review. You'll be contacted at{' '}
                                <span className="font-semibold text-ink-900">{email}</span> once it's approved.
                            </p>
                            <Link to="/login" className="btn-primary w-full mt-4 flex items-center justify-center py-3">
                                Back to sign in
                            </Link>
                        </div>
                    ) : (
                        <>
                            <div className="mb-6">
                                <h2 className="font-display text-2xl font-bold text-ink-950 tracking-tight">Request an account</h2>
                                <p className="text-sm text-ink-600 mt-1.5">
                                    An admin will review and approve your request.
                                </p>
                            </div>

                            {error && (
                                <div className="mb-5 rounded-xl bg-red-50 border border-red-200/80 px-4 py-3 text-sm text-red-900 flex items-start gap-3">
                                    <svg className="w-5 h-5 shrink-0 text-red-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
                                    </svg>
                                    <span>{error}</span>
                                </div>
                            )}

                            <form onSubmit={handleSubmit} className="space-y-5">
                                <div>
                                    <label htmlFor="name" className="label">Full name</label>
                                    <input
                                        id="name"
                                        type="text"
                                        required
                                        value={name}
                                        onChange={e => setName(e.target.value)}
                                        placeholder="Jane Smith"
                                        className="input"
                                    />
                                </div>

                                <div>
                                    <label htmlFor="email" className="label">Email</label>
                                    <input
                                        id="email"
                                        type="email"
                                        required
                                        value={email}
                                        onChange={e => setEmail(e.target.value)}
                                        placeholder="jane@example.com"
                                        className="input"
                                    />
                                </div>

                                <div>
                                    <label htmlFor="clearance" className="label">Requested role</label>
                                    <select
                                        id="clearance"
                                        value={clearance}
                                        onChange={e => setClearance(e.target.value as 'admin' | 'operator')}
                                        className="input"
                                    >
                                        <option value="operator">Operator</option>
                                        <option value="admin">Admin</option>
                                    </select>
                                </div>

                                <div>
                                    <label htmlFor="reason" className="label">
                                        Reason for access{' '}
                                        <span className="text-ink-400 font-normal">(optional)</span>
                                    </label>
                                    <textarea
                                        id="reason"
                                        rows={3}
                                        value={reason}
                                        onChange={e => setReason(e.target.value)}
                                        placeholder="Briefly describe why you need access…"
                                        className="input resize-none"
                                    />
                                </div>

                                <button type="submit" disabled={loading} className="btn-primary w-full py-3.5 text-base mt-2">
                                    {loading ? (
                                        <>
                                            <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                                            </svg>
                                            Submitting…
                                        </>
                                    ) : (
                                        'Submit request'
                                    )}
                                </button>
                            </form>
                        </>
                    )}
                </div>

                <p className="mt-8 text-center text-xs text-ink-500">
                    <Link to="/login" className="font-semibold text-moss-800 hover:text-moss-950 underline-offset-2 hover:underline">
                        ← Back to sign in
                    </Link>
                    <span className="mx-2 text-ink-400">·</span>
                    <span className="text-ink-500">SE 3A04 · Group 6</span>
                </p>
            </div>
        </div>
    );
}