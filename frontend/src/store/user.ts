/**
 * 用户状态管理
 * 使用Pinia管理用户登录状态和信息
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userApi } from '../api'
import apiClient from '../api'

export interface User {
  id: number
  username: string
  email: string
  created_at: string
}

export const useUserStore = defineStore('user', () => {
  // State - 从localStorage恢复token和用户信息
  const token = ref<string | null>(localStorage.getItem('token'))
  const userJson = localStorage.getItem('user')
  const user = ref<User | null>(userJson ? JSON.parse(userJson) : null)
  
  // Getters
  const isLoggedIn = computed(() => !!token.value)
  
  // Actions
  
  /**
   * 用户注册
   */
  async function register(username: string, email: string, password: string) {
    try {
      const response = await userApi.register({ username, email, password })
      
      // 保存token和用户信息
      token.value = response.access_token
      user.value = response.user
      
      // 持久化到localStorage
      localStorage.setItem('token', response.access_token)
      localStorage.setItem('user', JSON.stringify(response.user))
      
      return { success: true }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '注册失败'
      }
    }
  }
  
  /**
   * 用户登录
   */
  async function login(username: string, password: string) {
    try {
      const response = await userApi.login({ username, password })
      
      // 保存token和用户信息
      token.value = response.access_token
      user.value = response.user
      
      // 持久化到localStorage
      localStorage.setItem('token', response.access_token)
      localStorage.setItem('user', JSON.stringify(response.user))
      
      return { success: true }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '登录失败'
      }
    }
  }
  
  /**
   * 获取当前用户信息
   */
  async function fetchUserInfo() {
    if (!token.value) return
    
    try {
      const userInfo = await userApi.getCurrentUser()
      user.value = userInfo
      // 更新localStorage中的用户信息
      localStorage.setItem('user', JSON.stringify(userInfo))
    } catch (error: any) {
      // Token可能已过期,清除登录状态
      console.error('获取用户信息失败:', error)
      console.error('错误详情:', error.response?.data)
      console.error('状态码:', error.response?.status)
      
      // 只有在401(未授权)时才清除登录状态
      if (error.response?.status === 401) {
        console.log('Token已过期或无效,已清除登录状态')
        logout()
      }
    }
  }
  
  /**
   * 用户登出（服务端 Token 黑名单 + 本地清理）
   */
  async function logout() {
    // 先通知后端将 Token 加入 Redis 黑名单
    try {
      await apiClient.post('/api/user/logout')
    } catch (e) {
      console.warn('后端登出请求失败，继续本地登出', e)
    }
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }
  
  // 不在初始化时验证token,避免刷新时立即清除登录状态
  // 如果token无效,会在实际调用API时自然失败并跳转到登录页
  
  return {
    // State
    token,
    user,
    // Getters
    isLoggedIn,
    // Actions
    register,
    login,
    logout,
    fetchUserInfo
  }
})
