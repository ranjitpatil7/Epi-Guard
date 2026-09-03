import { client } from "./client";

export interface CopilotRequest {
  message: string;
  conversation_id?: number;
  region_id?: number;
}

export interface PredictionInterval {
  lower: number;
  upper: number;
}

export interface EvidenceCitation {
  source: string;
  excerpt: string;
}

export interface AgentTrace {
  iteration?: number;
  tool?: string;
  arguments?: any;
  success?: boolean;
  latency_ms?: number;
  error?: string;
  action?: string;
  status?: string;
}

export interface CopilotResponse {
  answer: string;
  risk_level?: string;
  prediction_interval?: PredictionInterval;
  confidence?: number;
  risk_trend?: string;
  contributing_factors?: string[];
  spatial_factors?: string[];
  forecast?: any;
  anomalies?: string[];
  alerts?: string[];
  scenario_results?: any;
  retrieved_evidence?: EvidenceCitation[];
  citations?: string[];
  sources?: string[];
  agent_trace?: AgentTrace[];
  data_quality?: number;
  limitations?: string;
  disclaimer: string;
}

export interface ConversationInfo {
  id: number;
  title: string;
  updated_at: string;
}

export interface MessageHistory {
  role: string;
  content: string;
  structured_response?: CopilotResponse;
}

export const chatWithCopilot = async (request: CopilotRequest): Promise<CopilotResponse> => {
  const { data } = await client.post("/copilot/chat", request);
  return data;
};

export const investigateWithCopilot = async (request: CopilotRequest): Promise<CopilotResponse> => {
  const { data } = await client.post("/copilot/investigate", request);
  return data;
};

export const getConversations = async (): Promise<ConversationInfo[]> => {
  const { data } = await client.get("/copilot/conversations");
  return data;
};

export const getConversationHistory = async (conversationId: number): Promise<MessageHistory[]> => {
  const { data } = await client.get(`/copilot/conversations/${conversationId}`);
  return data;
};

export const getInvestigationTrace = async (conversationId: number): Promise<AgentTrace[]> => {
  const { data } = await client.get(`/copilot/trace/${conversationId}`);
  return data;
};
