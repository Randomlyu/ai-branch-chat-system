<template>
  <div class="change-password-overlay" v-if="visible">
    <div class="change-password-modal">
      <!-- 模态框头部 -->
      <div class="modal-header">
        <div class="header-content">
          <div class="modal-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 15V12M12 9H12.01M17.8 21H6.2C5.0799 21 4.51984 21 4.09202 20.782C3.71569 20.5903 3.40973 20.2843 3.21799 19.908C3 19.4802 3 18.9201 3 17.8V6.2C3 5.0799 3 4.51984 3.21799 4.09202C3.40973 3.71569 3.71569 3.40973 4.09202 3.21799C4.51984 3 5.0799 3 6.2 3H17.8C18.9201 3 19.4802 3 19.908 3.21799C20.2843 3.40973 20.5903 3.71569 20.782 4.09202C21 4.51984 21 5.0799 21 6.2V17.8C21 18.9201 21 19.4802 20.782 19.908C20.5903 20.2843 20.2843 20.5903 19.908 20.782C19.4802 21 18.9201 21 17.8 21Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div>
            <h2>修改密码</h2>
            <p class="modal-subtitle">设置新密码以保护您的账户</p>
          </div>
        </div>
        <button v-if="!isRequired" @click="close" class="close-button" aria-label="关闭" title="关闭">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
      
      <!-- 首次登录提示 -->
      <div v-if="isRequired" class="required-notice">
        <svg class="notice-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 15V12M12 9H12.01M21 12C21 13.1819 20.7672 14.3522 20.3149 15.4442C19.8626 16.5361 19.1997 17.5282 18.364 18.364C17.5282 19.1997 16.5361 19.8626 15.4442 20.3149C14.3522 20.7672 13.1819 21 12 21C10.8181 21 9.64778 20.7672 8.55585 20.3149C7.46392 19.8626 6.47177 19.1997 5.63604 18.364C4.80031 17.5282 4.13738 16.5361 3.68508 15.4442C3.23279 14.3522 3 13.1819 3 12C3 9.61305 3.94821 7.32387 5.63604 5.63604C7.32387 3.94821 9.61305 3 12 3C14.3869 3 16.6761 3.94821 18.364 5.63604C20.0518 7.32387 21 9.61305 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <div class="notice-content">
          <h3>首次登录，请设置新密码</h3>
          <p>为了您的账户安全，请设置一个强密码并妥善保管</p>
        </div>
      </div>
      
      <!-- 密码修改表单 -->
      <form @submit.prevent="handleChangePassword" class="change-password-form">
        <!-- 当前密码（非强制修改时显示） -->
        <div v-if="!isRequired" class="form-group">
          <label for="currentPassword">当前密码</label>
          <div class="input-with-icon">
            <svg class="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 15C13.6569 15 15 13.6569 15 12C15 10.3431 13.6569 9 12 9C10.3431 9 9 10.3431 9 12C9 13.6569 10.3431 15 12 15Z" stroke="currentColor" stroke-width="2"/>
              <path d="M19 12C19 12.919 18.8189 13.8295 18.4672 14.6788C18.1154 15.5281 17.5998 16.2997 16.9497 16.9497C16.2997 17.5998 15.5281 18.1154 14.6788 18.4672C13.8295 18.8189 12.919 19 12 19C11.081 19 10.1705 18.8189 9.32122 18.4672C8.47194 18.1154 7.70026 17.5998 7.05025 16.9497C6.40024 16.2997 5.88463 15.5281 5.53284 14.6788C5.18106 13.8295 5 12.919 5 12C5 10.1435 5.7375 8.36301 7.05025 7.05025C8.36301 5.7375 10.1435 5 12 5C13.8565 5 15.637 5.7375 16.9497 7.05025C18.2625 8.36301 19 10.1435 19 12Z" stroke="currentColor" stroke-width="2"/>
            </svg>
            <input
              v-model="form.currentPassword"
              :type="showCurrentPassword ? 'text' : 'password'"
              id="currentPassword"
              :disabled="isLoading"
              placeholder="输入当前密码"
              required
            />
            <button
              type="button"
              class="password-toggle"
              @click="togglePasswordVisibility('current')"
              :title="showCurrentPassword ? '隐藏密码' : '显示密码'"
            >
              <svg v-if="showCurrentPassword" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
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
        
        <!-- 新密码 -->
        <div class="form-group">
          <label for="newPassword">新密码</label>
          <div class="input-with-icon">
            <svg class="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M15 7C16.1046 7 17 7.89543 17 9C17 10.1046 16.1046 11 15 11C13.8954 11 13 10.1046 13 9C13 7.89543 13.8954 7 15 7Z" stroke="currentColor" stroke-width="2"/>
              <path d="M20.5 15C20.5 15 19 15.5 18 15.5C16.276 15.5 13.5 15.5 13.5 20.5C13.5 20.5 13.5 22 12 22C10.5 22 10.5 20.5 10.5 20.5C10.5 15.5 7.724 15.5 6 15.5C5 15.5 3.5 15 3.5 15C3.5 10 7.686 5 12 5C16.314 5 20.5 10 20.5 15Z" stroke="currentColor" stroke-width="2"/>
            </svg>
            <input
              v-model="form.newPassword"
              :type="showNewPassword ? 'text' : 'password'"
              id="newPassword"
              :disabled="isLoading"
              placeholder="输入新密码（至少6位）"
              required
            />
            <button
              type="button"
              class="password-toggle"
              @click="togglePasswordVisibility('new')"
              :title="showNewPassword ? '隐藏密码' : '显示密码'"
            >
              <svg v-if="showNewPassword" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
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
        
        <!-- 确认新密码 -->
        <div class="form-group">
          <label for="confirmPassword">确认新密码</label>
          <div class="input-with-icon">
            <svg class="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 12L11 14L15 10M12 3C13.1819 3 14.3522 3.23279 15.4442 3.68508C16.5361 4.13738 17.5282 4.80031 18.364 5.63604C19.1997 6.47177 19.8626 7.46392 20.3149 8.55585C20.7672 9.64778 21 10.8181 21 12C21 13.1819 20.7672 14.3522 20.3149 15.4442C19.8626 16.5361 19.1997 17.5282 18.364 18.364C17.5282 19.1997 16.5361 19.8626 15.4442 20.3149C14.3522 20.7672 13.1819 21 12 21C10.8181 21 9.64778 20.7672 8.55585 20.3149C7.46392 19.8626 6.47177 19.1997 5.63604 18.364C4.80031 17.5282 4.13738 16.5361 3.68508 15.4442C3.23279 14.3522 3 13.1819 3 12C3 9.61305 3.94821 7.32387 5.63604 5.63604C7.32387 3.94821 9.61305 3 12 3Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <input
              v-model="form.confirmPassword"
              :type="showConfirmPassword ? 'text' : 'password'"
              id="confirmPassword"
              :disabled="isLoading"
              placeholder="再次输入新密码"
              required
            />
            <button
              type="button"
              class="password-toggle"
              @click="togglePasswordVisibility('confirm')"
              :title="showConfirmPassword ? '隐藏密码' : '显示密码'"
            >
              <svg v-if="showConfirmPassword" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
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
        <div v-if="passwordError" class="error-message">
          <svg class="error-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 8V12M12 16H12.01M22 12C22 17.5228 17.5228 22 12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>{{ passwordError }}</span>
        </div>
        
        <!-- 成功信息 -->
        <div v-if="successMessage" class="success-message">
          <svg class="success-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 12L11 14L15 10M12 3C13.1819 3 14.3522 3.23279 15.4442 3.68508C16.5361 4.13738 17.5282 4.80031 18.364 5.63604C19.1997 6.47177 19.8626 7.46392 20.3149 8.55585C20.7672 9.64778 21 10.8181 21 12C21 13.1819 20.7672 14.3522 20.3149 15.4442C19.8626 16.5361 19.1997 17.5282 18.364 18.364C17.5282 19.1997 16.5361 19.8626 15.4442 20.3149C14.3522 20.7672 13.1819 21 12 21C10.8181 21 9.64778 20.7672 8.55585 20.3149C7.46392 19.8626 6.47177 19.1997 5.63604 18.364C4.80031 17.5282 4.13738 16.5361 3.68508 15.4442C3.23279 14.3522 3 13.1819 3 12C3 9.61305 3.94821 7.32387 5.63604 5.63604C7.32387 3.94821 9.61305 3 12 3Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>{{ successMessage }}</span>
        </div>
        
        <!-- 表单操作按钮 -->
        <div class="form-actions">
          <button v-if="!isRequired" type="button" @click="close" :disabled="isLoading" class="cancel-button">
            取消
          </button>
          <button type="submit" :disabled="isLoading" class="submit-button">
            <svg v-if="isLoading" class="loading-spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" stroke-dasharray="60" stroke-dashoffset="60">
                <animate attributeName="stroke-dashoffset" dur="1.5s" repeatCount="indefinite" values="60;0;60" keyTimes="0;0.5;1" calcMode="spline" keySplines="0.4 0 0.2 1;0.4 0 0.2 1"/>
              </circle>
            </svg>
            <span v-if="isLoading">修改中...</span>
            <span v-else>修改密码</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'

