export interface LonghubangAnalysisRequest {
  analysis_mode: string
  date?: string
  days: number
}

export interface LonghubangReportInfo {
  report_id: string
  date: string
  created_at: string
  stock_count: number
  youzi_count: number
}

export interface LonghubangReportDetail {
  report_id: string
  date: string
  created_at: string
  data_info: Record<string, any>
  agents_analysis: Record<string, any>
  final_report: Record<string, any>
  recommended_stocks: Record<string, any>[]
}

export interface LonghubangAnalysisResponse {
  success: boolean
  message: string
  report_id?: string
  data_info?: Record<string, any>
  agents_analysis?: Record<string, any>
  final_report?: Record<string, any>
  recommended_stocks?: Record<string, any>[]
}

export interface LonghubangReportListResponse {
  success: boolean
  message: string
  reports: LonghubangReportInfo[]
  total: number
}

export interface RecommendedStock {
  stock_name?: string
  stock_code?: string
  reason?: string
  confidence?: number
  [key: string]: any
}
