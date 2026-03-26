/**
 * 健康分析API
 */
import axios from 'axios'
import type { HealthReport } from '../types'

const API_BASE_URL = 'http://127.0.0.1:8000'

// 创建axios实例
const healthClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000
})

// 请求拦截器 - 添加token
healthClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

/**
 * 健康分析API
 */
export const healthApi = {
  /**
   * 获取健康分析报告
   */
  async getHealthAnalysis(): Promise<{ success: boolean; data: HealthReport; cached: boolean }> {
    const response = await healthClient.get('/api/health/analysis')
    return response.data
  },

  /**
   * 生成新的健康分析报告
   */
  async generateHealthAnalysis(): Promise<{ success: boolean; data: HealthReport; cached: boolean }> {
    const response = await healthClient.post('/api/health/analysis/generate')
    return response.data
  },

  /**
   * 获取健康报告历史
   */
  async getHealthHistory(limit: number = 10): Promise<{ success: boolean; data: HealthReport[]; count: number }> {
    const response = await healthClient.get('/api/health/analysis/history', {
      params: { limit }
    })
    return response.data
  },

  /**
   * 获取健康趋势数据（基于历史报告）
   */
  async getHealthTrends(limit: number = 10): Promise<{ success: boolean; data: any }> {
    const response = await healthClient.get('/api/health/trends', {
      params: { limit }
    })
    return response.data
  }
}
