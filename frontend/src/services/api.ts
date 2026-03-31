import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import type { SuccessResponse, ErrorResponse } from '@/types/api'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const apiClient: AxiosInstance = axios.create({
  baseURL,
  timeout: 600000,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  (response: AxiosResponse<SuccessResponse>) => {
    return response
  },
  (error) => {
    const errorResponse: ErrorResponse = {
      code: error.response?.status || 500,
      message: error.response?.data?.message || error.message || '请求失败',
      errors: error.response?.data?.errors,
    }
    return Promise.reject(errorResponse)
  }
)

export default apiClient

export const apiGet = <T = any>(url: string, config?: AxiosRequestConfig) => {
  return apiClient.get<SuccessResponse<T>>(url, config)
}

export const apiPost = <T = any>(url: string, data?: any, config?: AxiosRequestConfig) => {
  return apiClient.post<SuccessResponse<T>>(url, data, config)
}

export const apiPut = <T = any>(url: string, data?: any, config?: AxiosRequestConfig) => {
  return apiClient.put<SuccessResponse<T>>(url, data, config)
}

export const apiDelete = <T = any>(url: string, config?: AxiosRequestConfig) => {
  return apiClient.delete<SuccessResponse<T>>(url, config)
}
