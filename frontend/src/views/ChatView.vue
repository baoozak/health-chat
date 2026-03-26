<template>
  <NMessageProvider>
    <NLayout has-sider style="height: 100vh; max-height: 100vh;">
      <!-- 侧边栏 -->
      <NLayoutSider :width="280" :collapsed-width="0" :collapsed="sidebarCollapsed" show-trigger="bar"
        collapse-mode="width" @collapse="sidebarCollapsed = true" @expand="sidebarCollapsed = false"
        style="border-right: 1px solid #e0f2e9; box-shadow: 2px 0 8px rgba(24, 160, 88, 0.05);">
        <SessionList :sessions="sessionStore.sortedSessions" :current-session-id="sessionStore.currentSessionId"
          @create-session="handleCreateSession" @select-session="handleSelectSession"
          @delete-session="handleDeleteSession" />
      </NLayoutSider>

      <!-- 主内容区 -->
      <NLayout>
        <NLayoutHeader
          style="height: 64px; padding: 0 24px; display: flex; align-items: center; justify-content: space-between; background: linear-gradient(to right, #ffffff 0%, #f8fffe 100%); border-bottom: 1px solid #e0f2e9; box-shadow: 0 2px 8px rgba(24, 160, 88, 0.05);">
          <div class="header-content">
            <NText strong style="font-size: 18px; color: #2c3e50;">
              {{ sessionStore.currentSession?.title || '个人健康管理助手 🏥' }}
            </NText>
          </div>
          <NSpace :size="12" style="align-items: center;">
            <NButton @click="goToHealth" type="primary" secondary style="border-radius: 10px;">
              <template #icon>
                <NIcon>
                  <HeartOutline />
                </NIcon>
              </template>
              我的健康状态
            </NButton>

            <!-- 用户信息卡片 -->
            <div class="user-info-card">
              <NIcon size="18" style="color: #18a058;">
                <PersonCircleOutline />
              </NIcon>
              <span class="username">{{ userStore.user?.username }}</span>
            </div>

            <NButton @click="handleLogout" quaternary style="border-radius: 10px; color: #5a6c7d;">
              <template #icon>
                <NIcon>
                  <LogOutOutline />
                </NIcon>
              </template>
              登出
            </NButton>
          </NSpace>
        </NLayoutHeader>

        <NLayoutContent style="padding: 0; display: flex; flex-direction: column; height: calc(100vh - 64px);">
          <MessageList :messages="messages" style="flex: 1; overflow-y: auto;" />
          <MessageInput @send="handleSend" @upload-file="handleFileUpload" :loading="loading" />
        </NLayoutContent>
      </NLayout>
    </NLayout>

    <!-- 健康咨询免责声明 -->
    <HealthDisclaimer />
  </NMessageProvider>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NLayout, NLayoutHeader, NLayoutContent, NLayoutSider, NButton, NSpace, NText, NIcon, useMessage, NMessageProvider } from 'naive-ui'
import { HeartOutline, PersonCircleOutline, LogOutOutline } from '@vicons/ionicons5'
import MessageList from '../components/MessageList.vue'
import MessageInput from '../components/MessageInput.vue'
import SessionList from '../components/SessionList.vue'
import HealthDisclaimer from '../components/HealthDisclaimer.vue'
import type { Message } from '../types'
import { MessageType } from '../types'
import { sendChatMessage, uploadFileWithMessage, sessionApi } from '../api'
import { useUserStore } from '../store/user'
import { useSessionStore } from '../store/session'

const router = useRouter()
const userStore = useUserStore()
const sessionStore = useSessionStore()
const message = useMessage()

const messages = ref<Message[]>([])
const loading = ref(false)
const sidebarCollapsed = ref(false)

// 欢迎消息（统一定义，避免重复）
const createWelcomeMessage = (): Message => ({
  id: 'welcome',
  type: MessageType.AI,
  content: `你好！我是你的健康管理助手 🏥

我可以帮助你：
✅ 分析身体状况
✅ 提供健康建议
✅ 解答健康疑问
✅ 制定健康计划
✅ 解读体检报告

⚠️ **重要提示**：
- 我不能替代专业医生诊断
- 身体不适请及时就医
- 紧急情况请拨打120

请告诉我你的健康问题或需求！`,
  timestamp: Date.now()
})