interface Props {
  visible?: boolean
  isRequired?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  isRequired: false
})

const emit = defineEmits<{
  close: []
  success: []
}>()

const authStore = useAuthStore()
const isLoading = ref(false)
const passwordError = ref('')
const successMessage = ref('')

// 密码显示状态
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

const form = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 切换密码显示状态
const togglePasswordVisibility = (type: 'current' | 'new' | 'confirm') => {
  if (type === 'current') {
    showCurrentPassword.value = !showCurrentPassword.value
  } else if (type === 'new') {
    showNewPassword.value = !showNewPassword.value
  } else {
    showConfirmPassword.value = !showConfirmPassword.value
  }
}

// 验证密码
const validatePassword = () => {
  if (!props.isRequired && !form.currentPassword) {
    passwordError.value = '请输入当前密码'
    return false
  }
  
  if (form.newPassword.length < 6) {
    passwordError.value = '新密码长度不能少于6位'
    return false
  }
  
  if (form.newPassword !== form.confirmPassword) {
    passwordError.value = '两次输入的新密码不一致'
    return false
  }
  
  // 在强制修改密码的情况下，新密码不能是初始密码
  if (props.isRequired && form.newPassword === "123456") {
    passwordError.value = '新密码不能与初始密码相同'
    return false
  }
  
  // 在非强制修改的情况下，新密码不能与当前密码相同
  if (!props.isRequired && form.currentPassword === form.newPassword) {
    passwordError.value = '新密码不能与当前密码相同'
    return false
  }
  
  passwordError.value = ''
  return true
}

