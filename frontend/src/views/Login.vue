<template>
  <div class="login-container">
    <!-- 系统标题和描述 -->
    <div class="login-header">
      <h1 class="system-title">🏥 个人健康管理咨询系统</h1>
      <p class="system-description">您的智能健康助手，为您提供专业的健康建议和管理服务</p>
    </div>

    <n-card class="login-card" :bordered="false">
      <n-tabs v-model:value="activeTab" type="segment" animated>
        <!-- 登录标签页 -->
        <n-tab-pane name="login" tab="登录">
          <n-form ref="loginFormRef" :model="loginForm" :rules="loginRules" size="large">
            <n-form-item path="username" label="用户名">
              <n-input v-model:value="loginForm.username" placeholder="请输入用户名" @keydown.enter="handleLogin" />
            </n-form-item>

            <n-form-item path="password" label="密码">
              <n-input v-model:value="loginForm.password" type="password" show-password-on="click" placeholder="请输入密码"
                @keydown.enter="handleLogin" />
            </n-form-item>

            <n-button type="primary" size="large" block :loading="loading" @click="handleLogin">
              登录
            </n-button>
          </n-form>
        </n-tab-pane>

        <!-- 注册标签页 -->
        <n-tab-pane name="register" tab="注册">
          <n-form ref="registerFormRef" :model="registerForm" :rules="registerRules" size="large">
            <n-form-item path="username" label="用户名">
              <n-input v-model:value="registerForm.username" placeholder="请输入用户名(3-50字符)" />
            </n-form-item>

            <n-form-item path="email" label="邮箱">
              <n-input v-model:value="registerForm.email" placeholder="请输入邮箱" />
            </n-form-item>

            <n-form-item path="password" label="密码">
              <n-input v-model:value="registerForm.password" type="password" show-password-on="click"
                placeholder="请输入密码(至少6位)" />
            </n-form-item>

            <n-form-item path="confirmPassword" label="确认密码">
              <n-input v-model:value="registerForm.confirmPassword" type="password" show-password-on="click"
                placeholder="请再次输入密码" @keydown.enter="handleRegister" />
            </n-form-item>

            <n-button type="primary" size="large" block :loading="loading" @click="handleRegister">
              注册
            </n-button>
          </n-form>
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, type FormInst, type FormRules } from 'naive-ui'
import { useUserStore } from '../store/user'

const router = useRouter()
const message = useMessage()
const userStore = useUserStore()

// 当前激活的标签页
const activeTab = ref('login')

// 加载状态
const loading = ref(false)

// 登录表单
const loginFormRef = ref<FormInst | null>(null)
const loginForm = ref({
  username: '',
  password: ''
})

const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

// 注册表单
const registerFormRef = ref<FormInst | null>(null)
const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为3-50个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value) => {
        return value === registerForm.value.password
      },
      message: '两次输入的密码不一致',
      trigger: 'blur'
    }
  ]
}

// 处理登录
async function handleLogin() {
  try {
    await loginFormRef.value?.validate()
    loading.value = true

    const result = await userStore.login(
      loginForm.value.username,
      loginForm.value.password
    )

    if (result.success) {
      message.success('登录成功!')
      router.push('/')
    } else {
      message.error(result.message || '登录失败')
    }
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    loading.value = false
  }
}

// 处理注册
async function handleRegister() {
  try {
    await registerFormRef.value?.validate()
    loading.value = true

    const result = await userStore.register(
      registerForm.value.username,
      registerForm.value.email,
      registerForm.value.password
    )

    if (result.success) {
      message.success('注册成功!正在跳转...')
      setTimeout(() => {
        router.push('/')
      }, 1000)
    } else {
      message.error(result.message || '注册失败')
    }
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #42b883 0%, #35495e 100%);
  padding: 20px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
  color: white;
}

.system-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 12px 0;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.system-description {
  font-size: 16px;
  margin: 0;
  opacity: 0.95;
  font-weight: 300;
}

.login-card {
  width: 100%;
  max-width: 420px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  border-radius: 16px;
}

.n-form-item {
  margin-bottom: 20px;
}

.n-button {
  margin-top: 10px;
}
</style>
