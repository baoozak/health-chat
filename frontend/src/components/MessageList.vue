<template>
    <div class="message-list" ref="messageListRef">
        <div v-for="message in messages" :key="message.id" :class="['message-item', message.type]">
            <div class="message-bubble">
                <div class="message-content">
                    <!-- 显示图片（如果存在） -->
                    <div v-if="message.image_data && message.image_mime_type" class="message-image">
                        <img :src="`data:${message.image_mime_type};base64,${message.image_data}`"
                            :alt="message.image_filename"
                            @click="openImageModal(message.image_data, message.image_mime_type)"
                            style="max-width: 200px; max-height: 150px; cursor: pointer; border-radius: 8px; margin-bottom: 8px;" />
                    </div>
                    <MarkdownRenderer v-if="message.type === 'ai'" :content="message.content" />
                    <div v-else>{{ message.content }}</div>
                </div>
                <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            </div>
        </div>

        <!-- 图片预览模态框 -->
        <div v-if="showImageModal" class="image-modal" @click="closeImageModal">
            <div class="image-modal-content" @click.stop>
                <img :src="modalImageSrc" alt="预览图片" style="max-width: 90%; max-height: 90vh;" />
                <button class="close-modal" @click="closeImageModal">&times;</button>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { Message } from '../types'
import MarkdownRenderer from './MarkdownRenderer.vue'

const props = defineProps<{
    messages: Message[]
}>()

// 图片预览相关
const showImageModal = ref(false)
const modalImageSrc = ref('')

const openImageModal = (imageData: string, mimeType: string) => {
    modalImageSrc.value = `data:${mimeType};base64,${imageData}`
    showImageModal.value = true
}

const closeImageModal = () => {
    showImageModal.value = false
    modalImageSrc.value = ''
}

const formatTime = (timestamp: number): string => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
    })
}

const messageListRef = ref<HTMLElement | null>(null)

watch(() => props.messages.length, async () => {
    await nextTick()
    if (messageListRef.value) {
        messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
})
</script>

<style scoped>
.message-list {
    width: 100%;
    height: 100%;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    background: linear-gradient(to bottom, #f8fffe 0%, #ffffff 100%);
}

.message-item {
    display: flex;
    width: 100%;
    animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(15px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.message-item.user {
    justify-content: flex-end;
}

.message-item.ai {
    justify-content: flex-start;
}

.message-bubble {
    max-width: 70%;
    padding: 14px 18px;
    border-radius: 16px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    transition: all 0.2s ease;
}

.message-bubble:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.message-item.user .message-bubble {
    background: linear-gradient(135deg, #18a058 0%, #36ad6a 100%);
    color: white;
}

.message-item.ai .message-bubble {
    background: #f0f9f4;
    color: #2c3e50;
    border: 1px solid #e0f2e9;
}

.message-content {
    font-size: 14px;
    line-height: 1.7;
    word-wrap: break-word;
    white-space: pre-wrap;
}

.message-time {
    font-size: 11px;
    margin-top: 8px;
    opacity: 0.65;
    font-weight: 500;
}

.message-list::-webkit-scrollbar {
    width: 8px;
}

.message-list::-webkit-scrollbar-track {
    background: #f0f9f4;
    border-radius: 4px;
}

.message-list::-webkit-scrollbar-thumb {
    background: #b3d9c4;
    border-radius: 4px;
    transition: background 0.2s;
}

.message-list::-webkit-scrollbar-thumb:hover {
    background: #18a058;
}
</style>

<style scoped>
/* 图片相关样式 */
.message-image {
    margin-bottom: 8px;
}

/* 图片预览模态框样式 */
.image-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.8);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.image-modal-content {
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;
}

.close-modal {
    position: absolute;
    top: 20px;
    right: 40px;
    font-size: 40px;
    color: white;
    background: none;
    border: none;
    cursor: pointer;
    z-index: 1001;
}

.close-modal:hover {
    color: #ccc;
}
</style>