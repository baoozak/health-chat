<template>
  <div class="file-upload-wrapper">
    <input ref="fileInputRef" type="file" accept=".txt,.docx,.jpg,.jpeg,.png,.pdf" style="display: none"
      @change="handleFileSelect" />
    <NTooltip>
      <template #trigger>
        <NButton circle @click="triggerFileInput" :loading="uploading">
          <template #icon>
            <span style="font-size: 18px">📎</span>
          </template>
        </NButton>
      </template>
      上传文件 (TXT, Word, 图片, PDF)
    </NTooltip>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NButton, NTooltip, useMessage } from 'naive-ui'

const fileInputRef = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const message = useMessage()

const emit = defineEmits<{
  fileSelected: [file: File]
}>()

// 触发文件选择
const triggerFileInput = () => {
  if (fileInputRef.value) {
    fileInputRef.value.click()
  }
}

// 处理文件选择
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (!file) return

  // 验证文件类型
  const allowedTypes = ['.txt', '.docx', '.jpg', '.jpeg', '.png', '.pdf']
  const fileExt = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
  if (!allowedTypes.includes(fileExt)) {
    message.error(`不支持的文件格式: ${fileExt}，支持 TXT, Word, JPG, PNG, PDF`)
    return
  }

  // 验证文件大小 (图片/PDF最大20MB, 文本最大10MB)
  const isImage = ['.jpg', '.jpeg', '.png', '.pdf'].includes(fileExt)
  const maxSize = isImage ? 20 * 1024 * 1024 : 10 * 1024 * 1024
  if (file.size > maxSize) {
    message.error(`文件过大: ${(file.size / 1024 / 1024).toFixed(2)}MB，最大支持${isImage ? '20' : '10'}MB`)
    return
  }

  // 发送文件选择事件
  emit('fileSelected', file)

  // 清空input，允许重复选择同一文件
  if (target) {
    target.value = ''
  }
}
</script>

<style scoped>
.file-upload-wrapper {
  display: inline-block;
}
</style>
