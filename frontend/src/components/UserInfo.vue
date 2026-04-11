<template>
  <div class="user-info-container" :class="{ 'collapsed': collapsed }">
    <!-- 收起状态下显示展开按钮 -->
    <div v-if="collapsed" class="collapsed-state" @click="$emit('toggle-collapsed')" title="展开侧边栏">
      <svg class="expand-icon" viewBox="0 0 24 24" width="20" height="20">
        <path fill="currentColor" d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" />
      </svg>
    </div>
    
    <!-- 展开状态下的完整用户信息 -->
    <div v-else class="user-info-expanded">
      <!-- Token用量统计 -->
      <div v-if="aiUsage" class="token-usage">
        <div class="usage-header">
          <span class="usage-title">用量统计</span>
          <span class="usage-percentage">
            {{ Math.round((aiUsage.total_tokens / aiUsage.max_daily_tokens) * 100) }}%
          </span>
        </div>
        
        <div class="usage-progress">
          <div 
            class="usage-progress-bar" 
            :style="{ width: `${Math.min(100, (aiUsage.total_tokens / aiUsage.max_daily_tokens) * 100)}%` }"
            :class="{ 'near-limit': (aiUsage.total_tokens / aiUsage.max_daily_tokens) > 0.8 }"
          ></div>
        </div>
        
        <div class="usage-details">
          <span class="usage-text">
            已用: {{ formatNumber(aiUsage.total_tokens) }}/{{ formatNumber(aiUsage.max_daily_tokens) }}
          </span>
          <span class="usage-reset" v-if="nextResetTime">
            重置: {{ formatResetTime(nextResetTime) }}
          </span>
        </div>
      </div>
      
      <!-- 用户信息和操作菜单 -->
      <div class="user-profile-section">
        <div class="user-profile" ref="userProfileRef">
          <div class="user-avatar-container">
            <div class="user-avatar" @click="toggleMenu" :class="{ 'menu-open': showMenu }">
              {{ avatarText }}
            </div>
            
            <!-- 操作菜单 - 显示在头像右上方 -->
            <div v-if="showMenu" class="user-menu" @click.stop>
              <button 
                v-if="showChangePasswordButton"
                class="menu-item btn-change-password" 
                @click="handleChangePassword"
              >
                <svg class="menu-icon" viewBox="0 0 24 24" width="16" height="16">
                  <path fill="currentColor" d="M12,15C12.81,15 13.5,14.7 14.11,14.11C14.7,13.5 15,12.81 15,12C15,11.19 14.7,10.5 14.11,9.89C13.5,9.3 12.81,9 12,9C11.19,9 10.5,9.3 9.89,9.89C9.3,10.5 9,11.19 9,12C9,12.81 9.3,13.5 9.89,14.11C10.5,14.7 11.19,15 12,15M12,2C14.75,2 17.1,3 19.05,4.95C21,6.9 22,9.25 22,12V13.45C22,14.45 21.65,15.3 21,16C20.3,16.67 19.5,17 18.5,17C17.3,17 16.31,16.5 15.56,15.5C14.56,16.5 13.38,17 12,17C10.63,17 9.45,16.5 8.46,15.54C7.5,14.55 7,13.38 7,12C7,10.63 7.5,9.45 8.46,8.46C9.45,7.5 10.63,7 12,7C13.38,7 14.55,7.5 15.54,8.46C16.5,9.45 17,10.63 17,12V13.45C17,13.86 17.16,14.22 17.46,14.53C17.76,14.84 18.11,15 18.5,15C18.92,15 19.27,14.84 19.57,14.53C19.87,14.22 20,13.86 20,13.45V12C20,9.81 19.23,7.93 17.65,6.35C16.07,4.77 14.19,4 12,4C9.81,4 7.93,4.77 6.35,6.35C4.77,7.93 4,9.81 4,12C4,14.19 4.77,16.07 6.35,17.65C7.93,19.23 9.81,20 12,20H17V22H12C9.25,22 6.9,21 4.95,19.05C3,17.1 2,14.75 2,12C2,9.25 3,6.9 4.95,4.95C6.9,3 9.25,2 12,2Z"/>
                </svg>
                修改密码
              </button>
              
              <button 
                class="menu-item btn-logout" 
                @click="handleLogout"
              >
                <svg class="menu-icon" viewBox="0 0 24 24" width="16" height="16">
                  <path fill="currentColor" d="M16,17V14H9V10H16V7L21,12L16,17M14,2A2,2 0 0,1 16,4V6H14V4H5V20H14V18H16V20A2,2 0 0,1 14,22H5A2,2 0 0,1 3,20V4A2,2 0 0,1 5,2H14Z"/>
                </svg>
                退出登录
              </button>
            </div>
          </div>
          
          <div class="user-details">
            <div class="username">{{ username }}</div>
            <div class="user-email">{{ email || '已登录' }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { useAuthStore } from '@/stores/auth'

interface Props {
  collapsed?: boolean
  showChangePasswordButton?: boolean
  aiUsage?: {
    current_date: string
    total_tokens: number
    max_daily_tokens: number
    remaining_tokens: number
    next_reset?: string
    next_reset_timestamp?: number
  } | null
}

// 定义props变量
const props = withDefaults(defineProps<Props>(), {
  collapsed: false,
  showChangePasswordButton: true
})

const emit = defineEmits<{
  'change-password': []
  'logout': []
  'toggle-collapsed': []
}>()

const authStore = useAuthStore()
const showMenu = ref(false)
const userProfileRef = ref<HTMLElement>()

// 计算属性
const username = computed(() => authStore.currentUser?.username || '未登录')
const email = computed(() => authStore.currentUser?.email)
const avatarText = computed(() => {
  const name = authStore.currentUser?.username || 'U'
  return name.charAt(0).toUpperCase()
})

// 计算下次重置时间
const nextResetTime = computed(() => {
  if (!props.aiUsage) return null
  
  if (props.aiUsage.next_reset) {
    return props.aiUsage.next_reset
  }
  
  if (props.aiUsage.next_reset_timestamp) {
    return new Date(props.aiUsage.next_reset_timestamp).toISOString()
  }
  
  if (props.aiUsage.current_date) {
    try {
      const today = new Date(props.aiUsage.current_date)
      const tomorrow = new Date(today)
      tomorrow.setDate(today.getDate() + 1)
      tomorrow.setHours(0, 0, 0, 0)
      
      return tomorrow.toISOString()
    } catch (e) {
      console.error('计算重置时间失败:', e)
    }
  }
  
  return null
})

// 方法
const handleChangePassword = () => {
  closeMenu()
  emit('change-password')
}

const handleLogout = () => {
  closeMenu()
  emit('logout')
}

const toggleMenu = () => {
  showMenu.value = !showMenu.value
}

const closeMenu = () => {
  showMenu.value = false
}

// 点击外部关闭菜单
const handleClickOutside = (event: MouseEvent) => {
  if (userProfileRef.value && !userProfileRef.value.contains(event.target as Node)) {
    closeMenu()
  }
}

// 添加全局点击事件监听
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

// 移除全局点击事件监听
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 工具函数
const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const formatResetTime = (timestamp: string): string => {
  if (!timestamp) return '未知'
  
  try {
    const resetTime = new Date(timestamp)
    
    if (isNaN(resetTime.getTime())) {
      return '未知'
    }
    
    const beijingTime = new Date(resetTime.getTime() + 8 * 60 * 60 * 1000)
    
    const month = String(beijingTime.getUTCMonth() + 1).padStart(2, '0')
    const day = String(beijingTime.getUTCDate()).padStart(2, '0')
    const hours = String(beijingTime.getUTCHours()).padStart(2, '0')
    const minutes = String(beijingTime.getUTCMinutes()).padStart(2, '0')
    
    return `${month}-${day} ${hours}:${minutes}`
  } catch {
    return '未知'
  }
}
</script>

<style scoped>
.user-info-container {
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background-color: #f9fafb;
  transition: all 0.3s ease;
  flex-shrink: 0;
  overflow: hidden;
}

.user-info-container.collapsed {
  min-height: 0;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.collapsed-state {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.collapsed-state:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.expand-icon {
  color: #6b7280;
  transition: transform 0.2s;
}

.collapsed-state:hover .expand-icon {
  transform: translateX(2px);
  color: #3b82f6;
}

.user-info-expanded {
  padding: 16px;
}

/* Token用量统计 */
.token-usage {
  margin-bottom: 16px;
  padding: 12px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.usage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.usage-title {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.usage-percentage {
  font-size: 12px;
  font-weight: 600;
  color: #3b82f6;
}

.usage-progress {
  height: 6px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}

.usage-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #3b82f6);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.usage-progress-bar.near-limit {
  background: linear-gradient(90deg, #f59e0b, #ef4444);
  animation: pulse-warning 2s infinite;
}

@keyframes pulse-warning {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

.usage-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
}

.usage-text {
  color: #666;
}

.usage-reset {
  color: #888;
  font-size: 10px;
}

/* 用户信息区域 */
.user-profile-section {
  position: relative;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

.user-avatar-container {
  position: relative;
  display: block;
  width: 40px; /* 头像宽度 */
  height: 40px; /* 头像高度 */
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
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  z-index: 10;
}

.user-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.user-avatar.menu-open {
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.5);
  transform: scale(1.05);
  z-index: 1000;
}

.user-details {
  flex: 1;
  min-width: 0;
}

.username {
  font-weight: 600;
  color: #1f2937;
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

/* 操作菜单样式 - 显示在头像右上方，离头像更近 */
.user-menu {
  position: absolute;
  top: 0; /* 与头像顶部对齐 */
  left: 0; /* 从头像左侧开始 */
  transform: translate(calc(30%), -100%); /* 调整：向右移动100%宽度+4px，向上移动90%高度，离头像更近 */
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  overflow: hidden;
  animation: slideIn 0.2s ease;
  border: 1px solid rgba(0, 0, 0, 0.08);
  min-width: 140px;
  white-space: nowrap;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translate(calc(30%), -100%); /* 调整动画起始位置 */
  }
  to {
    opacity: 1;
    transform: translate(calc(30%), -100%); /* 调整动画结束位置 */
  }
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  background: none;
  color: #374151;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-item:hover {
  background-color: #f9fafb;
  color: #1f2937;
}

.btn-change-password:hover {
  color: #3b82f6;
}

.btn-logout:hover {
  color: #ef4444;
}

.menu-icon {
  flex-shrink: 0;
  width: 16px;
  height: 16px;
}
</style>