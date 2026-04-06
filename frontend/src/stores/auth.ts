import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/chat'
import { clearAllUIState } from '@/utils/state-persistence'

export interface User {
  id: number
  username: string
  email?: string
  need_password_change: boolean
  created_at: string
}

export const useAuthStore = defineStore('auth', () => {
  // ========== 状态 ==========
  const accessToken = ref<string>('')
  const refreshToken = ref<string>('')
  const currentUser = ref<User | null>(null)
  const isAuthenticated = ref<boolean>(false)
  const isLoading = ref<boolean>(false)
  const error = ref<string>('')
  const needPasswordChange = ref<boolean>(false)

  // ========== 计算属性 ==========
  const isLoggedIn = computed(() => isAuthenticated.value && currentUser.value !== null)
  const username = computed(() => currentUser.value?.username || '')
  const userId = computed(() => currentUser.value?.id || 0)

  // ========== 从localStorage初始化 ==========
  const initFromStorage = () => {
    const storedAccessToken = localStorage.getItem('access_token')
    const storedRefreshToken = localStorage.getItem('refresh_token')
    const storedUser = localStorage.getItem('user')
    
    if (storedAccessToken) {
      accessToken.value = storedAccessToken
    }
    
    if (storedRefreshToken) {
      refreshToken.value = storedRefreshToken
    }
    
    if (storedUser) {
      try {
        currentUser.value = JSON.parse(storedUser)
        isAuthenticated.value = true
        needPasswordChange.value = currentUser.value?.need_password_change || false
        
        // 如果存在令牌，自动获取用户信息
        if (storedAccessToken) {
          fetchCurrentUser()
        }
      } catch (e) {
        console.error('解析用户信息失败:', e)
        clearLocalStorage()
      }
    }
  }

  // ========== 保存到localStorage ==========
  const saveToStorage = () => {
    if (accessToken.value) {
      localStorage.setItem('access_token', accessToken.value)
    }
    
    if (refreshToken.value) {
      localStorage.setItem('refresh_token', refreshToken.value)
    }
    
    if (currentUser.value) {
      localStorage.setItem('user', JSON.stringify(currentUser.value))
    }
  }

  // ========== 清除localStorage ==========
  const clearLocalStorage = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  // ========== 动作 ==========
  /**
   * 用户登录
   */
  const login = async (username: string, password: string) => {
    try {
      isLoading.value = true
      error.value = ''
      
      const response = await api.login({ username, password })
      const { data } = response
      
      // 保存令牌
      accessToken.value = data.access_token
      refreshToken.value = data.refresh_token
      needPasswordChange.value = data.need_password_change
      
      // 获取用户信息
      await fetchCurrentUser()
      
      // 保存到localStorage
      saveToStorage()
      
      return { success: true, needPasswordChange: data.need_password_change }
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : '登录失败'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 获取当前用户信息
   */
  const fetchCurrentUser = async () => {
    try {
      if (!accessToken.value) {
        throw new Error('未找到访问令牌')
      }
      
      const response = await api.getCurrentUser()
      currentUser.value = response.data
      isAuthenticated.value = true
      needPasswordChange.value = currentUser.value?.need_password_change || false
      
      // 更新localStorage
      saveToStorage()
      
      return currentUser.value
    } catch (err: unknown) {
      console.error('获取用户信息失败:', err)
      logout()
      throw err
    }
  }

  /**
   * 刷新访问令牌
   */
  const refreshAccessToken = async () => {
    try {
      if (!refreshToken.value) {
        throw new Error('未找到刷新令牌')
      }
      
      const response = await api.refreshToken({ refresh_token: refreshToken.value })
      const { data } = response
      
      // 更新访问令牌
      accessToken.value = data.access_token
      
      // 保存到localStorage
      saveToStorage()
      
      return { success: true }
    } catch (err: unknown) {
      console.error('刷新令牌失败:', err)
      logout()
      return { success: false, error: err instanceof Error ? err.message : '刷新令牌失败' }
    }
  }

  /**
   * 修改密码
   */
  const changePassword = async (currentPassword: string, newPassword: string) => {
    try {
      isLoading.value = true
      error.value = ''
      
      await api.changePassword({
        current_password: currentPassword,
        new_password: newPassword
      })
      
      // 密码修改成功后，重置需要修改密码标志
      needPasswordChange.value = false
      if (currentUser.value) {
        currentUser.value.need_password_change = false
        saveToStorage()
      }
      
      return { success: true }
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : '修改密码失败'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 用户登出
   */
  const logout = () => {
  // 清除所有UI状态
  clearAllUIState()
  // 清除状态
  accessToken.value = ''
  refreshToken.value = ''
  currentUser.value = null
  isAuthenticated.value = false
  needPasswordChange.value = false
  error.value = ''
  
  // 清除localStorage
  clearLocalStorage()
  
  // 延迟重定向到登录页，确保状态已清除
  setTimeout(() => {
    window.location.href = '/login'
  }, 100)
}


  /**
   * 检查是否需要修改密码
   */
  const checkPasswordChange = (): boolean => {
    return needPasswordChange.value
  }

  // ========== 初始化 ==========
  // 应用启动时从localStorage恢复状态
  initFromStorage()

  return {
    // 状态
    accessToken,
    refreshToken,  // 状态变量
    currentUser,
    isAuthenticated,
    isLoading,
    error,
    needPasswordChange,
    
    // 计算属性
    isLoggedIn,
    username,
    userId,
    
    // 动作
    login,
    fetchCurrentUser,
    refreshAccessToken,  // 修改后的函数名
    changePassword,
    logout,
    checkPasswordChange
  }
})

function showToast(arg0: string) {
  throw new Error('Function not implemented.')
}
