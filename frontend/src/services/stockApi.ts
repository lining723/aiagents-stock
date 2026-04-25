import { apiPost, apiGet, apiDelete } from './api'
import type { 
  StockListResponse, 
  ValueStockRequest, 
  MainForceStockRequest,
  BatchAIAnalysisRequest,
  BatchAIAnalysisResponse,
  TechnicalAnalysisRequest,
  TechnicalAnalysisResponse,
  FundamentalAnalysisRequest,
  FundamentalAnalysisResponse,
  PricePredictionRequest,
  PricePredictionResponse,
  ComprehensiveAnalysisRequest,
  ComprehensiveAnalysisResponse,
  AIAnalysisRequest,
  AIAnalysisResponse,
  AnalysisHistoryListResponse,
  AnalysisHistoryDetailResponse,
} from '@/types/stock'

export const stockApi = {
  getValueStocks: async (request: ValueStockRequest) => {
    const response = await apiPost<StockListResponse>('/stock/value', request)
    return response.data.data
  },

  getMainForceStocks: async (request: MainForceStockRequest) => {
    const response = await apiPost<StockListResponse>('/stock/main-force', request)
    return response.data.data
  },

  getStrategies: async () => {
    const response = await apiGet<string[]>('/stock/strategies')
    return response.data.data
  },

  getTechnicalAnalysis: async (request: TechnicalAnalysisRequest) => {
    const response = await apiPost<TechnicalAnalysisResponse>('/analysis/technical', request)
    return response.data.data
  },

  getFundamentalAnalysis: async (request: FundamentalAnalysisRequest) => {
    const response = await apiPost<FundamentalAnalysisResponse>('/analysis/fundamental', request)
    return response.data.data
  },

  getPricePrediction: async (request: PricePredictionRequest) => {
    const response = await apiPost<PricePredictionResponse>('/analysis/price-prediction', request)
    return response.data.data
  },

  getComprehensiveAnalysis: async (request: ComprehensiveAnalysisRequest) => {
    const response = await apiPost<ComprehensiveAnalysisResponse>('/analysis/comprehensive', request)
    return response.data.data
  },

  getAIAnalysis: async (data: AIAnalysisRequest) => {
    const response = await apiPost<AIAnalysisResponse>('/analysis/ai', data)
    return response.data.data
  },

  getBatchAIAnalysis: async (data: BatchAIAnalysisRequest) => {
    const response = await apiPost<BatchAIAnalysisResponse>('/analysis/batch-ai', data)
    return response.data.data
  },

  getAnalysisHistory: async (limit: number = 50, offset: number = 0) => {
    const response = await apiGet<AnalysisHistoryListResponse>(`/analysis/history?limit=${limit}&offset=${offset}`)
    return response.data.data
  },

  getAnalysisHistoryDetail: async (id: string) => {
    const response = await apiGet<AnalysisHistoryDetailResponse>(`/analysis/history/${id}`)
    return response.data.data
  },

  deleteAnalysisHistory: async (id: string) => {
    const response = await apiDelete<Record<string, any>>(`/analysis/history/${id}`)
    return response.data.data
  },
}
