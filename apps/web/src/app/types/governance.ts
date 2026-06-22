export interface GovernancePreviewRow {
  timestamp: string;
  principalId: string;
  applicationName: string;
  accessState: string;
  authResult: string;
  riskSignal: string;
  source_ip: string;
}

export interface GovernanceAnalysis {
  total_log_entries: number;
  total_authentications: number;
  denied_access_count: number;
  failed_count: number;
  success_count: number;
  success_rate: number;
  denial_rate_pct: number;
  failure_rate_pct: number;
  risk_score: number;
  unique_users_count: number;
  unique_apps_count: number;
  admin_weak_auth_events: number;
  off_hours_events: number;
  geo_anomaly_events: number;
  top_failed_users: [string, number][];
  events_per_day: Record<string, number>;
}

export interface GovernanceRecommendation {
  priority: string;
  policy_name: string;
  scenario_or_condition: string;
  recommended_decision: string;
  target: string;
}

export interface GovernancePreview {
  metadata: Record<string, string | number>;
  analysis: GovernanceAnalysis;
  preview_rows: GovernancePreviewRow[];
  recommendations: GovernanceRecommendation[];
  privacy_issues: string[];
  risk_score: number;
  events_per_day: Record<string, number>;
}

export interface GovernanceReport extends GovernancePreview {
  report_markdown: string;
  mode: string;
}