// 仅刷新会话列表元数据（不重新加载消息，避免覆盖正在进行的聊天）
const refreshSessionList = async () => {
  try {
    const sessions = await sessionApi.getSessions()
    sessionStore.setSessions(sessions)
  } catch (error: any) {
    console.warn('刷新会话列表失败:', error.message)
  }
}

// 初始加载会话列表（仅在 onMounted 时调用）
const loadSessions = async () => {
  try {
    const sessions = await sessionApi.getSessions()
    sessionStore.setSessions(sessions)

    // 如果没有会话,创建一个默认会话
    if (sessions.length === 0) {
      await handleCreateSession()
    } else {
      // 加载第一个会话的消息
      if (sessions[0]) {
        await loadSessionMessages(sessions[0].session_id)
      }
    }
  } catch (error: any) {
    message.error(`加载会话列表失败: ${error.message}`)
  }
}

// 加载会话消息
const loadSessionMessages = async (sessionId: string) => {
  try {
    sessionStore.switchSession(sessionId)
    const sessionMessages = await sessionApi.getSessionMessages(sessionId)

    // 转换消息格式
    const loadedMessages = sessionMessages.map(msg => ({
      id: msg.id,
      type: msg.type as MessageType,
      content: msg.content,
      timestamp: new Date(msg.timestamp).getTime(),
      image_data: msg.image_data,
      image_filename: msg.image_filename,
      image_mime_type: msg.image_mime_type
    }))

    // 如果没有历史消息,添加欢迎消息
    if (loadedMessages.length === 0) {
      messages.value = [createWelcomeMessage()]
    } else {
      messages.value = loadedMessages
    }
  } catch (error: any) {
    message.error(`加载消息失败: ${error.message}`)
    // 即使加载失败也显示欢迎消息
    messages.value = [createWelcomeMessage()]
  }
}

// 创建新会话
const handleCreateSession = async () => {
  try {
    const session = await sessionApi.createSession('新对话')
    sessionStore.createLocalSession(session)
    // 添加欢迎消息
    messages.value = [createWelcomeMessage()]
    message.success('新对话已创建')
  } catch (error: any) {
    message.error(`创建会话失败: ${error.message}`)
  }
}

// 选择会话
const handleSelectSession = async (sessionId: string) => {
  await loadSessionMessages(sessionId)
}

// 删除会话
const handleDeleteSession = async (sessionId: string) => {
  try {
    await sessionApi.deleteSession(sessionId)
    sessionStore.removeSession(sessionId)
    message.success('会话已删除')

    // 如果删除的是当前会话,切换到第一个会话
    if (sessionId === sessionStore.currentSessionId) {
      const sessions = sessionStore.sortedSessions
      if (sessions.length > 0 && sessions[0]) {
        await loadSessionMessages(sessions[0].session_id)
      } else {
        messages.value = []
        await handleCreateSession()
      }
    }
  } catch (error: any) {
    message.error(`删除会话失败: ${error.message}`)
  }
}

