/**
 * 会话状态管理
 * 使用Pinia管理会话列表和当前会话
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Session {
  session_id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export const useSessionStore = defineStore('session', () => {
  // State
  const sessions = ref<Session[]>([])
  const currentSessionId = ref<string>('default_session')
  const loading = ref(false)
  
  // Getters
  const currentSession = computed(() => {
    return sessions.value.find(s => s.session_id === currentSessionId.value)
  })
  
  const sortedSessions = computed(() => {
    return [...sessions.value].sort((a, b) => {
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    })
  })
  
  // Actions
  
  /**
   * 设置会话列表
   */
  function setSessions(newSessions: Session[]) {
    sessions.value = newSessions
  }
  
  /**
   * 添加会话
   */
  function addSession(session: Session) {
    sessions.value.unshift(session)
  }
  
  /**
   * 删除会话
   */
  function removeSession(sessionId: string) {
    const index = sessions.value.findIndex(s => s.session_id === sessionId)
    if (index !== -1) {
      sessions.value.splice(index, 1)
    }
  }
  
  /**
   * 更新会话
   */
  function updateSession(sessionId: string, updates: Partial<Session>) {
    const session = sessions.value.find(s => s.session_id === sessionId)
    if (session) {
      Object.assign(session, updates)
    }
  }
  
  /**
   * 切换当前会话
   */
  function switchSession(sessionId: string) {
    currentSessionId.value = sessionId
  }
  
  /**
   * 创建新会话(本地)
   */
  function createLocalSession(session: Session) {
    addSession(session)
    switchSession(session.session_id)
  }
  
  return {
    // State
    sessions,
    currentSessionId,
    loading,
    // Getters
    currentSession,
    sortedSessions,
    // Actions
    setSessions,
    addSession,
    removeSession,
    updateSession,
    switchSession,
    createLocalSession
  }
})
