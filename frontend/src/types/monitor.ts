export interface EntryRange {
  min: number
  max: number
}

export interface MonitoredStock {
  id: string
  symbol: string
  name: string
  rating: string
  entry_range: Record<string, any>
  take_profit?: number
  stop_loss?: number
  current_price?: number
  last_checked?: string
  check_interval: number
  notification_enabled: boolean
  trading_hours_only: boolean
  quant_enabled: boolean
  quant_config?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface MonitoredStockCreate {
  symbol: string
  name: string
  rating: string
  entry_range: EntryRange
  take_profit: number
  stop_loss: number
  check_interval: number
  notification_enabled: boolean
  trading_hours_only: boolean
  quant_enabled: boolean
  quant_config?: Record<string, any>
}

export interface MonitoredStockUpdate {
  rating?: string
  entry_range?: EntryRange
  take_profit?: number
  stop_loss?: number
  check_interval?: number
  notification_enabled?: boolean
  trading_hours_only?: boolean
  quant_enabled?: boolean
  quant_config?: Record<string, any>
}

export interface MonitoredStockListResponse {
  success: boolean
  message: string
  stocks: MonitoredStock[]
  total: number
}

export interface MonitoredStockResponse {
  success: boolean
  message: string
  stock?: MonitoredStock
}

export interface NotificationInfo {
  id: string
  stock_id: string
  symbol: string
  name: string
  type: string
  message: string
  triggered_at: string
  sent: boolean
}

export interface NotificationListResponse {
  success: boolean
  message: string
  notifications: NotificationInfo[]
  total: number
}

export interface MonitorConfig {
  monitor_enabled: boolean
  check_interval: number
  auto_notification: boolean
}

export interface MonitorConfigResponse {
  success: boolean
  message: string
  config: MonitorConfig
}
