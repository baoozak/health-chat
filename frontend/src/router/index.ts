/**
 * 路由配置
 * 配置应用的路由和导航守卫
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../store/user'
import ChatView from '../views/ChatView.vue'
import Login from '../views/Login.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: Login,
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      name: 'Chat',
      component: ChatView,
      meta: { requiresAuth: true }
    },
    {
      path: '/health',
      name: 'Health',
      component: () => import('../views/HealthDashboard.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

// 导航守卫 - 检查登录状态
router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()
  const requiresAuth = to.meta.requiresAuth
  
  if (requiresAuth && !userStore.isLoggedIn) {
    // 需要登录但未登录,跳转到登录页
    next({ name: 'Login' })
  } else if (to.name === 'Login' && userStore.isLoggedIn) {
    // 已登录访问登录页,跳转到聊天页
    next({ name: 'Chat' })
  } else {
    next()
  }
})

export default router
