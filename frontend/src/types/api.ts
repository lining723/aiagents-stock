export interface ResponseBase {
  code: number
  message: string
}

export interface SuccessResponse<T = any> extends ResponseBase {
  data?: T
}

export interface ErrorResponse extends ResponseBase {
  errors?: any[]
}

export interface HealthCheckResponse {
  status: string
  service: string
  version: string
}