const handleSend = async (content: string) => {
  // 添加用户消息
  const userMsg: Message = {
    id: Date.now().toString(),
    content,
    type: MessageType.USER,
    timestamp: Date.now()
  }
  messages.value.push(userMsg)

  // 如果是第一条用户消息，更新会话标题
  const isFirstMessage = messages.value.filter(m => m.type === MessageType.USER).length === 1
  if (isFirstMessage && sessionStore.currentSessionId) {
    try {
      // 用用户的第一句话作为标题，最多20个字符
      const title = content.length > 20 ? content.substring(0, 20) + '...' : content
      await sessionApi.updateSession(sessionStore.currentSessionId, title)
      // 只在本地更新会话标题，不重新加载消息（避免覆盖刚添加的用户消息）
      sessionStore.updateSession(sessionStore.currentSessionId, { title })
    } catch (error) {
      console.error('更新会话标题失败:', error)
    }
  }

  // 创建AI消息占位符
  const aiMsgId = (Date.now() + 1).toString()
  const aiMsg: Message = {
    id: aiMsgId,
    content: '',
    type: MessageType.AI,
    timestamp: Date.now()
  }
  messages.value.push(aiMsg)

  // 调用流式API
  loading.value = true

  try {
    await sendChatMessage(
      content,
      sessionStore.currentSessionId,
      // onChunk: 接收到文本片段
      (text: string) => {
        // 找到AI消息并追加文本
        const aiMessage = messages.value.find(m => m.id === aiMsgId)
        if (aiMessage) {
          aiMessage.content += text
        }
      },
      // onComplete: 完成
      () => {
        loading.value = false
        // 只刷新会话列表元数据（消息计数和时间），不重新加载消息
        refreshSessionList()
      },
      // onError: 错误
      (error: Error) => {
        loading.value = false
        message.error(`错误: ${error.message}`)
        // 移除失败的AI消息
        const index = messages.value.findIndex(m => m.id === aiMsgId)
        if (index !== -1) {
          messages.value.splice(index, 1)
        }
      }
    )
  } catch (error: any) {
    loading.value = false
    message.error(`发送失败: ${error.message}`)
  }
}

// 处理文件上传
const handleFileUpload = async (file: File, question: string) => {
  if (!sessionStore.currentSessionId) {
    message.error('请先创建或选择一个会话')
    return
  }

  // 如果是图片文件，先读取图片数据
  if (file.type.startsWith('image/')) {
    const reader = new FileReader()
    reader.onload = (e) => {
      // 图片数据加载完成后，再创建消息
      const dataUrl = e.target?.result as string
      // 从data URL中提取纯base64数据（移除data:image/xxx;base64,前缀）
      const base64Data = dataUrl.split(',')[1]
      const userMsg: Message = {
        id: Date.now().toString(),
        content: question,
        type: MessageType.USER,
        timestamp: Date.now(),
        image_data: base64Data,
        image_filename: file.name,
        image_mime_type: file.type
      }
      messages.value.push(userMsg)

      // 继续后续处理
      continueFileUpload(file, question)
    }
    reader.readAsDataURL(file)
  } else {
    // 非图片文件，直接创建消息
    const userMsg: Message = {
      id: Date.now().toString(),
      content: question,
      type: MessageType.USER,
      timestamp: Date.now()
    }
    messages.value.push(userMsg)

    // 继续后续处理
    continueFileUpload(file, question)
  }
}

// 文件上传的后续处理
const continueFileUpload = async (file: File, question: string) => {
  const aiMsgId = (Date.now() + 1).toString()
  const aiMsg: Message = {
    id: aiMsgId,
    content: '',
    type: MessageType.AI,
    timestamp: Date.now()
  }
  messages.value.push(aiMsg)

  loading.value = true
  await uploadFileWithMessage(
    file,
    question,
    sessionStore.currentSessionId,
    (text: string) => {
      const msg = messages.value.find(m => m.id === aiMsgId)
      if (msg) msg.content += text
    },
    () => {
      loading.value = false
      message.success('文件处理完成')
    },
    (error: Error) => {
      loading.value = false
      message.error(`文件处理失败: ${error.message}`)
      const index = messages.value.findIndex(m => m.id === aiMsgId)
      if (index !== -1) messages.value.splice(index, 1)
    }
  )
}

// 处理登出
const handleLogout = async () => {
  await userStore.logout()
  message.success('已登出')
  router.push('/login')
}

// 跳转到健康状态页面
const goToHealth = () => {
  router.push('/health')
}

// 组件挂载时加载会话列表
onMounted(() => {
  loadSessions()
})
</script>

<style scoped>
.header-content {
  display: flex;
  align-items: center;
}

.user-info-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #f0f9f4 0%, #e8f5ed 100%);
  border-radius: 20px;
  border: 1px solid #d0e8dc;
  transition: all 0.3s ease;
  cursor: default;
}

.user-info-card:hover {
  background: linear-gradient(135deg, #e8f5ed 0%, #d9f0e3 100%);
  box-shadow: 0 2px 8px rgba(24, 160, 88, 0.15);
}

.user-info-card .username {
  font-size: 14px;
  font-weight: 500;
  color: #2c3e50;
}
</style>
