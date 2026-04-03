<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>AI分支对话系统</h1>
        <p>登录您的账户</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            v-model="form.username"
            type="text"
            id="username"
            :disabled="isLoading"
            placeholder="输入用户名"
            required
            autofocus
          />
        </div>
        
        <div class="form-group">
          <label for="password">密码</label>
          <input
            v-model="form.password"
            type="password"
            id="password"
            :disabled="isLoading"
            placeholder="输入密码"
            required
          />
        </div>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <button type="submit" :disabled="isLoading" class="login-button">
          <span v-if="isLoading">登录中...</span>
          <span v-else>登录</span>
        </button>
        
        <div class="login-footer">
          <p>初始用户: user1 到 user15，密码: 123456</p>
          <p>首次登录后需要修改密码</p>
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
}

.login-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  color: #333;
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
}

.login-header p {
  color: #666;
  font-size: 14px;
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

.login-button {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 10px;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.2);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-footer {
  margin-top: 20px;
  text-align: center;
  color: #888;
  font-size: 12px;
  line-height: 1.5;
}
</style>