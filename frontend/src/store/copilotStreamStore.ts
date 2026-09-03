import { create } from 'zustand';

export interface CopilotStreamStep {
    sequence_number: number;
    timestamp: string;
    event_type: string;
    payload: Record<string, any>;
}

interface CopilotStreamState {
    activeRequestId: string | null;
    conversationId: number | null;
    steps: CopilotStreamStep[];
    isStreaming: boolean;
    error: string | null;
    
    startStream: (requestId: string) => void;
    addStep: (step: CopilotStreamStep, requestId: string, conversationId: number) => void;
    endStream: () => void;
    failStream: (error: string) => void;
    resetStream: () => void;
}

export const useCopilotStreamStore = create<CopilotStreamState>((set, get) => ({
    activeRequestId: null,
    conversationId: null,
    steps: [],
    isStreaming: false,
    error: null,

    startStream: (requestId: string) => set({
        activeRequestId: requestId,
        steps: [],
        isStreaming: true,
        error: null,
        conversationId: null
    }),

    addStep: (step: CopilotStreamStep, requestId: string, conversationId: number) => {
        const state = get();
        // Ignore stale events or events for other requests
        if (state.activeRequestId !== requestId) {
            return;
        }

        // Prevent duplicate insertion by sequence_number
        if (state.steps.some(s => s.sequence_number === step.sequence_number)) {
            return;
        }

        set((prev) => {
            const newSteps = [...prev.steps, step];
            // Ensure ordered by sequence_number
            newSteps.sort((a, b) => a.sequence_number - b.sequence_number);
            return {
                steps: newSteps,
                conversationId: conversationId
            };
        });
    },

    endStream: () => set({ isStreaming: false }),
    
    failStream: (error: string) => set({ isStreaming: false, error }),
    
    resetStream: () => set({
        activeRequestId: null,
        conversationId: null,
        steps: [],
        isStreaming: false,
        error: null
    })
}));
