<template>
  <div class="login-container">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="bg-circle-1"></div>
      <div class="bg-circle-2"></div>
      <div class="bg-circle-3"></div>
    </div>
    
    <div class="login-card">
      <!-- 头部Logo区域 -->
      <div class="login-header">
        <div class="logo-container">
          <div class="logo-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <h1>思维森林</h1>
          <p class="subtitle">AI 分支对话系统</p>
        </div>
        <p class="welcome-text">欢迎回来，请登录您的账户</p>
      </div>
      
      <!-- 登录表单 -->
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <div class="input-with-icon">
            <svg class="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20 21V19C20 16.7909 18.2091 15 16 15H8C5.79086 15 4 16.7909 4 19V21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M12 11C14.2091 11 16 9.20914 16 7C16 4.79086 14.2091 3 12 3C9.79086 3 8 4.79086 8 7C8 9.20914 9.79086 11 12 11Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <input
              v-model="form.username"
              type="text"
              id="username"
              :disabled="isLoading"
              placeholder="请输入用户名"
              required
              autofocus
            />
          </div>
        </div>
        
        <div class="form-group">
          <div class="label-row">
            <label for="password">密码</label>
            <span class="forgot-password" @click="handleForgotPassword">忘记密码？</span>
          </div>
          <div class="input-with-icon">
            <svg class="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 15C13.6569 15 15 13.6569 15 12C15 10.3431 13.6569 9 12 9C10.3431 9 9 10.3431 9 12C9 13.6569 10.3431 15 12 15Z" stroke="currentColor" stroke-width="2"/>
              <path d="M19 12C19 12.919 18.8189 13.8295 18.4672 14.6788C18.1154 15.5281 17.5998 16.2997 16.9497 16.9497C16.2997 17.5998 15.5281 18.1154 14.6788 18.4672C13.8295 18.8189 12.919 19 12 19C11.081 19 10.1705 18.8189 9.32122 18.4672C8.47194 18.1154 7.70026 17.5998 7.05025 16.9497C6.40024 16.2997 5.88463 15.5281 5.53284 14.6788C5.18106 13.8295 5 12.919 5 12C5 10.1435 5.7375 8.36301 7.05025 7.05025C8.36301 5.7375 10.1435 5 12 5C13.8565 5 15.637 5.7375 16.9497 7.05025C18.2625 8.36301 19 10.1435 19 12Z" stroke="currentColor" stroke-width="2"/>
            </svg>
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              id="password"
              :disabled="isLoading"
              placeholder="请输入密码"
              required
            />
            <!-- 显示/隐藏密码按钮 -->
            <button
              type="button"
              class="password-toggle"
              @click="togglePasswordVisibility"
              :title="showPassword ? '隐藏密码' : '显示密码'"
            >
              <svg v-if="showPassword" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M1 12C1 12 5 4 12 4C19 4 23 12 23 12C23 12 19 20 12 20C5 20 1 12 1 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 15C13.6569 15 15 13.6569 15 12C15 10.3431 13.6569 9 12 9C10.3431 9 9 10.3431 9 12C9 13.6569 10.3431 15 12 15Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9.9 4.24C10.5883 4.07888 11.2931 3.99834 12 4C19 4 23 12 23 12C22.393 13.1356 21.6691 14.2047 20.84 15.19M14.12 14.12C13.8454 14.4147 13.5141 14.6512 13.1462 14.8151C12.7782 14.9791 12.3809 15.0673 11.9781 15.0744C11.5753 15.0815 11.1752 15.0074 10.8016 14.8565C10.4281 14.7056 10.0887 14.481 9.80385 14.1962C9.51897 13.9113 9.29439 13.5719 9.14351 13.1984C8.99262 12.8248 8.91853 12.4247 8.92563 12.0219C8.93274 11.6191 9.02091 11.2218 9.18488 10.8538C9.34884 10.4859 9.58525 10.1546 9.88 9.88M17.94 17.94C16.2306 19.243 14.1491 19.9649 12 20C5 20 1 12 1 12C2.24389 9.6819 3.96914 7.65661 6.06 6.06L17.94 17.94Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M1 1L23 23" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </div>
        
        <!-- 错误信息 -->
        <div v-if="error" class="error-message">
          <svg class="error-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 8V12M12 16H12.01M22 12C22 17.5228 17.5228 22 12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>{{ error }}</span>
        </div>
        
        <!-- 登录按钮 -->
        <button type="submit" :disabled="isLoading" class="login-button">
          <svg v-if="isLoading" class="loading-spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" stroke-dasharray="60" stroke-dashoffset="60">
              <animate attributeName="stroke-dashoffset" dur="1.5s" repeatCount="indefinite" values="60;0;60" keyTimes="0;0.5;1" calcMode="spline" keySplines="0.4 0 0.2 1;0.4 0 0.2 1"/>
            </circle>
          </svg>
          <span v-if="isLoading">登录中...</span>
          <span v-else>登录</span>
        </button>
        
        <!-- 使用提示 -->
        <div class="login-footer">
          <div class="usage-tip">
            <svg class="tip-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 16V12M12 8H12.01M22 12C22 17.5228 17.5228 22 12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>初始用户: user1 到 user15，密码: 123456</span>
          </div>
          <div class="usage-tip">
            <svg class="tip-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 15V12M12 9H12.01M7.8 21H16.2C17.8802 21 18.7202 21 19.362 20.673C19.9265 20.3854 20.3854 19.9265 20.673 19.362C21 18.7202 21 17.8802 21 16.2V7.8C21 6.11984 21 5.27976 20.673 4.63803C20.3854 4.07354 19.9265 3.6146 19.362 3.32698C18.7202 3 17.8802 3 16.2 3H7.8C6.11984 3 5.27976 3 4.63803 3.32698C4.07354 3.6146 3.6146 4.07354 3.32698 4.63803C3 5.27976 3 6.11984 3 7.8V16.2C3 17.8802 3 18.7202 3.32698 19.362C3.6146 19.9265 4.07354 20.3854 4.63803 20.673C5.27976 21 6.11984 21 7.8 21Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>首次登录后需要修改密码</span>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isLoading = ref(false)
