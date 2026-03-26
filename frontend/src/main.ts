/**
 * 应用入口文件
 * 集成NaiveUI组件库并挂载Vue应用
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import naive from 'naive-ui'
import App from './App.vue'
import router from './router'

// 创建Vue应用实例
const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(naive)

// 挂载应用
app.mount('#app')
