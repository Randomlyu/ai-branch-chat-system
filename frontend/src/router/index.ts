import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '@/views/ChatView.vue'
import LoginView from '@/views/LoginView.vue'
import ChangePasswordView from '@/views/ChangePasswordView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'chat',
      component: ChatView,
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false }
    },
    {
      path: '/change-password',
      name: 'change-password',
      component: ChangePasswordView,
      meta: { requiresAuth: true }
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // 检查路由是否需要认证
  if (to.meta.requiresAuth) {
    if (authStore.isLoggedIn) {
      // 检查是否需要修改密码
      if (authStore.needPasswordChange && to.name !== 'change-password') {
        // 强制跳转到修改密码页面
        next('/change-password')
      } else if (!authStore.needPasswordChange && to.name === 'change-password') {
        // 已修改过密码的用户访问修改密码页，重定向到首页
        next('/')
      } else {
        next()
      }
    } else {
      // 未登录，重定向到登录页
      next('/login')
    }
  } else {
    // 不需要认证的路由
    if (to.path === '/login' && authStore.isLoggedIn) {
      // 已登录的用户访问登录页，重定向到首页
      next('/')
    } else {
      next()
    }
  }
})

export default router