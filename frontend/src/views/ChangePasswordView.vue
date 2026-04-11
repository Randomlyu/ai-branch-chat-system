<template>
  <div class="change-password-view">
    <div class="bg-decoration">
      <div class="bg-circle-1"></div>
      <div class="bg-circle-2"></div>
      <div class="bg-circle-3"></div>
    </div>
    
    <div class="container">
      <div class="header">
        <div class="logo-container">
          <div class="logo-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <h1>安全设置</h1>
          <p class="subtitle">修改登录密码</p>
        </div>
        
        <div class="security-tip">
          <svg class="tip-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 15V12M12 9H12.01M21 12C21 13.1819 20.7672 14.3522 20.3149 15.4442C19.8626 16.5361 19.1997 17.5282 18.364 18.364C17.5282 19.1997 16.5361 19.8626 15.4442 20.3149C14.3522 20.7672 13.1819 21 12 21C10.8181 21 9.64778 20.7672 8.55585 20.3149C7.46392 19.8626 6.47177 19.1997 5.63604 18.364C4.80031 17.5282 4.13738 16.5361 3.68508 15.4442C3.23279 14.3522 3 13.1819 3 12C3 9.61305 3.94821 7.32387 5.63604 5.63604C7.32387 3.94821 9.61305 3 12 3C14.3869 3 16.6761 3.94821 18.364 5.63604C20.0518 7.32387 21 9.61305 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <div class="tip-content">
            <h3>首次登录，请设置新密码</h3>
            <p>为了您的账户安全，请设置一个强密码并妥善保管</p>
          </div>
        </div>
        
        <div class="initial-password-hint">
          <svg class="key-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M15 7C16.1046 7 17 7.89543 17 9C17 10.1046 16.1046 11 15 11C13.8954 11 13 10.1046 13 9C13 7.89543 13.8954 7 15 7Z" stroke="currentColor" stroke-width="2"/>
            <path d="M20.5 15C20.5 15 19 15.5 18 15.5C16.276 15.5 13.5 15.5 13.5 20.5C13.5 20.5 13.5 22 12 22C10.5 22 10.5 20.5 10.5 20.5C10.5 15.5 7.724 15.5 6 15.5C5 15.5 3.5 15 3.5 15C3.5 10 7.686 5 12 5C16.314 5 20.5 10 20.5 15Z" stroke="currentColor" stroke-width="2"/>
          </svg>
          <div>
            <span class="hint-label">当前初始密码：</span>
            <code class="password-display">123456</code>
            <span class="hint-text">（登录后此密码将失效）</span>
          </div>
        </div>
      </div>
      
      <div class="password-form-container">
        <ChangePassword 
          :visible="true" 
          :is-required="true" 
          @success="handlePasswordChanged"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import ChangePassword from '@/components/ChangePassword.vue'

const router = useRouter()

const handlePasswordChanged = () => {
  setTimeout(() => {
    router.push('/')
  }, 500)
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

.container {
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  padding: 40px;
  width: 100%;
  max-width: 480px;
  position: relative;
  z-index: 1;
}

/* 头部区域 */
.header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-container {
  margin-bottom: 24px;
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

.header h1 {
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

/* 安全提示 */
.security-tip {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  background: linear-gradient(135deg, #f0f4ff 0%, #f9f5ff 100%);
  border: 1px solid #e9d8fd;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  text-align: left;
}

.tip-icon {
  flex-shrink: 0;
  color: #8b5cf6;
  margin-top: 2px;
}

.tip-content h3 {
  color: #553c9a;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 6px;
}

.tip-content p {
  color: #6b7280;
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
}

/* 初始密码提示 */
.initial-password-hint {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 16px;
  font-size: 14px;
}

.key-icon {
  flex-shrink: 0;
  color: #667eea;
}

.hint-label {
  color: #4a5568;
  font-weight: 500;
  margin-right: 6px;
}

.password-display {
  background: #2d3748;
  color: #fff;
  padding: 4px 10px;
  border-radius: 6px;
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-weight: 600;
  letter-spacing: 0.5px;
  margin-right: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.hint-text {
  color: #718096;
  font-size: 13px;
}

/* 密码表单容器 */
.password-form-container {
  padding: 20px 0 0;
  border-top: 1px solid #e2e8f0;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .change-password-view {
    padding: 16px;
  }
  
  .container {
    padding: 32px 24px;
  }
  
  .header h1 {
    font-size: 24px;
  }
  
  .security-tip {
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 16px;
  }
  
  .tip-icon {
    margin-top: 0;
  }
  
  .initial-password-hint {
    flex-direction: column;
    text-align: center;
    gap: 8px;
  }
  
  .password-display {
    display: block;
    margin: 8px auto;
    width: fit-content;
  }
}
</style>