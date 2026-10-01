export interface Project {
  id: string;
  name: string;
  raw_description: string;
  target_domain: string;
  target_audience?: string;
  status: string;
  current_phase?: string;
  created_at: string;
  clusters_count: number;
  keywords_count: number;
  pages_count: number;
  health_score: number;
}

export interface PipelineEvent {
  project_id: string;
  phase: string;
  step: string;
  message: string;
  progress_percentage: number;
  status: string;
  data_preview?: Record<string, any>;
  timestamp: string;
}

export interface PageSummary {
  slug: string;
  url_path: string;
  title: string;
  h1: string;
  primary_keyword?: string;
  secondary_keywords: string[];
  cluster: string;
  page_type: string;
  search_intent: string;
  word_count: number;
  health_score: number;
  schema_type: string;
  has_jsx_component: boolean;
}

export interface FAQItem {
  question: string;
  answer: string;
  target_question_keyword?: string;
}

export interface InternalLinkItem {
  target_slug: string;
  target_url: string;
  anchor_text: string;
  relationship: string;
}

export interface PageDetail extends PageSummary {
  meta_description: string;
  canonical_url: string;
  robots: string;
  markdown_content: string;
  nextjs_jsx_code: string;
  faqs: FAQItem[];
  internal_links: InternalLinkItem[];
  schema_json_ld: Record<string, any>;
  validation_issues: string[];
}

export interface PageIndexStatus {
  slug: string;
  url: string;
  title: string;
  cluster: string;
  primary_keyword: string;
  is_indexed: boolean;
  index_verdict: string;
  first_detected_date?: string;
  impressions_7d: number;
  impressions_30d: number;
  clicks_7d: number;
  clicks_30d: number;
  avg_position: number;
  ctr_percentage: number;
  status_category: "indexed_and_alive" | "indexed_silent" | "invisible_anomaly" | "breakout_candidate";
  mined_queries: string[];
}

export interface MonitoringAlert {
  id: string;
  severity: "info" | "warning" | "critical";
  alert_type: string;
  page_slug?: string;
  message: string;
  recommendation: string;
  created_at: string;
}

export interface MonitoringDashboardData {
  project_id: string;
  total_pages_monitored: number;
  indexed_pages_count: number;
  indexed_percentage: number;
  total_impressions_7d: number;
  total_clicks_7d: number;
  avg_click_through_rate: number;
  pages: PageIndexStatus[];
  active_alerts: MonitoringAlert[];
  category_breakdown: Record<string, number>;
  last_synced_at: string;
  recommendations_summary: string[];
}
