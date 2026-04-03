<template>
  <!-- 移除根元素的 @click 事件 -->
  <div class="user-info" :class="{ 'collapsed': collapsed }">
    <!-- 只在收起状态的头像上添加点击事件 -->
    <div v-if="collapsed" class="user-collapsed-info" @click="toggleCollapsed" title="点击展开侧边栏">
      {{ avatarText }}
    </div>
    
    <!-- 展开状态下的内容 -->
    <template v-else>
      <div class="user-avatar">
        {{ avatarText }}
      </div>
      
      <div class="user-details">
        <div class="username">{{ username }}</div>
        <div v-if="email" class="user-email">{{ email }}</div>
        <div v-else class="user-email">已登录</div>
      </div>
      
      <div class="user-actions">
        <button 
          v-if="showChangePasswordButton"
          class="btn-user-action btn-change-password" 
          @click.stop="handleChangePassword"
          title="修改密码"
        >
          <svg class="action-icon" viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M12,15C12.81,15 13.5,14.7 14.11,14.11C14.7,13.5 15,12.81 15,12C15,11.19 14.7,10.5 14.11,9.89C13.5,9.3 12.81,9 12,9C11.19,9 10.5,9.3 9.89,9.89C9.3,10.5 9,11.19 9,12C9,12.81 9.3,13.5 9.89,14.11C10.5,14.7 11.19,15 12,15M12,2C14.75,2 17.1,3 19.05,4.95C21,6.9 22,9.25 22,12V13.45C22,14.45 21.65,15.3 21,16C20.3,16.67 19.5,17 18.5,17C17.3,17 16.31,16.5 15.56,15.5C14.56,16.5 13.38,17 12,17C10.63,17 9.45,16.5 8.46,15.54C7.5,14.55 7,13.38 7,12C7,10.63 7.5,9.45 8.46,8.46C9.45,7.5 10.63,7 12,7C13.38,7 14.55,7.5 15.54,8.46C16.5,9.45 17,10.63 17,12V13.45C17,13.86 17.16,14.22 17.46,14.53C17.76,14.84 18.11,15 18.5,15C18.92,15 19.27,14.84 19.57,14.53C19.87,14.22 20,13.86 20,13.45V12C20,9.81 19.23,7.93 17.65,6.35C16.07,4.77 14.19,4 12,4C9.81,4 7.93,4.77 6.35,6.35C4.77,7.93 4,9.81 4,12C4,14.19 4.77,16.07 6.35,17.65C7.93,19.23 9.81,20 12,20H17V22H12C9.25,22 6.9,21 4.95,19.05C3,17.1 2,14.75 2,12C2,9.25 3,6.9 4.95,4.95C6.9,3 9.25,2 12,2Z"/>
          </svg>
          修改密码
        </button>
        <button 
          class="btn-user-action btn-logout" 
          @click.stop="handleLogout"
          title="退出登录"
        >
          <svg class="action-icon" viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M16,17V14H9V10H16V7L21,12L16,17M14,2A2,2 0 0,1 16,4V6H14V4H5V20H14V18H16V20A2,2 0 0,1 14,22H5A2,2 0 0,1 3,20V4A2,2 0 0,1 5,2H14Z"/>
          </svg>
          退出
        </button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

interface Props {
  collapsed?: boolean
  showChangePasswordButton?: boolean
}

withDefaults(defineProps<Props>(), {
  collapsed: false,
  showChangePasswordButton: true
})

const emit = defineEmits<{
  'change-password': []
  'logout': []
  'toggle-collapsed': []
}>()

const authStore = useAuthStore()

// 计算属性
const username = computed(() => authStore.currentUser?.username || '未登录')
const email = computed(() => authStore.currentUser?.email)
const avatarText = computed(() => {
  const name = authStore.currentUser?.username || 'U'
  return name.charAt(0).toUpperCase()
})

// 方法
const handleChangePassword = () => {
  emit('change-password')
}

const handleLogout = () => {
  emit('logout')
}

const toggleCollapsed = () => {
  emit('toggle-collapsed')
}
</script>

<style scoped>
.user-info {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background-color: #f9fafb;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  cursor: default; /* 改为默认光标，不再表示可点击 */
  transition: background-color 0.2s;
  user-select: none;
  flex-shrink: 0; /* 确保不会挤压 */
}

.user-info:hover {
  background-color: #f9fafb;
}

.user-info.collapsed {
  justify-content: center;
  padding: 12px;
  cursor: pointer; /* 只在收起状态下显示可点击光标 */
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 18px;
  margin-right: 12px;
  flex-shrink: 0;
}

.user-info.collapsed .user-avatar {
  display: none; /* 在收起状态下隐藏正常头像 */
}

.user-details {
  flex: 1;
  min-width: 0;
  margin-right: 12px;
}

.username {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-email {
  color: #6b7280;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.btn-user-action {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  font-size: 12px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background-color: white;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-user-action:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.btn-change-password:hover {
  background-color: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.btn-logout:hover {
  background-color: #ef4444;
  color: white;
  border-color: #ef4444;
}

.action-icon {
  flex-shrink: 0;
}

.user-info.collapsed .user-details,
.user-info.collapsed .user-actions {
  display: none;
}

.user-collapsed-info {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 16px;
  cursor: pointer;
  transition: transform 0.2s;
}

.user-collapsed-info:hover {
  transform: scale(1.1);
}
</style>