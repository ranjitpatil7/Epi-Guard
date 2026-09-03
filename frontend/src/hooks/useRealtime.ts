/**
 * useRealtime — WebSocket hook for JalRakshak AI Command Center
 *
 * Manages the full WebSocket lifecycle:
 *  - Connection with authentication token
 *  - Automatic reconnection with exponential backoff (1s → 2s → 4s → 8s → 16s → 30s)
 *  - Heartbeat/ping to keep connection alive and detect stale connections
 *  - Safe unmount cleanup to prevent memory leaks
 *  - Duplicate connection prevention
 *  - React Query cache invalidation on relevant events
 *  - Malformed message protection
 *
 * SECURITY:
 *  - The client NEVER sends domain events back to the server.
 *  - Only {"type": "ping"} heartbeat messages are sent.
 *  - Risk/severity/confidence values displayed always originate from
 *    the deterministic backend. The frontend never computes these.
 *
 * FALLBACK:
 *  - If WebSocket is unavailable, React Query polling continues normally.
 *    The dashboard degrades gracefully to REST-only mode.
 */

import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useRealtimeStore, type WSMessage } from '@/store/realtimeStore';
import { useCopilotStreamStore, type CopilotStreamStep } from '@/store/copilotStreamStore';

// ─── Configuration ──────────────────────────────────────────────────────────────

const WS_BASE_URL = (() => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  // In dev with Vite proxy this needs to point to the backend directly
  const host = import.meta.env.VITE_API_HOST ?? window.location.host;
  return `${protocol}//${host}/api/v1/realtime/ws/intelligence`;
})();

const HEARTBEAT_INTERVAL_MS = 25_000; // 25 s — slightly shorter than server's 30 s timeout
const RECONNECT_DELAYS_MS = [1000, 2000, 4000, 8000, 16000, 30000];

// Query keys to invalidate on specific event types
const QUERY_INVALIDATION_MAP: Record<string, string[][]> = {
  RISK_RECALCULATED: [['currentRisk'], ['riskSnapshots']],
  RISK_ESCALATED: [['currentRisk']],
  RISK_DEESCALATED: [['currentRisk']],
  ALERT_CREATED: [['alerts']],
  ALERT_ESCALATED: [['alerts']],
  ALERT_DEESCALATED: [['alerts']],
  ALERT_RESOLVED: [['alerts']],
  INTELLIGENCE_INCIDENT_CREATED: [['incidents']],
  INTELLIGENCE_INCIDENT_UPDATED: [['incidents']],
  INTELLIGENCE_INCIDENT_ESCALATED: [['incidents']],
  INTELLIGENCE_INCIDENT_RESOLVED: [['incidents']],
};

// ─── Hook ───────────────────────────────────────────────────────────────────────

export function useRealtime() {
  const queryClient = useQueryClient();
  const store = useRealtimeStore();

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isMountedRef = useRef(true);

  const clearTimers = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
  }, []);

  const startHeartbeat = useCallback((ws: WebSocket) => {
    heartbeatTimerRef.current = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        try {
          ws.send(JSON.stringify({ type: 'ping' }));
        } catch {
          // Ignore send errors — stale detection will handle cleanup
        }
      }
    }, HEARTBEAT_INTERVAL_MS);
  }, []);

  const handleMessage = useCallback(
    (raw: string) => {
      let msg: WSMessage;
      try {
        msg = JSON.parse(raw) as WSMessage;
      } catch {
        console.warn('[WS] Malformed message discarded');
        return;
      }

      // Ignore server-side heartbeat acks silently
      if (msg.event_type === 'HEARTBEAT_ACK') return;

      // Check if it's a Copilot streaming event
      const copilotEventTypes = [
        'COPILOT_REQUEST_STARTED', 'AGENT_THINKING', 'TOOL_SELECTED',
        'TOOL_EXECUTION_STARTED', 'TOOL_EXECUTION_COMPLETED', 'TOOL_EXECUTION_FAILED',
        'EVIDENCE_RETRIEVED', 'RAG_RETRIEVAL_STARTED', 'RAG_RETRIEVAL_COMPLETED',
        'AGENT_SYNTHESIS_STARTED', 'FINAL_SYNTHESIS', 'COPILOT_REQUEST_COMPLETED',
        'COPILOT_REQUEST_FAILED'
      ];

      if (copilotEventTypes.includes(msg.event_type)) {
        if (!msg.payload.request_id || !msg.payload.sequence_number) {
          console.warn('[WS] Malformed Copilot event missing correlation ids');
          return;
        }

        const step: CopilotStreamStep = {
          sequence_number: Number(msg.payload.sequence_number),
          timestamp: String(msg.payload.timestamp),
          event_type: msg.event_type,
          payload: msg.payload
        };

        useCopilotStreamStore.getState().addStep(
          step, 
          String(msg.payload.request_id), 
          Number(msg.payload.conversation_id)
        );
        return;
      }

      // Push to timeline store
      store.pushEvent(msg);

      // Invalidate React Query caches for relevant event types
      const queryKeys = QUERY_INVALIDATION_MAP[msg.event_type];
      if (queryKeys) {
        for (const key of queryKeys) {
          queryClient.invalidateQueries({ queryKey: key });
        }
      }
    },
    [store, queryClient]
  );

  const connect = useCallback(() => {
    if (!isMountedRef.current) return;

    // Prevent duplicate connections
    if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
      return;
    }

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      store.setError('No authentication token found');
      return;
    }

    const url = `${WS_BASE_URL}?token=${token}`;
    store.setStatus('CONNECTING');

    let ws: WebSocket;
    try {
      ws = new WebSocket(url);
    } catch (err) {
      store.setError(`Failed to create WebSocket: ${err}`);
      return;
    }

    wsRef.current = ws;

    ws.onopen = () => {
      if (!isMountedRef.current) {
        ws.close();
        return;
      }
      store.setConnected();
      reconnectAttemptRef.current = 0;
      startHeartbeat(ws);
    };

    ws.onmessage = (event) => {
      handleMessage(event.data as string);
    };

    ws.onerror = () => {
      store.setError('WebSocket error');
    };

    ws.onclose = (event) => {
      clearTimers();
      wsRef.current = null;

      if (!isMountedRef.current) return;

      if (event.code === 4001) {
        // Authentication failure — do not reconnect
        store.setError('Authentication failed');
        return;
      }

      if (event.code === 4003) {
        // Server rejected a client mutation attempt — do not reconnect
        store.setError('Connection terminated: mutation not allowed');
        return;
      }

      // Schedule reconnect with exponential backoff
      const attempt = reconnectAttemptRef.current;
      const delay = RECONNECT_DELAYS_MS[Math.min(attempt, RECONNECT_DELAYS_MS.length - 1)];
      reconnectAttemptRef.current = attempt + 1;

      store.setReconnecting(reconnectAttemptRef.current);

      reconnectTimerRef.current = setTimeout(() => {
        if (isMountedRef.current) connect();
      }, delay);
    };
  }, [store, startHeartbeat, clearTimers, handleMessage]);

  useEffect(() => {
    isMountedRef.current = true;
    connect();

    return () => {
      isMountedRef.current = false;
      clearTimers();
      if (wsRef.current) {
        wsRef.current.onclose = null;
        // In React 18 StrictMode dev, do not aggressively close connecting sockets to avoid console errors.
        if (wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.close();
        }
        wsRef.current = null;
      }
      store.setDisconnected();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    status: store.status,
    timeline: store.timeline,
    lastEvent: store.lastEvent,
    criticalEventCount: store.criticalEventCount,
    reconnectAttempts: store.reconnectAttempts,
  };
}
