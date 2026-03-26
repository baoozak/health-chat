/**
 * API客户端
 * 封装所有后端API调用
 */
import axios from 'axios'

// 从环境变量读取 API 基础地址
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 自动添加token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
)

/**
 * 聊天API接口
 */
export interface ChatRequest {
  message: string
  session_id: string
}

/**
 * 通用 SSE 流解析（处理粘包/半包问题）
 * ReadableStream 的 chunk 不保证按行边界切割，需要维护 buffer
 */
async function processSSEStream(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  onChunk: (text: string) => void,
  onComplete: () => void,
  onError: (error: Error) => void
) {
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()

      if (done) break

      // stream: true 避免多字节 UTF-8 字符被截断
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      // 最后一个元素可能不完整，放回 buffer
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed.startsWith('data: ')) continue
        const data = trimmed.slice(6)

        if (data === '[DONE]') {
          onComplete()
          return
        }

        try {
          const json = JSON.parse(data)
          if (json.error) {
            onError(new Error(json.error))
            return
          }
          if (json.text) {
            onChunk(json.text)
          }
        } catch (_e) {
          // JSON 解析失败，可能是非数据行，跳过
        }
      }
    }
    onComplete()
  } catch (error: any) {
    onError(error)
  }
}

/**
 * 发送聊天消息（流式）
 */
export async function sendChatMessage(
  message: string,
  sessionId: string,
  onChunk: (text: string) => void,
  onComplete: () => void,
  onError: (error: Error) => void
) {
  try {
    const token = localStorage.getItem('token')
    
    const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify({ message, session_id: sessionId })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('无法获取响应流')
    }
    
    await processSSEStream(reader, onChunk, onComplete, onError)
  } catch (error: any) {
    onError(error)
  }
}

/**
 * 文件上传API
 */
export async function uploadFileWithMessage(
  file: File,
  message: string,
  sessionId: string,
  onChunk: (text: string) => void,
  onComplete: () => void,
  onError: (error: Error) => void
) {
  try {
    const token = localStorage.getItem('token')
    
    const formData = new FormData()
    formData.append('file', file)
    formData.append('message', message)
    formData.append('session_id', sessionId)
    
    const headers: Record<string, string> = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    const response = await fetch(`${API_BASE_URL}/api/upload/file`, {
      method: 'POST',
      headers,
      body: formData
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('无法获取响应流')
    }
    
    await processSSEStream(reader, onChunk, onComplete, onError)
  } catch (error: any) {
    onError(error)
  }
}

/**
 * 会话API
 */
export interface Session {
  session_id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export interface Message {
  id: string
  type: string
  content: string
  timestamp: string
  image_data?: string
  image_filename?: string
  image_mime_type?: string
}

export const sessionApi = {
  async getSessions(): Promise<Session[]> {
    const response = await apiClient.get<{ sessions: Session[] }>('/api/sessions')
    return response.data.sessions
  },

  async createSession(title: string = '新对话'): Promise<Session> {
    const response = await apiClient.post<Session>('/api/sessions', { title })
    return response.data
  },

  async deleteSession(sessionId: string): Promise<void> {
    await apiClient.delete(`/api/sessions/${sessionId}`)
  },

  async getSessionMessages(sessionId: string): Promise<Message[]> {
    const response = await apiClient.get<{ messages: Message[] }>(`/api/sessions/${sessionId}/messages`)
    return response.data.messages
  },

  async updateSession(sessionId: string, title: string): Promise<void> {
    await apiClient.put(`/api/sessions/${sessionId}`, { title })
  }
}

/**
 * 用户API接口
 */
export interface UserRegisterRequest {
  username: string
  email: string
  password: string
}

export interface UserLoginRequest {
  username: string
  password: string
}

export interface User {
  id: number
  username: string
  email: string
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export const userApi = {
  async register(data: UserRegisterRequest): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/api/user/register', data)
    return response.data
  },

  async login(data: UserLoginRequest): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/api/user/login', data)
    return response.data
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/api/user/me')
    return response.data
  }
}

export default apiClient