// 处理修改密码
const handleChangePassword = async () => {
  if (!validatePassword()) {
    return
  }
  
  isLoading.value = true
  passwordError.value = ''
  successMessage.value = ''
  
  // 如果是首次登录强制修改密码，当前密码自动设为初始密码"123456"
  const currentPasswordToSend = props.isRequired ? "123456" : form.currentPassword
  
  console.log("修改密码请求数据:", {
    currentPassword: currentPasswordToSend,
    newPassword: form.newPassword,
    confirmPassword: form.confirmPassword
  })
  
  try {
    const result = await authStore.changePassword(currentPasswordToSend, form.newPassword)
    
    if (result.success) {
      successMessage.value = '密码修改成功！'
      
      // 清除表单
      form.currentPassword = ''
      form.newPassword = ''
      form.confirmPassword = ''
      
      // 重置密码显示状态
      showCurrentPassword.value = false
      showNewPassword.value = false
      showConfirmPassword.value = false
      
      // 如果是强制修改，自动关闭
      if (props.isRequired) {
        setTimeout(() => {
          emit('success')
        }, 1500)
      } else {
        // 非强制修改，保持模态框打开以便用户看到成功消息
        setTimeout(() => {
          successMessage.value = ''
        }, 3000)
      }
    } else {
      passwordError.value = result.error || '修改密码失败'
    }
  } catch (err) {
    console.error("修改密码错误:", err)
    passwordError.value = err instanceof Error ? err.message : '修改密码失败'
  } finally {
    isLoading.value = false
  }
}

