export interface StockInfo {
  symbol: string
  name: string
  pe_ratio?: number
  pb_ratio?: number
  dividend_rate?: number
  debt_ratio?: number
  market_cap?: number
  industry?: string
  range_change?: number
  main_fund_inflow?: number
}

export interface StockListResponse {
  success: boolean
  message: string
  count: number
  stocks: StockInfo[]
  timestamp: string
}

export interface ValueStockRequest {
  top_n: number
  pe_max?: number
  pb_max?: number
}

export interface MainForceStockRequest {
  days_ago: number
  min_market_cap: number
  max_market_cap: number
  max_range_change: number
  top_n: number
}

export interface TechnicalIndicator {
  name: string
  value?: number
  signal?: string
  description?: string
}

export interface KlineData {
  date: string
  open: number
  close: number
  high: number
  low: number
  volume: number
  ma5?: number
  ma10?: number
  ma20?: number
}

export interface TechnicalAnalysisRequest {
  symbol: string
  days_ago: number
}

export interface BatchAIAnalysisRequest {
  symbols: string[]
  days_ago?: number
}

export interface BatchAIAnalysisResponse {
  success: boolean
  message: string
  total: number
  success_count: number
  failed_count: number
  results: AIAnalysisResponse[]
  failed_symbols: string[]
}

export interface TechnicalAnalysisResponse {
  success: boolean
  message: string
  symbol: string
  name?: string
  current_price?: number
  change_percent?: number
  indicators: TechnicalIndicator[]
  kline_data?: KlineData[]
  summary?: string
  timestamp: string
}

export interface FundamentalMetric {
  name: string
  value?: number
  unit?: string
  rank?: string
  description?: string
}

export interface FundamentalAnalysisRequest {
  symbol: string
}

export interface FundamentalAnalysisResponse {
  success: boolean
  message: string
  symbol: string
  name?: string
  industry?: string
  market_cap?: number
  pe_ratio?: number
  pb_ratio?: number
  roe?: number
  debt_ratio?: number
  dividend_rate?: number
  metrics: FundamentalMetric[]
  summary?: string
  timestamp: string
}

export interface AnalysisScore {
  category: string
  score: number
  weight: number
}

export interface AIAnalysisRequest {
  symbol: string
}

export interface AIAnalysisResponse {
  success: boolean
  message: string
  symbol: string
  name?: string
  ai_report: string
  timestamp: string
}

export interface ComprehensiveAnalysisRequest {
  symbol: string
  days_ago: number
}

export interface ComprehensiveAnalysisResponse {
  success: boolean
  message: string
  symbol: string
  name?: string
  overall_score: number
  overall_rating: string
  scores: AnalysisScore[]
  technical_analysis?: TechnicalAnalysisResponse
  fundamental_analysis?: FundamentalAnalysisResponse
  risks: string[]
  opportunities: string[]
  recommendations: string[]
  timestamp: string
}

export interface AnalysisHistoryItem {
  id: string
  symbol: string
  name?: string
  created_at: string
  ai_report?: string
}

export interface AnalysisHistoryListResponse {
  success: boolean
  message: string
  total: number
  items: AnalysisHistoryItem[]
}

export interface AnalysisHistoryDetailResponse {
  success: boolean
  message: string
  data?: AnalysisHistoryItem
}
