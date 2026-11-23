export interface Email {
  id: string;
  from_address: string;
  from_name: string | null;
  to_address: string;
  subject: string;
  body: string;
  received_at: string;
  has_attachments: boolean;
}

export interface Classification {
  email_id: string;
  category: string;
  priority: string;
  needs_reply: boolean;
  summary: string;
  confidence: number;
  reasoning: string | null;
  classified_at: string;
  model_used: string;
  is_mock: boolean;
}

export interface Draft {
  id: string;
  email_id: string;
  subject: string;
  body: string;
  status: 'pending' | 'approved' | 'rejected' | 'sent';
  created_at: string;
  updated_at: string;
  approved_at: string | null;
  approved_by: string | null;
  sent_at: string | null;
  rejection_reason: string | null;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  action: string;
  entity_type: string;
  entity_id: string;
  actor: string;
  details: Record<string, unknown> | null;
}

export interface TriageSummary {
  total_emails: number;
  classified: number;
  drafts_created: number;
  by_category: Record<string, number>;
  by_priority: Record<string, number>;
  needs_reply: number;
}

export interface QueueItem {
  email: Email;
  classification: Classification;
  draft: Draft | null;
}

export interface ReviewQueue {
  queue: {
    critical: QueueItem[];
    high: QueueItem[];
    medium: QueueItem[];
    low: QueueItem[];
  };
  total_pending: number;
}