// 关闭模态框
const close = () => {
  if (!isLoading.value) {
    // 清除表单
    form.currentPassword = ''
    form.newPassword = ''
    form.confirmPassword = ''
    passwordError.value = ''
    successMessage.value = ''
    
    // 重置密码显示状态
    showCurrentPassword.value = false
    showNewPassword.value = false
    showConfirmPassword.value = false
    
    emit('close')
  }
}

// 监听可见性变化
watch(() => props.visible, (newVal) => {
  if (newVal && props.isRequired) {
    // 如果是强制修改，自动聚焦到新密码输入框
    setTimeout(() => {
      const input = document.getElementById('newPassword')
      if (input) input.focus()
    }, 100)
  }
})
</script>

<style scoped>
.change-password-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.change-password-modal {
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.2);
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 28px 28px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.header-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  flex: 1;
}

.modal-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  flex-shrink: 0;
}

.modal-header h2 {
  margin: 0 0 6px 0;
  color: #2d3748;
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
}

.modal-subtitle {
  margin: 0;
  color: #718096;
  font-size: 14px;
  line-height: 1.4;
}

.close-button {
  background: #f7fafc;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a0aec0;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
  padding: 0;
  outline: none;
}

.close-button:hover {
  background: #e2e8f0;
  color: #4a5568;
  transform: rotate(90deg);
}

/* 首次登录提示 */
.required-notice {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  background: linear-gradient(135deg, #f0f4ff 0%, #f9f5ff 100%);
  border: 1px solid #e9d8fd;
  border-radius: 12px;
  margin: 20px 28px;
  padding: 20px;
  text-align: left;
}

.notice-icon {
  flex-shrink: 0;
  color: #8b5cf6;
  margin-top: 2px;
}

.notice-content h3 {
  color: #553c9a;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 6px;
  line-height: 1.3;
}

.notice-content p {
  color: #6b7280;
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
}

/* 表单样式 */
.change-password-form {
  padding: 0 28px 28px;
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
  z-index: 1;
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
  z-index: 1;
}

.password-toggle:hover {
  color: #667eea;
}

/* 消息提示样式 */
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

.success-message {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: #f0fff4;
  color: #2f855a;
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 14px;
  margin-bottom: 20px;
  border: 1px solid #c6f6d5;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.success-icon {
  flex-shrink: 0;
  color: #38a169;
}

/* 表单操作按钮 */
.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 28px;
}

.cancel-button,
.submit-button {
  flex: 1;
  padding: 16px;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 52px;
}

.cancel-button {
  background: #f7fafc;
  color: #4a5568;
  border: 2px solid #e2e8f0;
}

.cancel-button:hover:not(:disabled) {
  background: #e2e8f0;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.submit-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 25px rgba(102, 126, 234, 0.4);
}

.submit-button:active:not(:disabled) {
  transform: translateY(0);
}

.cancel-button:disabled,
.submit-button:disabled {
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

/* 响应式设计 */
@media (max-width: 480px) {
  .change-password-overlay {
    padding: 16px;
  }
  
  .change-password-modal {
    max-height: 95vh;
  }
  
  .modal-header {
    padding: 24px 20px 16px;
  }
  
  .required-notice {
    margin: 16px 20px;
    padding: 16px;
  }
  
  .change-password-form {
    padding: 0 20px 24px;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .cancel-button,
  .submit-button {
    width: 100%;
  }
}
</style>