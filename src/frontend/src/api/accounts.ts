/**
 * Account Management API — wrappers for all /account endpoints.
 *
 * Auth: the backend uses custom headers (X-Account-Id, X-Account-Clearance,
 * X-Account-Email). These are read from localStorage
 * and attached to every request via accountAuthHeaders().
 */
import { apiClient } from './client';
import type { Account } from '../types';

function accountAuthHeaders() {
    const account = JSON.parse(localStorage.getItem('scemas_account') ?? '{}');
    return {
        'X-Account-Id': String(account.aid ?? ''),
        'X-Account-Clearance': account.clearance ?? '',
        'X-Account-Email': account.email ?? '',
    };
}

export interface AccountListResponse {
    accounts: Account[];
    total: number;
}

export interface AuditLogEntry {
    id: number;
    event_type: string;
    actor_id: number | null;
    actor_email: string | null;
    target_id: number | null;
    target_email: string | null;
    detail: string | null;
    created_at: string;
}

export interface AuditLogListResponse {
    entries: AuditLogEntry[];
    total: number;
}

export interface AccountCreate {
    name: string;
    email: string;
    password: string;
    clearance: 'admin' | 'operator';
}

export interface AccountRegisterRequest {
    name: string;
    email: string;
    clearance: 'admin' | 'operator';
    reason?: string;
}

export interface PendingRequest {
    id: number;
    name: string;
    email: string;
    clearance: 'admin' | 'operator';
    reason: string | null;
    requested_at: string;
}

export interface PendingRequestListResponse {
    requests: PendingRequest[];
    total: number;
}

export async function listAccounts(): Promise<Account[]> {
    const { data } = await apiClient.get<AccountListResponse>('/account', { headers: accountAuthHeaders() });
    return data.accounts;
}

export async function getAccount(aid: number): Promise<Account> {
    const { data } = await apiClient.get<Account>(`/account/${aid}`, { headers: accountAuthHeaders() });
    return data;
}

export async function registerAccount(body: AccountCreate): Promise<Account> {
    const { data } = await apiClient.post<Account>('/account/register', body, { headers: accountAuthHeaders() });
    return data;
}

export async function changePassword(aid: number, newPassword: string): Promise<Account> {
    const { data } = await apiClient.patch<Account>(`/account/${aid}/credentials`, { new_password: newPassword }, { headers: accountAuthHeaders() });
    return data;
}

export async function deactivateAccount(aid: number): Promise<Account> {
    const { data } = await apiClient.patch<Account>(`/account/${aid}/deactivate`, {}, { headers: accountAuthHeaders() });
    return data;
}

export async function submitRegistrationRequest(
    body: AccountRegisterRequest,
): Promise<PendingRequest> {
    const { data } = await apiClient.post<PendingRequest>('/account/request', body);
    return data;
}

export async function listPendingRequests(): Promise<PendingRequest[]> {
    const { data } = await apiClient.get<PendingRequestListResponse>('/account/requests/pending', { headers: accountAuthHeaders() });
    return data.requests;
}

export async function approveRequest(requestId: number): Promise<Account> {
    const { data } = await apiClient.post<Account>(`/account/requests/${requestId}/approve`, {}, { headers: accountAuthHeaders() });
    return data;
}

export async function denyRequest(requestId: number): Promise<void> {
    await apiClient.post(`/account/requests/${requestId}/deny`, {}, { headers: accountAuthHeaders() });
}
// aduit log

export async function listAuditLog(params?: {
    event_type?: string;
    date_from?: string;
    date_to?: string;
}): Promise<AuditLogEntry[]> {
    const { data } = await apiClient.get<AuditLogListResponse>('/account/audit-log', { params, headers: accountAuthHeaders() });
    return data.entries;
}