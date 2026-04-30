export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  tool_uses?: ToolUse[];
  tokens_input?: number;
  tokens_output?: number;
  created_at?: string;
}

export interface ToolUse {
  name: string;
  input: Record<string, unknown>;
  output?: string;
  duration_ms?: number;
  is_error?: boolean;
  permission_decision?: string;
}

export interface SessionInfo {
  id: string;
  agent_id: string;
  status: string;
  title: string;
  created_at: string;
}

export interface MemoryFact {
  id: string;
  content: string;
  category: string;
}
