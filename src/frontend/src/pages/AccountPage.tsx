/**
 * AccountsPage — account management dashboard.
 *
 * Access:
 *  - Both admins and operators can reach this page.
 *  - Admins see all three tabs: Accounts, Pending Requests, Audit Log.
 *  - Operators only see the Accounts tab, showing only their own account
 *    with just the change-password action. The backend enforces this too.
 */
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
    listAccounts, registerAccount, changePassword, deactivateAccount,
    listPendingRequests, approveRequest, denyRequest, type PendingRequest,
    listAuditLog, type AuditLogEntry,
} from '../api/accounts';
import type { Account } from '../types';
import ConfirmDialog from '../components/ConfirmDialog';
import { ScemasLogoMark } from '../components/ScemasLogoMark';

type Tab = 'accounts' | 'pending' | 'audit';

const EVENT_TYPES = [
    '',
    'login_success',
    'login_failure',
    'account_created',
    'account_deactivated',
    'password_changed',
    'request_approved',
    'request_denied',
];

export default function AccountsPage() {
    const { account: self, isAdmin, signOut } = useAuth();
    const navigate = useNavigate();

    const [tab, setTab] = useState<Tab>('accounts');

    // accounts
    const [accounts, setAccounts] = useState<Account[]>([]);
    const [accountsLoading, setAccountsLoading] = useState(true);
    const [accountsError, setAccountsError] = useState<string | null>(null);

    // create form (admin only)
    const [createName, setCreateName] = useState('');
    const [createEmail, setCreateEmail] = useState('');
    const [createPassword, setCreatePassword] = useState('');
    const [createClearance, setCreateClearance] = useState<'admin' | 'operator'>('operator');
    const [createLoading, setCreateLoading] = useState(false);
    const [createError, setCreateError] = useState<string | null>(null);

    // change-password
    const [pwAid, setPwAid] = useState<number | null>(null);
    const [newPw, setNewPw] = useState('');
    const [pwError, setPwError] = useState<string | null>(null);
    const [pwLoading, setPwLoading] = useState(false);

    // Deactivate confirm
    const [deactivateTarget, setDeactivateTarget] = useState<Account | null>(null);

    // pending requests (admin only)
    const [pending, setPending] = useState<PendingRequest[]>([]);
    const [pendingLoading, setPendingLoading] = useState(false);
    const [pendingError, setPendingError] = useState<string | null>(null);
    const [denyTarget, setDenyTarget] = useState<PendingRequest | null>(null);
    const [approveLoading, setApproveLoading] = useState<number | null>(null);

    // audit log (admin only)
    const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([]);
    const [auditLoading, setAuditLoading] = useState(false);
    const [auditError, setAuditError] = useState<string | null>(null);
    const [filterEventType, setFilterEventType] = useState('');
    const [filterDateFrom, setFilterDateFrom] = useState('');
    const [filterDateTo, setFilterDateTo] = useState('');

    // loaders
    const loadAccounts = useCallback(async () => {
        setAccountsError(null);
        try {
            if (isAdmin) {
                // Admins fetch all accounts
                setAccounts(await listAccounts());
            } else {
                // Operators only see their own account
                if (self) setAccounts([self]);
            }
        } catch (err: unknown) {
            if ((err as { response?: { status?: number } })?.response?.status === 401) {
                signOut(); navigate('/login', { replace: true }); return;
            }
            setAccountsError('Failed to load accounts.');
        } finally {
            setAccountsLoading(false);
        }
    }, [isAdmin, self, signOut, navigate]);

    const loadPending = useCallback(async () => {
        if (!isAdmin) return;
        setPendingLoading(true);
        setPendingError(null);
        try {
            setPending(await listPendingRequests());
        } catch (err: unknown) {
            if ((err as { response?: { status?: number } })?.response?.status === 401) {
                signOut(); navigate('/login', { replace: true }); return;
            }
            setPendingError('Failed to load pending requests.');
        } finally {
            setPendingLoading(false);
        }
    }, [isAdmin, signOut, navigate]);

    const loadAuditLog = useCallback(async () => {
        if (!isAdmin) return;
        setAuditLoading(true);
        setAuditError(null);
        try {
            setAuditLog(await listAuditLog({
                event_type: filterEventType || undefined,
                date_from: filterDateFrom || undefined,
                date_to: filterDateTo || undefined,
            }));
        } catch {
            setAuditError('Failed to load audit log.');
        } finally {
            setAuditLoading(false);
        }
    }, [isAdmin, filterEventType, filterDateFrom, filterDateTo]);

    useEffect(() => { void loadAccounts(); }, [loadAccounts]);
    useEffect(() => { void loadPending(); }, [loadPending]);
    useEffect(() => { void loadAuditLog(); }, [loadAuditLog]);

    // handlers

    async function handleCreate(e: React.FormEvent) {
        e.preventDefault();
        setCreateError(null);
        setCreateLoading(true);
        try {
            const created = await registerAccount({
                name: createName, email: createEmail,
                password: createPassword, clearance: createClearance,
            });
            setAccounts(prev => [...prev, created]);
            setCreateName(''); setCreateEmail(''); setCreatePassword(''); setCreateClearance('operator');
        } catch (err: unknown) {
            const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
            setCreateError(typeof detail === 'string' ? detail : 'Failed to create account.');
        } finally {
            setCreateLoading(false);
        }
    }

    async function handleChangePassword() {
        if (pwAid === null) return;
        setPwError(null);
        setPwLoading(true);
        try {
            const updated = await changePassword(pwAid, newPw);
            setAccounts(prev => prev.map(a => a.aid === updated.aid ? updated : a));
            setPwAid(null); setNewPw('');
        } catch {
            setPwError('Failed to update password.');
        } finally {
            setPwLoading(false);
        }
    }

    async function handleDeactivate() {
        if (!deactivateTarget) return;
        try {
            const updated = await deactivateAccount(deactivateTarget.aid);
            setAccounts(prev => prev.map(a => a.aid === updated.aid ? updated : a));
            void loadAuditLog();
        } catch { /* silent */ }
        finally { setDeactivateTarget(null); }
    }

    async function handleApprove(req: PendingRequest) {
        setApproveLoading(req.id);
        try {
            const created = await approveRequest(req.id);
            setPending(prev => prev.filter(r => r.id !== req.id));
            setAccounts(prev => [...prev, created]);
            void loadAuditLog();
        } catch { /* silent */ }
        finally { setApproveLoading(null); }
    }

    async function handleDeny() {
        if (!denyTarget) return;
        const target = denyTarget;
        setDenyTarget(null); // close dialog immediately
        try {
            await denyRequest(target.id);
            setPending(prev => prev.filter(r => r.id !== target.id));
            void loadAuditLog();
        } catch (err: unknown) {
            console.error('Deny failed:', err);
            void loadPending(); // reload to restore state if it failed
        }
    }

    // stats (admin only)
    const totalActive = accounts.filter(a => a.is_active).length;
    const totalAdmins = accounts.filter(a => a.clearance === 'admin').length;
    const totalOperators = accounts.filter(a => a.clearance === 'operator').length;

    // tabs (operators can only see accounts)
    const visibleTabs = ([
        { key: 'accounts' as Tab, label: 'Accounts', adminOnly: false },
        { key: 'pending' as Tab, label: `Pending requests${pending.length > 0 ? ` (${pending.length})` : ''}`, adminOnly: true },
        { key: 'audit' as Tab, label: 'Audit log', adminOnly: true },
    ]).filter(t => !t.adminOnly || isAdmin);

    return (
        <div className="min-h-screen flex flex-col bg-parchment bg-noise-soft">

            {/* ── Nav ──────────────────────────────────────────────────────────────── */}
            <header className="sticky top-0 z-40 border-b border-white/10 bg-gradient-to-r from-moss-800 via-moss-800 to-moss-900 text-white shadow-lg shadow-moss-900/35">
                <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/30 to-transparent" aria-hidden />
                <div className="max-w-screen-xl mx-auto px-4 sm:px-6 h-[4.25rem] flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3 min-w-0">
                        <div className="w-10 h-10 rounded-2xl bg-white text-moss-700 flex items-center justify-center shadow-lg shadow-moss-950/25 shrink-0 ring-2 ring-white/25">
                            <ScemasLogoMark className="w-5 h-5" />
                        </div>
                        <div className="min-w-0">
                            <span className="font-display font-bold tracking-tight text-lg block leading-tight">SCEMAS</span>
                            <span className="hidden sm:block text-moss-200/90 text-[10px] font-bold uppercase tracking-[0.2em]">
                                Account Management
                            </span>
                        </div>
                    </div>

                    <div className="flex items-center gap-2 sm:gap-3 shrink-0">
                        <button
                            type="button"
                            onClick={() => navigate('/thresholds')}
                            className="rounded-xl px-3 py-2 text-sm font-semibold text-moss-100/90 hover:text-white hover:bg-white/10 transition-colors"
                        >
                            ← Dashboard
                        </button>
                        <span className="hidden md:block text-sm text-moss-100/95 truncate max-w-[200px]">
                            {self?.name}
                            <span className={`ml-2 text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-md font-bold ${isAdmin
                                    ? 'bg-moss-600/40 text-moss-100 ring-1 ring-moss-400/30'
                                    : 'bg-moss-900/70 text-moss-200 ring-1 ring-white/15'
                                }`}>
                                {self?.clearance}
                            </span>
                        </span>
                        <button
                            type="button"
                            onClick={() => { signOut(); navigate('/login', { replace: true }); }}
                            className="rounded-xl px-3 py-2 text-sm font-semibold text-moss-100/90 hover:text-white hover:bg-white/10 transition-colors"
                        >
                            Sign out
                        </button>
                    </div>
                </div>
            </header>

            <main className="flex-1 max-w-screen-xl mx-auto w-full px-4 sm:px-6 py-6 sm:py-10 space-y-8">

                {/* ── Operator read-only banner ─────────────────────────────────────── */}
                {!isAdmin && (
                    <div className="rounded-2xl border border-moss-300/50 bg-gradient-to-r from-moss-100/60 to-parchment px-4 py-4 flex items-center gap-3 text-sm text-ink-900 shadow-sm">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-moss-700 text-white">
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <span>
                            Signed in as <strong>OPERATOR</strong> — you can view and update your own account details only.
                        </span>
                    </div>
                )}

                {/* ── Stats row (admin only) ────────────────────────────────────────── */}
                {isAdmin && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
                        {[
                            { label: 'Total accounts', value: accounts.length, accent: 'from-sky-600 to-blue-700', text: 'text-sky-800' },
                            { label: 'Active', value: totalActive, accent: 'from-moss-500 to-moss-700', text: 'text-moss-800' },
                            { label: 'Admins', value: totalAdmins, accent: 'from-violet-600 to-indigo-700', text: 'text-violet-900' },
                            { label: 'Operators', value: totalOperators, accent: 'from-amber-500 to-orange-600', text: 'text-amber-800' },
                        ].map(({ label, value, accent, text }) => (
                            <div key={label} className="card group relative overflow-hidden p-4 sm:p-5 border-ink-200/70 transition-all duration-300 hover:border-moss-200 hover:shadow-lift">
                                <div className={`absolute -right-6 -top-6 h-28 w-28 rounded-full bg-gradient-to-br ${accent} opacity-[0.14] blur-2xl`} aria-hidden />
                                <p className="section-title relative">{label}</p>
                                <p className={`font-display relative text-3xl sm:text-4xl font-bold tabular-nums mt-2 ${text}`}>{value}</p>
                                <div className={`relative mt-3 h-1 w-12 rounded-full bg-gradient-to-r ${accent}`} aria-hidden />
                            </div>
                        ))}
                    </div>
                )}

                {/* ── Tabs ─────────────────────────────────────────────────────────── */}
                <div className="border-b border-ink-200/80 flex gap-1">
                    {visibleTabs.map(t => (
                        <button
                            key={t.key}
                            onClick={() => setTab(t.key)}
                            className={`px-5 py-3 text-sm font-semibold transition border-b-2 -mb-px ${tab === t.key
                                    ? 'border-moss-600 text-moss-800'
                                    : 'border-transparent text-ink-500 hover:text-ink-800'
                                }`}
                        >
                            {t.label}
                        </button>
                    ))}
                </div>

                {/* ── ACCOUNTS TAB ─────────────────────────────────────────────────── */}
                {tab === 'accounts' && (
                    <div className="space-y-8">

                        {/* Create account form — admin only */}
                        {isAdmin && (
                            <div className="card border-ink-200/80 p-6">
                                <h2 className="font-display text-base font-bold text-ink-950 mb-1">Create account</h2>
                                <p className="text-xs text-ink-500 mb-5">Manually add a new user — logged to audit trail.</p>
                                <form onSubmit={handleCreate} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    <div>
                                        <label className="label">Full name</label>
                                        <input className="input" required value={createName}
                                            onChange={e => setCreateName(e.target.value)} placeholder="Jane Smith" />
                                    </div>
                                    <div>
                                        <label className="label">Email</label>
                                        <input className="input" type="email" required value={createEmail}
                                            onChange={e => setCreateEmail(e.target.value)} placeholder="jane@example.com" />
                                    </div>
                                    <div>
                                        <label className="label">Password</label>
                                        <input className="input" type="password" required value={createPassword}
                                            onChange={e => setCreatePassword(e.target.value)} placeholder="••••••••" />
                                    </div>
                                    <div>
                                        <label className="label">Clearance</label>
                                        <select className="input" value={createClearance}
                                            onChange={e => setCreateClearance(e.target.value as 'admin' | 'operator')}>
                                            <option value="operator">Operator</option>
                                            <option value="admin">Admin</option>
                                        </select>
                                    </div>
                                    {createError && <p className="sm:col-span-2 text-sm text-red-700">{createError}</p>}
                                    <div className="sm:col-span-2 flex justify-end">
                                        <button type="submit" disabled={createLoading} className="btn-primary">
                                            {createLoading ? 'Creating…' : 'Create account'}
                                        </button>
                                    </div>
                                </form>
                            </div>
                        )}

                        {/* Accounts table */}
                        <div className="card border-ink-200/80 overflow-hidden shadow-card-lg">
                            <div className="px-5 py-4 border-b border-ink-100 bg-gradient-to-r from-white via-parchment/50 to-moss-50/30">
                                <h2 className="font-display font-bold text-ink-950 text-lg">
                                    {isAdmin ? 'All accounts' : 'Your account'}
                                    <span className="ml-2 text-sm font-sans font-semibold text-ink-400">
                                        {isAdmin ? `${accounts.length} total` : ''}
                                    </span>
                                </h2>
                            </div>

                            {accountsLoading ? (
                                <div className="flex items-center justify-center py-16 text-ink-500 gap-3">
                                    <svg className="animate-spin w-6 h-6 text-moss-600" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                                    </svg>
                                    <span className="text-sm font-medium">Loading…</span>
                                </div>
                            ) : accountsError ? (
                                <div className="px-5 py-4 text-sm text-red-900 bg-red-50">
                                    {accountsError}{' '}
                                    <button onClick={() => void loadAccounts()} className="font-semibold underline">Retry</button>
                                </div>
                            ) : (
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b border-ink-100 text-ink-500 text-left text-xs uppercase tracking-wider">
                                                <th className="px-5 py-3 font-semibold">Name</th>
                                                <th className="px-5 py-3 font-semibold">Email</th>
                                                <th className="px-5 py-3 font-semibold">Clearance</th>
                                                <th className="px-5 py-3 font-semibold">Status</th>
                                                <th className="px-5 py-3 font-semibold">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-ink-100">
                                            {accounts.map(acc => (
                                                <tr key={acc.aid} className="hover:bg-parchment/40 transition-colors">
                                                    <td className="px-5 py-3.5 font-medium text-ink-900">{acc.name}</td>
                                                    <td className="px-5 py-3.5 text-ink-600">{acc.email}</td>
                                                    <td className="px-5 py-3.5">
                                                        <span className={`inline-flex items-center rounded-lg px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide ${acc.clearance === 'admin'
                                                                ? 'bg-violet-100 text-violet-800'
                                                                : 'bg-moss-100 text-moss-800'
                                                            }`}>
                                                            {acc.clearance}
                                                        </span>
                                                    </td>
                                                    <td className="px-5 py-3.5">
                                                        <span className={`inline-flex items-center rounded-lg px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide ${acc.is_active
                                                                ? 'bg-green-100 text-green-800'
                                                                : 'bg-ink-100 text-ink-500'
                                                            }`}>
                                                            {acc.is_active ? 'Active' : 'Inactive'}
                                                        </span>
                                                    </td>
                                                    <td className="px-5 py-3.5">
                                                        <div className="flex items-center gap-2 flex-wrap">
                                                            {/* Change password — available to everyone for their own account */}
                                                            {(isAdmin || acc.aid === self?.aid) && (
                                                                pwAid === acc.aid ? (
                                                                    <div className="flex items-center gap-2">
                                                                        <input
                                                                            type="password"
                                                                            placeholder="New password"
                                                                            value={newPw}
                                                                            onChange={e => setNewPw(e.target.value)}
                                                                            className="input !py-1.5 !text-xs w-36"
                                                                        />
                                                                        <button
                                                                            onClick={() => void handleChangePassword()}
                                                                            disabled={pwLoading || !newPw}
                                                                            className="btn-primary !text-xs !py-1.5"
                                                                        >
                                                                            {pwLoading ? '…' : 'Save'}
                                                                        </button>
                                                                        <button
                                                                            onClick={() => { setPwAid(null); setPwError(null); setNewPw(''); }}
                                                                            className="btn-ghost !text-xs"
                                                                        >
                                                                            Cancel
                                                                        </button>
                                                                        {pwError && <span className="text-xs text-red-600">{pwError}</span>}
                                                                    </div>
                                                                ) : (
                                                                    <button
                                                                        onClick={() => { setPwAid(acc.aid); setNewPw(''); setPwError(null); }}
                                                                        className="btn-ghost !text-xs"
                                                                    >
                                                                        Change password
                                                                    </button>
                                                                )
                                                            )}

                                                            {/* Deactivate — admin only, can't deactivate yourself */}
                                                            {isAdmin && acc.is_active && acc.aid !== self?.aid && (
                                                                <button
                                                                    onClick={() => setDeactivateTarget(acc)}
                                                                    className="btn-danger !text-xs !py-1.5"
                                                                >
                                                                    Deactivate
                                                                </button>
                                                            )}
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* ── PENDING REQUESTS TAB (admin only) ────────────────────────────── */}
                {tab === 'pending' && isAdmin && (
                    <div className="card border-ink-200/80 overflow-hidden shadow-card-lg">
                        <div className="px-5 py-4 border-b border-ink-100 bg-gradient-to-r from-white via-parchment/50 to-moss-50/30">
                            <h2 className="font-display font-bold text-ink-950 text-lg">Pending account requests</h2>
                            <p className="text-xs text-ink-500 mt-0.5">
                                Approve to create the account; deny to remove the request. Both actions are logged.
                            </p>
                        </div>

                        {pendingLoading ? (
                            <div className="flex items-center justify-center py-16 text-ink-500 gap-3">
                                <svg className="animate-spin w-6 h-6 text-moss-600" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                                </svg>
                                <span className="text-sm font-medium">Loading requests…</span>
                            </div>
                        ) : pendingError ? (
                            <div className="px-5 py-4 text-sm text-red-900 bg-red-50">
                                {pendingError}{' '}
                                <button onClick={() => void loadPending()} className="font-semibold underline">Retry</button>
                            </div>
                        ) : pending.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-16 text-ink-400 gap-2">
                                <svg className="w-10 h-10 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <p className="text-sm font-medium">No pending requests</p>
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b border-ink-100 text-ink-500 text-left text-xs uppercase tracking-wider">
                                            <th className="px-5 py-3 font-semibold">Name</th>
                                            <th className="px-5 py-3 font-semibold">Email</th>
                                            <th className="px-5 py-3 font-semibold">Requested role</th>
                                            <th className="px-5 py-3 font-semibold">Reason</th>
                                            <th className="px-5 py-3 font-semibold">Requested at</th>
                                            <th className="px-5 py-3 font-semibold">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-ink-100">
                                        {pending.map(req => (
                                            <tr key={req.id} className="hover:bg-parchment/40 transition-colors">
                                                <td className="px-5 py-3.5 font-medium text-ink-900">{req.name}</td>
                                                <td className="px-5 py-3.5 text-ink-600">{req.email}</td>
                                                <td className="px-5 py-3.5">
                                                    <span className={`inline-flex items-center rounded-lg px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide ${req.clearance === 'admin'
                                                            ? 'bg-violet-100 text-violet-800'
                                                            : 'bg-moss-100 text-moss-800'
                                                        }`}>
                                                        {req.clearance}
                                                    </span>
                                                </td>
                                                <td className="px-5 py-3.5 text-ink-500 max-w-[200px] truncate" title={req.reason ?? ''}>
                                                    {req.reason ?? <span className="italic text-ink-400">—</span>}
                                                </td>
                                                <td className="px-5 py-3.5 text-ink-500 text-xs whitespace-nowrap">
                                                    {new Date(req.requested_at).toLocaleString()}
                                                </td>
                                                <td className="px-5 py-3.5">
                                                    <div className="flex items-center gap-2">
                                                        <button
                                                            onClick={() => void handleApprove(req)}
                                                            disabled={approveLoading === req.id}
                                                            className="btn-primary !text-xs !py-1.5"
                                                        >
                                                            {approveLoading === req.id ? 'Approving…' : 'Approve'}
                                                        </button>
                                                        <button
                                                            onClick={() => setDenyTarget(req)}
                                                            className="btn-danger !text-xs !py-1.5"
                                                        >
                                                            Deny
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                )}

                {/* ── AUDIT LOG TAB (admin only) ────────────────────────────────────── */}
                {tab === 'audit' && isAdmin && (
                    <div className="space-y-6">
                        <div className="card border-ink-200/80 p-5">
                            <h2 className="font-display text-base font-bold text-ink-950 mb-4">Filter audit log</h2>
                            <div className="flex flex-wrap gap-3 items-end">
                                <div>
                                    <label className="label">Event type</label>
                                    <select className="input !py-1.5 !text-xs w-44"
                                        value={filterEventType} onChange={e => setFilterEventType(e.target.value)}>
                                        {EVENT_TYPES.map(t => (
                                            <option key={t} value={t}>{t || 'All events'}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="label">From</label>
                                    <input type="datetime-local" className="input !py-1.5 !text-xs"
                                        value={filterDateFrom} onChange={e => setFilterDateFrom(e.target.value)} />
                                </div>
                                <div>
                                    <label className="label">To</label>
                                    <input type="datetime-local" className="input !py-1.5 !text-xs"
                                        value={filterDateTo} onChange={e => setFilterDateTo(e.target.value)} />
                                </div>
                                <button onClick={() => void loadAuditLog()} className="btn-primary !text-xs">
                                    Apply
                                </button>
                                {(filterEventType || filterDateFrom || filterDateTo) && (
                                    <button
                                        onClick={() => { setFilterEventType(''); setFilterDateFrom(''); setFilterDateTo(''); }}
                                        className="btn-ghost !text-xs text-ink-500"
                                    >
                                        Clear
                                    </button>
                                )}
                            </div>
                        </div>

                        <div className="card border-ink-200/80 overflow-hidden shadow-card-lg">
                            {auditLoading ? (
                                <div className="flex items-center justify-center py-16 text-ink-500 gap-3">
                                    <svg className="animate-spin w-6 h-6 text-moss-600" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                                    </svg>
                                    <span className="text-sm font-medium">Loading audit log…</span>
                                </div>
                            ) : auditError ? (
                                <div className="px-5 py-4 text-sm text-red-900 bg-red-50">
                                    {auditError}{' '}
                                    <button onClick={() => void loadAuditLog()} className="font-semibold underline">Retry</button>
                                </div>
                            ) : (
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b border-ink-100 text-ink-500 text-left text-xs uppercase tracking-wider">
                                                <th className="px-5 py-3 font-semibold">Event</th>
                                                <th className="px-5 py-3 font-semibold">Actor</th>
                                                <th className="px-5 py-3 font-semibold">Target</th>
                                                <th className="px-5 py-3 font-semibold">Detail</th>
                                                <th className="px-5 py-3 font-semibold">Timestamp</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-ink-100">
                                            {auditLog.length === 0 ? (
                                                <tr>
                                                    <td colSpan={5} className="px-5 py-10 text-center text-sm text-ink-400">
                                                        No entries found.
                                                    </td>
                                                </tr>
                                            ) : auditLog.map(entry => (
                                                <tr key={entry.id} className="hover:bg-parchment/40 transition-colors">
                                                    <td className="px-5 py-3.5">
                                                        <span className={`inline-flex items-center rounded-lg px-2.5 py-1 text-[11px] font-bold font-mono uppercase tracking-wide ${entry.event_type.includes('failure') || entry.event_type.includes('denied')
                                                                ? 'bg-red-100 text-red-800'
                                                                : entry.event_type.includes('deactivated')
                                                                    ? 'bg-amber-100 text-amber-800'
                                                                    : entry.event_type.includes('approved') || entry.event_type.includes('created')
                                                                        ? 'bg-green-100 text-green-800'
                                                                        : 'bg-ink-100 text-ink-600'
                                                            }`}>
                                                            {entry.event_type}
                                                        </span>
                                                    </td>
                                                    <td className="px-5 py-3.5 text-ink-600">{entry.actor_email ?? '—'}</td>
                                                    <td className="px-5 py-3.5 text-ink-600">{entry.target_email ?? '—'}</td>
                                                    <td className="px-5 py-3.5 text-ink-400 max-w-[200px] truncate" title={entry.detail ?? ''}>
                                                        {entry.detail ?? '—'}
                                                    </td>
                                                    <td className="px-5 py-3.5 text-ink-400 text-xs whitespace-nowrap">
                                                        {new Date(entry.created_at).toLocaleString()}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </main>

            {/* ── Confirm dialogs ───────────────────────────────────────────────── */}
            {deactivateTarget && (
                <ConfirmDialog
                    title="Deactivate account"
                    message={
                        <>
                            Deactivate <strong>{deactivateTarget.email}</strong>? They will no longer be able to sign in.
                            This action is logged to the audit trail.
                        </>
                    }
                    confirmLabel="Deactivate"
                    onConfirm={() => void handleDeactivate()}
                    onCancel={() => setDeactivateTarget(null)}
                />
            )}

            {denyTarget && (
                <ConfirmDialog
                    title="Deny request"
                    message={
                        <>
                            Deny the access request from <strong>{denyTarget.email}</strong>?
                            This action is logged to the audit trail.
                        </>
                    }
                    confirmLabel="Deny"
                    onConfirm={() => void handleDeny()}
                    onCancel={() => setDenyTarget(null)}
                />
            )}
        </div>
    );
}