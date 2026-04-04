/**
 * Authenticated SSE reader for GET /alerts/stream (fetch + Bearer; not EventSource).
 */
import type { SseAlertEvent } from '../types';

function extractDataLine(block: string): string | null {
  for (const line of block.split('\n')) {
    if (line.startsWith('data:')) {
      return line.replace(/^data:\s?/, '').trim();
    }
  }
  return null;
}

/**
 * Read the response body until aborted; parses SSE blocks and invokes onEvent for each `data:` JSON.
 */
export async function consumeAlertSseStream(
  response: Response,
  onEvent: (evt: SseAlertEvent) => void,
  signal: AbortSignal
): Promise<void> {
  if (!response.body) return;
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (!signal.aborted) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop() ?? '';
      for (const raw of parts) {
        const block = raw.trim();
        if (!block || block.startsWith(':')) continue;
        const json = extractDataLine(block);
        if (!json) continue;
        try {
          const parsed = JSON.parse(json) as SseAlertEvent;
          onEvent(parsed);
        } catch {
          /* ignore malformed chunk */
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export async function openAlertSseStream(
  apiBase: string,
  token: string,
  onEvent: (evt: SseAlertEvent) => void,
  signal: AbortSignal
): Promise<void> {
  const url = `${apiBase.replace(/\/$/, '')}/alerts/stream`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}`, Accept: 'text/event-stream' },
    signal,
  });
  if (!res.ok) return;
  await consumeAlertSseStream(res, onEvent, signal);
}
