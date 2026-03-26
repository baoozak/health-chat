<template>
    <div class="session-list">
        <!-- 新建会话按钮 -->
        <div class="new-session-btn">
            <NButton type="primary" block @click="handleCreateSession" :loading="creating">
                <template #icon>
                    <span>➕</span>
                </template>
                新建对话
            </NButton>
        </div>

        <!-- 会话列表 -->
        <div class="sessions">
            <div v-for="session in sessions" :key="session.session_id"
                :class="['session-item', { active: session.session_id === currentSessionId }]"
                @click="handleSelectSession(session.session_id)">
                <div class="session-info">
                    <div class="session-title">{{ session.title }}</div>
                    <div class="session-meta">
                        <span class="message-count">{{ session.message_count }} 条消息</span>
                        <span class="session-time">{{ formatTime(session.updated_at) }}</span>
                    </div>
                </div>
                <div class="session-actions">
                    <NButton text size="small" @click.stop="handleDeleteSession(session.session_id)"
                        :loading="deleting === session.session_id">
                        🗑️
                    </NButton>
                </div>
            </div>

            <!-- 空状态 -->
            <div v-if="sessions.length === 0" class="empty-state">
                <div class="empty-icon">💬</div>
                <div class="empty-text">暂无对话</div>
                <div class="empty-hint">点击上方按钮创建新对话</div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NButton } from 'naive-ui'
import type { Session } from '../store/session'

defineProps<{
    sessions: Session[]
    currentSessionId: string
}>()

const emit = defineEmits<{
    createSession: []
    selectSession: [sessionId: string]
    deleteSession: [sessionId: string]
}>()

const creating = ref(false)
const deleting = ref<string | null>(null)

// 格式化时间
const formatTime = (timestamp: string) => {
    // 将UTC时间转换为本地时间
    const date = new Date(timestamp)
    // 获取本地时间和UTC时间的时差（分钟）
    const timezoneOffset = date.getTimezoneOffset()
    // 调整时区到本地时间
    const localDate = new Date(date.getTime() - timezoneOffset * 60000)

    const now = new Date()
    const diff = now.getTime() - localDate.getTime()

    // 小于1分钟
    if (diff < 60000) {
        return '刚刚'
    }
    // 小于1小时
    if (diff < 3600000) {
        return `${Math.floor(diff / 60000)}分钟前`
    }
    // 小于24小时
    if (diff < 86400000) {
        return `${Math.floor(diff / 3600000)}小时前`
    }
    // 小于7天
    if (diff < 604800000) {
        return `${Math.floor(diff / 86400000)}天前`
    }
    // 其他显示日期
    return localDate.toLocaleDateString('zh-CN')
}

// 创建会话
const handleCreateSession = () => {
    emit('createSession')
}

// 选择会话
const handleSelectSession = (sessionId: string) => {
    emit('selectSession', sessionId)
}

// 删除会话
const handleDeleteSession = (sessionId: string) => {
    emit('deleteSession', sessionId)
}
</script>

<style scoped>
.session-list {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: linear-gradient(to bottom, #f8fffe 0%, #ffffff 100%);
    border-right: 1px solid #e0f2e9;
}

.new-session-btn {
    padding: 0 16px;
    border-bottom: 1px solid #e0f2e9;
    background: linear-gradient(to right, #ffffff 0%, #f8fffe 100%);
    height: 64px;
    display: flex;
    align-items: center;
    box-shadow: 0 2px 8px rgba(24, 160, 88, 0.05);
}

.new-session-btn :deep(.n-button) {
    border-radius: 10px;
    font-weight: 500;
}

.sessions {
    flex: 1;
    overflow-y: auto;
    padding: 12px 16px;
}

.session-item {
    display: flex;
    align-items: center;
    padding: 14px;
    margin-bottom: 8px;
    background-color: white;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    border: 2px solid transparent;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.session-item:hover {
    background-color: #f0f9f4;
    transform: translateX(4px);
    box-shadow: 0 4px 8px rgba(24, 160, 88, 0.1);
}

.session-item.active {
    border-color: #18a058;
    background: linear-gradient(135deg, #f0f9f4 0%, #e8f5ed 100%);
    box-shadow: 0 4px 12px rgba(24, 160, 88, 0.15);
}

.session-info {
    flex: 1;
    min-width: 0;
}

.session-title {
    font-size: 14px;
    font-weight: 600;
    color: #2c3e50;
    margin-bottom: 6px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.session-meta {
    display: flex;
    gap: 10px;
    font-size: 12px;
    color: #999;
}

.message-count {
    color: #18a058;
    font-weight: 500;
}

.session-time {
    color: #999;
}

.session-actions {
    margin-left: 8px;
}

.session-actions .n-button {
    opacity: 0.5;
    transition: all 0.3s ease;
    font-size: 16px;
}

.session-actions .n-button:hover {
    opacity: 1;
    transform: scale(1.15);
    color: #ff4757;
}

/* 空状态 */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #999;
}

.empty-icon {
    font-size: 56px;
    margin-bottom: 20px;
    opacity: 0.6;
}

.empty-text {
    font-size: 16px;
    margin-bottom: 10px;
    color: #5a6c7d;
    font-weight: 500;
}

.empty-hint {
    font-size: 13px;
    color: #999;
}

/* 滚动条样式 */
.sessions::-webkit-scrollbar {
    width: 8px;
}

.sessions::-webkit-scrollbar-track {
    background: #f0f9f4;
    border-radius: 4px;
}

.sessions::-webkit-scrollbar-thumb {
    background-color: #b3d9c4;
    border-radius: 4px;
    transition: background 0.2s;
}

.sessions::-webkit-scrollbar-thumb:hover {
    background-color: #18a058;
}
</style>
