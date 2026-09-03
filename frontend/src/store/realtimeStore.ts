/**
 * Realtime Store — JalRakshak AI Command Center
 *
 * Manages WebSocket connection lifecycle state and a bounded live event timeline.
 * Uses Zustand for minimal, predictable state management.
 *
 * DESIGN RULES:
 *  - This store is READ-ONLY from the WebSocket perspective.
 *    The server pushes events; the client never pushes domain events back.
 *  - The timeline is bounded to MAX_TIMELINE_EVENTS to prevent unbounded memory growth.
 *  - Critical events (ALERT_ESCALATED, INCIDENT_CREATED, INCIDENT_ESCALATED)
 *    are never silently discarded when the buffer is full.
 *  - Risk/severity/confidence values displayed here come exclusively from
 *    the deterministic backend (PostgreSQL + CEP + Risk Engine).
 *    The frontend NEVER computes these values.
 */

import { create } from 'zustand';

// ─── Types ─────────────────────────────────────────────────────────────────────

export type ConnectionStatus =
  | 'CONNECTING'
  | 'CONNECTED'
  | 'RECONNECTING'
  | 'DISCONNECTED'
  | 'ERROR';

/** Standard envelope matching backend WebSocketMessage schema. */
export interface WSMessage {
  message_id: string;
  event_type: string;
  timestamp: string;
  region_id?: number;
  correlation_id?: string;
  severity?: string;
  payload: Record<string, unknown>;
}

// Event types that must never be silently discarded from the timeline
const CRITICAL_EVENT_TYPES = new Set([
  'ALERT_ESCALATED',
  'INTELLIGENCE_INCIDENT_CREATED',
  'INTELLIGENCE_INCIDENT_ESCALATED',
]);

const MAX_TIMELINE_EVENTS = 100;

// ─── Store interface ────────────────────────────────────────────────────────────

interface RealtimeState {
  // Connection
  status: ConnectionStatus;
  connectedAt: string | null;
  reconnectAttempts: number;
  lastError: string | null;

  // Events
  timeline: WSMessage[];
  lastEvent: WSMessage | null;
  criticalEventCount: number;

  // Actions
  setStatus: (status: ConnectionStatus) => void;
  setConnected: () => void;
  setReconnecting: (attempt: number) => void;
  setError: (msg: string) => void;
  setDisconnected: () => void;
  pushEvent: (event: WSMessage) => void;
  clearTimeline: () => void;
}

// ─── Store implementation ───────────────────────────────────────────────────────

export const useRealtimeStore = create<RealtimeState>()((set) => ({
  // Initial state
  status: 'DISCONNECTED',
  connectedAt: null,
  reconnectAttempts: 0,
  lastError: null,
  timeline: [],
  lastEvent: null,
  criticalEventCount: 0,

  setStatus: (status) => set({ status }),

  setConnected: () =>
    set({
      status: 'CONNECTED',
      connectedAt: new Date().toISOString(),
      reconnectAttempts: 0,
      lastError: null,
    }),

  setReconnecting: (attempt) =>
    set({
      status: 'RECONNECTING',
      reconnectAttempts: attempt,
    }),

  setError: (msg) =>
    set({
      status: 'ERROR',
      lastError: msg,
    }),

  setDisconnected: () =>
    set({
      status: 'DISCONNECTED',
    }),

  pushEvent: (event) =>
    set((state) => {
      // Prevent duplicate events (often caused by React StrictMode double WebSocket connections in dev)
      if (state.timeline.some(e => e.message_id === event.message_id)) {
        return state;
      }

      const isCritical = CRITICAL_EVENT_TYPES.has(event.event_type);
      let timeline = [...state.timeline, event];

      // Enforce bounded buffer — drop oldest non-critical events first
      if (timeline.length > MAX_TIMELINE_EVENTS) {
        const excessCount = timeline.length - MAX_TIMELINE_EVENTS;
        let dropped = 0;
        const trimmed: WSMessage[] = [];

        for (const e of timeline) {
          if (dropped < excessCount && !CRITICAL_EVENT_TYPES.has(e.event_type)) {
            dropped++;
          } else {
            trimmed.push(e);
          }
        }

        // Fallback: if we still exceed the limit (all events are critical), drop oldest
        timeline = trimmed.length <= MAX_TIMELINE_EVENTS
          ? trimmed
          : trimmed.slice(trimmed.length - MAX_TIMELINE_EVENTS);
      }

      return {
        timeline,
        lastEvent: event,
        criticalEventCount: state.criticalEventCount + (isCritical ? 1 : 0),
      };
    }),

  clearTimeline: () =>
    set({
      timeline: [],
      criticalEventCount: 0,
    }),
}));
