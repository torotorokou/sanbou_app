export type Severity = 'success' | 'info' | 'warning' | 'error';

export interface ProblemDetails {
  status: number;
  code: string;
  userMessage: string;
  title?: string;
  traceId?: string;
}

export interface NotificationEvent {
  id: string; // uuid
  severity: Severity;
  title: string;
  message?: string;
  duration?: number | null;
  feature?: string;
  resultUrl?: string;
  jobId?: string;
  traceId?: string;
  createdAt: string; // ISO8601
}
