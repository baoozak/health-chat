<template>
    <div class="message-input">
        <!-- 文件上传按钮 -->
        <FileUploadButton @file-selected="handleFileSelected" />

        <n-input v-model:value="inputValue" type="textarea" placeholder="输入消息...按Shift+Enter换行"
            :autosize="{ minRows: 1, maxRows: 8 }" @keydown.enter="handleEnter" class="message-textarea" />

        <n-button type="primary" :disabled="!inputValue.trim()" @click="handleSend" :loading="props.loading">
            发送
        </n-button>
    </div>

    <!-- 文件上传对话框 -->
    <n-modal v-model:show="showFileDialog" preset="dialog" title="上传文件">
        <template #default>
            <div v-if="selectedFile">
                <p><strong>文件:</strong> {{ selectedFile.name }}</p>
                <p><strong>大小:</strong> {{ (selectedFile.size / 1024).toFixed(2) }} KB</p>

                <!-- 图片预览 -->
                <div v-if="isImageFile(selectedFile)" class="image-preview">
                    <img :src="imagePreviewUrl" alt="预览"
                        style="max-width: 100%; max-height: 300px; border-radius: 8px; margin-top: 12px;" />
                </div>

                <n-input v-model:value="fileQuestion" type="textarea" placeholder="请输入你想问的问题...按Shift+Enter换行"
                    :autosize="{ minRows: 2, maxRows: 6 }" style="margin-top: 12px"
                    @keydown.enter="handleFileQuestionEnter" />
            </div>
        </template>
        <template #action>
            <n-space>
                <n-button @click="showFileDialog = false">取消</n-button>
                <n-button type="primary" @click="handleFileUpload" :disabled="!fileQuestion.trim()">
                    上传并提问
                </n-button>
            </n-space>
        </template>
    </n-modal>
</template>

<script setup lang="ts">
/**
 * 消息输入框组件
 * 支持文本输入、文件上传和发送功能
 */
import { ref } from 'vue'
import { NInput, NButton, NModal, NSpace } from 'naive-ui'
import FileUploadButton from './FileUploadButton.vue'

// 定义props
const props = defineProps<{
    loading?: boolean
}>()

// 定义emits
const emit = defineEmits<{
    send: [content: string]
    uploadFile: [file: File, question: string]
}>()

// 输入框内容
const inputValue = ref('')

// 文件上传相关
const showFileDialog = ref(false)
const selectedFile = ref<File | null>(null)
const fileQuestion = ref('')
const imagePreviewUrl = ref('')

// 判断是否为图片文件
const isImageFile = (file: File) => {
    return file.type.startsWith('image/')
}

// 发送消息
const handleSend = () => {
    const content = inputValue.value.trim()
    if (content) {
        emit('send', content)
        inputValue.value = ''
    }
}

// 处理回车键
const handleEnter = (e: KeyboardEvent) => {
    // Shift + Enter 换行
    if (e.shiftKey) {
        return true
    }
    // 单独 Enter 发送
    e.preventDefault()
    handleSend()
}

// 处理文件选择
const handleFileSelected = (file: File) => {
    selectedFile.value = file
    fileQuestion.value = ''

    // 如果是图片，生成预览
    if (isImageFile(file)) {
        imagePreviewUrl.value = URL.createObjectURL(file)
    } else {
        imagePreviewUrl.value = ''
    }

    showFileDialog.value = true
}

// 处理文件上传对话框的回车键
const handleFileQuestionEnter = (e: KeyboardEvent) => {
    // Shift + Enter 换行
    if (e.shiftKey) {
        return true
    }
    // 单独 Enter 触发上传
    e.preventDefault()
    handleFileUpload()
}

// 处理文件上传
const handleFileUpload = () => {
    if (selectedFile.value && fileQuestion.value.trim()) {
        emit('uploadFile', selectedFile.value, fileQuestion.value.trim())
        showFileDialog.value = false

        // 清理预览URL
        if (imagePreviewUrl.value) {
            URL.revokeObjectURL(imagePreviewUrl.value)
            imagePreviewUrl.value = ''
        }

        selectedFile.value = null
        fileQuestion.value = ''
    }
}
</script>

<style scoped>
.message-input {
    display: flex;
    gap: 12px;
    padding: 18px 20px;
    background: linear-gradient(to top, #f8fffe 0%, #ffffff 100%);
    border-top: 1px solid #e0f2e9;
    position: sticky;
    bottom: 0;
    z-index: 10;
    box-shadow: 0 -2px 8px rgba(24, 160, 88, 0.05);
}

.message-input :deep(.n-input) {
    flex: 1;
}

.message-input :deep(.n-input__border),
.message-input :deep(.n-input__state-border) {
    border-color: #d0e8dc;
    transition: all 0.3s ease;
}

.message-input :deep(.n-input:hover .n-input__border),
.message-input :deep(.n-input:hover .n-input__state-border) {
    border-color: #18a058;
}

.message-input :deep(.n-input--focus .n-input__border),
.message-input :deep(.n-input--focus .n-input__state-border) {
    border-color: #18a058;
    box-shadow: 0 0 0 2px rgba(24, 160, 88, 0.1);
}

.message-textarea :deep(textarea) {
    resize: none;
    font-family: inherit;
    line-height: 1.6;
    border-radius: 12px;
}

.message-input :deep(.n-button) {
    align-self: flex-end;
    border-radius: 10px;
    min-width: 80px;
    font-weight: 500;
    transition: all 0.3s ease;
}

.message-input :deep(.n-button--primary) {
    background: linear-gradient(135deg, #18a058 0%, #36ad6a 100%);
}

.message-input :deep(.n-button--primary:hover) {
    background: linear-gradient(135deg, #0e8a47 0%, #2a9d5d 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(24, 160, 88, 0.3);
}
</style>
