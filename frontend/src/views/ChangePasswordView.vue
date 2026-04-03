<template>
  <div class="change-password-view">
    <div class="container">
      <div class="header">
        <h1>修改密码</h1>
        <p>首次登录需要修改密码以确保账户安全</p>
        <p class="password-hint">当前密码为初始密码: <strong>123456</strong></p>
      </div>
      
      <ChangePassword 
        :visible="true" 
        :is-required="true" 
        @success="handlePasswordChanged"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import ChangePassword from '@/components/ChangePassword.vue'

const router = useRouter()

const handlePasswordChanged = () => {
  // 密码修改成功后跳转到主页面
  router.push('/')
}
</script>

<style scoped>
.change-password-view {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 500px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h1 {
  color: #333;
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
}

.header p {
  color: #666;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 4px;
}

.password-hint {
  color: #f57c00;
  font-weight: 500;
  margin-top: 10px;
  padding: 8px;
  background-color: #fff8e1;
  border-radius: 6px;
  border: 1px solid #ffe082;
}
</style>