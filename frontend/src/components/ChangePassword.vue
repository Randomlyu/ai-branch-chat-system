<template>
  <div class="change-password-overlay" v-if="visible">
    <div class="change-password-modal">
      <div class="modal-header">
        <h2>修改密码</h2>
        <button v-if="!isRequired" @click="close" class="close-button" aria-label="关闭">
          &times;
        </button>
      </div>
      
      <div v-if="isRequired" class="required-notice">
        <div class="notice-icon">⚠️</div>
        <h3>首次登录需要修改密码</h3>
        <p>为保护您的账户安全，请立即修改密码</p>
      </div>
      
      <form @submit.prevent="handleChangePassword" class="change-password-form">
        <div v-if="!isRequired" class="form-group">
          <label for="currentPassword">当前密码</label>
          <input
            v-model="form.currentPassword"
            type="password"
            id="currentPassword"
            :disabled="isLoading"
            placeholder="输入当前密码"
            required
          />
        </div>
        
        <div class="form-group">
          <label for="newPassword">新密码</label>
          <input
            v-model="form.newPassword"
            type="password"
            id="newPassword"
            :disabled="isLoading"
            placeholder="输入新密码（至少6位）"
            required
          />
        </div>
        
        <div class="form-group">
          <label for="confirmPassword">确认新密码</label>
          <input
            v-model="form.confirmPassword"
            type="password"
            id="confirmPassword"
            :disabled="isLoading"
            placeholder="再次输入新密码"
            required
          />
        </div>
        
        <div v-if="passwordError" class="error-message">
          {{ passwordError }}
        </div>
        
        <div v-if="successMessage" class="success-message">
          {{ successMessage }}
        </div>
        
        <div class="form-actions">
          <button v-if="!isRequired" type="button" @click="close" :disabled="isLoading" class="cancel-button">
            取消
          </button>
          <button type="submit" :disabled="isLoading" class="submit-button">
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

const form = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

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
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.change-password-modal {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 450px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
}

.modal-header h2 {
  margin: 0;
  color: #333;
  font-size: 20px;
  font-weight: 600;
}

.close-button {
  background: none;
  border: none;
  font-size: 28px;
  color: #999;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-button:hover {
  background-color: #f5f5f5;
  color: #333;
}

.required-notice {
  background-color: #fff8e1;
  padding: 20px 24px;
  border-bottom: 1px solid #ffe082;
  text-align: center;
}

.notice-icon {
  font-size: 40px;
  margin-bottom: 10px;
}

.required-notice h3 {
  margin: 0 0 8px 0;
  color: #f57c00;
  font-size: 18px;
  font-weight: 600;
}

.required-notice p {
  margin: 0;
  color: #ff9800;
  font-size: 14px;
}

.change-password-form {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  color: #555;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 6px;
}

.form-group input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.3s;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-group input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.error-message {
  background-color: #fee;
  color: #c33;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
  margin-bottom: 20px;
  text-align: center;
}

.success-message {
  background-color: #e8f5e9;
  color: #2e7d32;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
  margin-bottom: 20px;
  text-align: center;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.cancel-button,
.submit-button {
  flex: 1;
  padding: 14px;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.cancel-button {
  background-color: #f5f5f5;
  color: #666;
}

.cancel-button:hover:not(:disabled) {
  background-color: #e0e0e0;
}

.submit-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.2);
}

.cancel-button:disabled,
.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
</style>