const error = ref('')
const showPassword = ref(false) // 控制密码显示状态

const form = reactive({
  username: '',
  password: ''
})

onMounted(() => {
  // 如果已经登录，跳转到主页面
  if (authStore.isLoggedIn) {
    router.push('/')
  }
})

// 切换密码显示状态
const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value
}

// 忘记密码处理
const handleForgotPassword = () => {
  // 这里可以实现忘记密码的逻辑
  error.value = '请联系管理员重置密码'
}

const handleLogin = async () => {
  if (!form.username || !form.password) {
    error.value = '请输入用户名和密码'
    return
  }
  
  isLoading.value = true
  error.value = ''
  
  try {
    const result = await authStore.login(form.username, form.password)
    
    if (result.success) {
      if (result.needPasswordChange) {
        // 首次登录需要修改密码
        router.push('/change-password')
      } else {
        // 登录成功，跳转到主页面
        router.push('/')
      }
    } else {
      error.value = result.error || '登录失败'
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '登录失败'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  position: relative;
  overflow: hidden;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 0;
}

.bg-circle-1,
.bg-circle-2,
.bg-circle-3 {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

.bg-circle-1 {
  width: 300px;
  height: 300px;
  top: -150px;
  right: -100px;
}

.bg-circle-2 {
  width: 200px;
  height: 200px;
  bottom: -100px;
  left: -50px;
  background: rgba(255, 255, 255, 0.05);
}

.bg-circle-3 {
  width: 150px;
  height: 150px;
  top: 50%;
  right: 10%;
  background: rgba(255, 255, 255, 0.08);
}

.login-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  padding: 40px;
  width: 100%;
  max-width: 420px;
  position: relative;
  z-index: 1;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: transform 0.3s ease;
}

.login-card:hover {
  transform: translateY(-5px);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-container {
  margin-bottom: 16px;
}

.logo-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  margin-bottom: 16px;
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
}

.login-header h1 {
  color: #2d3748;
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  color: #718096;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.welcome-text {
  color: #a0aec0;
  font-size: 15px;
  margin-top: 8px;
}

/* 表单样式 */
.login-form {
  width: 100%;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  color: #4a5568;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.forgot-password {
  color: #667eea;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.2s;
}

.forgot-password:hover {
  color: #764ba2;
  text-decoration: underline;
}

.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 16px;
  color: #a0aec0;
  pointer-events: none;
}

.input-with-icon input {
  width: 100%;
  padding: 16px 16px 16px 48px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 15px;
  transition: all 0.3s;
  background: white;
  box-sizing: border-box;
  height: 52px;
}

.input-with-icon input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.input-with-icon input:disabled {
  background-color: #f7fafc;
  cursor: not-allowed;
  border-color: #e2e8f0;
}

.password-toggle {
  position: absolute;
  right: 16px;
  background: none;
  border: none;
  color: #a0aec0;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
  outline: none;
}

.password-toggle:hover {
  color: #667eea;
}

/* 错误信息样式 */
.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: #fff5f5;
  color: #c53030;
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 14px;
  margin-bottom: 20px;
  border: 1px solid #fed7d7;
}

.error-icon {
  flex-shrink: 0;
  color: #c53030;
}

/* 登录按钮样式 */
.login-button {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
  height: 52px;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 25px rgba(102, 126, 234, 0.4);
}

.login-button:active:not(:disabled) {
  transform: translateY(0);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.loading-spinner {
  animation: spin 1.5s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 底部提示 */
.login-footer {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
}

.usage-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #718096;
  font-size: 13px;
  margin-bottom: 8px;
}

.usage-tip:last-child {
  margin-bottom: 0;
}

.tip-icon {
  flex-shrink: 0;
  color: #a0aec0;
}

/* 响应式调整 */
@media (max-width: 480px) {
  .login-container {
    padding: 16px;
  }
  
  .login-card {
    padding: 32px 24px;
  }
  
  .login-header h1 {
    font-size: 24px;
  }
  
  .input-with-icon input {
    padding: 14px 16px 14px 44px;
    height: 48px;
  }
  
  .login-button {
    padding: 14px;
    height: 48px;
  }
}
</style>