import { apiGet, apiPost, apiPut, apiDelete } from './api'
import type {
  MonitorConfig,
  MonitorConfigResponse,
  MonitoredStockListResponse,
  MonitoredStockResponse,
  MonitoredStockCreate,
  MonitoredStockUpdate,
  NotificationListResponse,
} from '@/types/monitor'

export const monitorApi = {
  getConfig: async () => {
    const response = await apiGet<MonitorConfigResponse>('/monitor/config')
    return response.data.data
  },

  updateConfig: async (config: MonitorConfig) => {
    const response = await apiPut<MonitorConfigResponse>('/monitor/config', config)
    return response.data.data
  },

  getStocks: async () => {
    const response = await apiGet<MonitoredStockListResponse>('/monitor/stocks')
    return response.data.data
  },

  addStock: async (stock: MonitoredStockCreate) => {
    const response = await apiPost<MonitoredStockResponse>('/monitor/stocks', stock)
    return response.data.data
  },

  getStock: async (stockId: string) => {
    const response = await apiGet<MonitoredStockResponse>(`/monitor/stocks/${stockId}`)
    return response.data.data
  },

  updateStock: async (stockId: string, stock: MonitoredStockUpdate) => {
    const response = await apiPut<MonitoredStockResponse>(`/monitor/stocks/${stockId}`, stock)
    return response.data.data
  },

  deleteStock: async (stockId: string) => {
    const response = await apiDelete<Record<string, any>>(`/monitor/stocks/${stockId}`)
    return response.data.data
  },

  getNotifications: async (limit: number = 20) => {
    const response = await apiGet<NotificationListResponse>(`/monitor/notifications?limit=${limit}`)
    return response.data.data
  },

  markNotificationsRead: async () => {
    const response = await apiPost<Record<string, any>>('/monitor/notifications/mark-read', {})
    return response.data.data
  },

  clearNotifications: async () => {
    const response = await apiDelete<Record<string, any>>('/monitor/notifications')
    return response.data.data
  },
}
