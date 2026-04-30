export interface AuditLog {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  agent_id?: string;
  status_code?: number;
  error_message?: string;
  details?: string;
  created_at: string;
}
