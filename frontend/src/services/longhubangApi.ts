import { apiPost, apiGet, apiDelete } from './api'
import type {
  LonghubangAnalysisRequest,
  LonghubangAnalysisResponse,
  LonghubangReportListResponse,
  LonghubangReportDetail,
} from '@/types/longhubang'

export const longhubangApi = {
  analyze: async (request: LonghubangAnalysisRequest) => {
    const response = await apiPost<LonghubangAnalysisResponse>('/longhubang/analyze', request)
    return response.data.data
  },

  getReports: async () => {
    const response = await apiGet<LonghubangReportListResponse>('/longhubang/reports')
    return response.data.data
  },

  getReportDetail: async (reportId: string) => {
    const response = await apiGet<LonghubangReportDetail>(`/longhubang/reports/${reportId}`)
    return response.data.data
  },

  deleteReport: async (reportId: string) => {
    const response = await apiDelete<Record<string, any>>(`/longhubang/reports/${reportId}`)
    return response.data.data
  },

  getStatistics: async () => {
    const response = await apiGet<Record<string, any>>('/longhubang/statistics')
    return response.data.data
  },
}
