<template>
  <n-modal 
    v-model:show="showDisclaimer" 
    :mask-closable="false"
    :closable="false"
    transform-origin="center"
  >
    <n-card 
      style="max-width: 600px; border-radius: 12px;"
      title="健康咨询免责声明"
      :bordered="false"
    >
      <n-space vertical :size="16">
        <p style="font-size: 16px; margin: 0;">
          欢迎使用<strong>个人健康管理咨询系统</strong>！
        </p>
        
        <n-alert type="warning" title="⚠️ 重要提示" :bordered="false">
          <n-ul style="margin: 8px 0; padding-left: 20px;">
            <li>本系统提供的是<strong>一般性健康信息和建议</strong></li>
            <li><strong>不能替代</strong>专业医疗诊断和治疗</li>
            <li><strong>不推荐</strong>具体药物品牌或剂量</li>
            <li>如有身体不适，请<strong>及时就医</strong></li>
            <li>紧急情况请立即拨打<strong style="color: #d03050;">120</strong></li>
          </n-ul>
        </n-alert>

        <n-alert type="info" title="📋 使用须知" :bordered="false">
          <n-ul style="margin: 8px 0; padding-left: 20px;">
            <li>AI助手会基于医学知识提供健康建议</li>
            <li>建议仅供参考，不构成医疗诊断</li>
            <li>请如实描述您的健康状况</li>
            <li>保护您的隐私，不存储敏感医疗信息</li>
          </n-ul>
        </n-alert>

        <n-divider style="margin: 0;" />

        <p style="font-size: 14px; color: #666; margin: 0; text-align: center;">
          使用本系统即表示您已阅读并同意上述声明
        </p>
      </n-space>

      <template #footer>
        <n-space justify="end">
          <n-button 
            type="primary" 
            size="large"
            @click="acceptDisclaimer"
            style="padding: 0 32px;"
          >
            我已阅读并理解
          </n-button>
        </n-space>
      </template>
    </n-card>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NModal, NCard, NAlert, NButton, NSpace, NDivider, NUl } from 'naive-ui'

const showDisclaimer = ref(false)

// 检查用户是否已经同意过免责声明
const DISCLAIMER_KEY = 'health_disclaimer_accepted'

onMounted(() => {
  const accepted = localStorage.getItem(DISCLAIMER_KEY)
  if (!accepted) {
    showDisclaimer.value = true
  }
})

// 用户同意免责声明
const acceptDisclaimer = () => {
  localStorage.setItem(DISCLAIMER_KEY, 'true')
  showDisclaimer.value = false
}
</script>

<style scoped>
:deep(.n-card-header) {
  font-size: 20px;
  font-weight: 600;
  text-align: center;
  padding: 24px 24px 16px;
}

:deep(.n-card__content) {
  padding: 16px 24px;
}

:deep(.n-card__footer) {
  padding: 16px 24px 24px;
}

:deep(.n-alert) {
  border-radius: 8px;
}

:deep(.n-alert__content) {
  font-size: 14px;
}

li {
  margin: 6px 0;
  line-height: 1.6;
}
</style>
