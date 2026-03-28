<template>
  <aside class="sidebar left-sidebar" :class="{ 'collapsed': isCollapsed }">
    <div class="sidebar-header">
      <h2>AI对话</h2>
      <div class="sidebar-header-actions">
        <!-- 在非收起状态下显示新建对话按钮 -->
        <button v-if="!isCollapsed" class="btn-new-chat" @click="handleCreateConversation" title="新对话">
          <svg class="new-chat-icon" viewBox="0 0 24 24" width="18" height="18">
            <path fill="currentColor" d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z" />
          </svg>
          新对话
        </button>
        <!-- 收起按钮始终显示 -->
        <button class="btn-toggle-sidebar" @click="$emit('toggle-collapse')" :title="isCollapsed ? '展开侧边栏' : '收起侧边栏'">
            <svg v-if="isCollapsed" class="sidebar-icon" viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" />
            </svg>
            <svg v-else class="sidebar-icon" viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z" />
            </svg>
        </button>
      </div>
    </div>
    <div class="conversations-list">
      <div
        v-for="conv in conversations"
        :key="conv.id"
        class="conversation-item"
        :class="{ 
          active: currentConversation?.id === conv.id,
          editing: editingConversationId === conv.id
        }"
        @click="handleConversationClick(conv.id)"
      >
        <span class="conv-icon">💬</span>
        
        <!-- 对话标题显示 -->
        <div class="conv-title-container">
          <input
            v-if="editingConversationId === conv.id"
            ref="titleInput"
            v-model="editingTitle"
            class="conv-title-edit"
            @blur="handleSaveTitle(conv.id)"
            @keyup.enter="handleSaveTitle(conv.id)"
            @keyup.esc="cancelEditTitle"
          />
          <span v-else class="conv-title">
            {{ conv.title || '未命名对话' }}
          </span>
        </div>
        
        <span class="conv-time">{{ formatTime(conv.updated_at) }}</span>
        
        <!-- 三点菜单按钮 -->
        <button 
          class="conversation-menu-btn"
          @click.stop="handleShowConversationMenu(conv, $event)"
          aria-label="对话操作菜单"
          title="更多操作"
        >
          <svg class="conversation-menu-icon" viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M12,16A2,2 0 0,1 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18A2,2 0 0,1 12,16M12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10M12,4A2,2 0 0,1 14,6A2,2 0 0,1 12,8A2,2 0 0,1 10,6A2,2 0 0,1 12,4Z"/>
          </svg>
        </button>
      </div>
      <div v-if="conversations.length === 0" class="empty-tip">
        暂无对话，点击上方按钮开始
      </div>
    </div>
    
    <!-- AI用量信息 -->
    <div class="usage-info" v-if="aiUsage">
      <div class="usage-title">用量统计</div>
      <div class="usage-progress">
        <div 
          class="usage-progress-bar" 
          :style="{ width: `${Math.min(100, (aiUsage.total_tokens / aiUsage.max_daily_tokens) * 100)}%` }"
          :class="{ 'near-limit': (aiUsage.total_tokens / aiUsage.max_daily_tokens) > 0.8 }"
        ></div>
      </div>
      <div class="usage-details">
        <span class="usage-text">
          已用: {{ formatNumber(aiUsage.total_tokens) }} / {{ formatNumber(aiUsage.max_daily_tokens) }} tokens
        </span>
        <span class="usage-percentage">
          {{ Math.round((aiUsage.total_tokens / aiUsage.max_daily_tokens) * 100) }}%
        </span>
      </div>
      <div class="usage-date" v-if="nextResetTime">下次重置: {{ formatResetTime(nextResetTime) }}</div>
      <div class="usage-date" v-else-if="aiUsage.current_date">重置日期: {{ formatDate(aiUsage.current_date) }}</div>
      <div class="usage-date" v-else>重置时间: 未知</div>
    </div>
    
    <div class="sidebar-footer">
      <div class="user-avatar">U</div>
      <div class="user-info">
        <div class="username">开发者</div>
        <div class="user-email">dev@example.com</div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, nextTick, computed } from 'vue'
import { formatTime, formatNumber } from '@/utils/formatters'
import type { Conversation } from '@/types/chat'

// 定义Props
const props = defineProps<{
  conversations: Conversation[]
  currentConversation: Conversation | null
  aiUsage?: {
    current_date: string
    total_tokens: number
    max_daily_tokens: number
    remaining_tokens: number
    next_reset?: string
    next_reset_timestamp?: number
  } | null
  isCollapsed: boolean
  isStreaming: boolean
}>()

// 定义事件
const emit = defineEmits<{
  'create-conversation': []
  'select-conversation': [id: number]
  'update-title': [id: number, title: string]
  'delete-conversation': [id: number]
  'toggle-collapse': []
  'show-context-menu': [conversation: Conversation, event: MouseEvent]
}>()

// 本地状态
const editingConversationId = ref<number | null>(null)
const editingTitle = ref('')
const titleInput = ref<HTMLInputElement>()

// 计算下次重置时间（兼容旧版API）
const nextResetTime = computed(() => {
  if (!props.aiUsage) return null
  
  // 如果有后端返回的next_reset，直接使用
  if (props.aiUsage.next_reset) {
    return props.aiUsage.next_reset
  }
  
  // 如果有timestamp，转换为ISO字符串
  if (props.aiUsage.next_reset_timestamp) {
    return new Date(props.aiUsage.next_reset_timestamp).toISOString()
  }
  
  // 如果没有next_reset信息，根据current_date计算
  if (props.aiUsage.current_date) {
    try {
      const today = new Date(props.aiUsage.current_date)
      // 计算明天0点（北京时间）
      const tomorrow = new Date(today)
      tomorrow.setDate(today.getDate() + 1)
      tomorrow.setHours(0, 0, 0, 0)
      
      // 转换为ISO字符串
      return tomorrow.toISOString()
    } catch (e) {
      console.error('计算重置时间失败:', e)
    }
  }
  
  return null
})

// 方法
const handleCreateConversation = () => {
  emit('create-conversation')
}

const handleConversationClick = (convId: number) => {
  // 如果正在编辑，不切换对话
  if (editingConversationId.value === convId) return
  
  emit('select-conversation', convId)
}

const handleShowConversationMenu = (conversation: Conversation, event: MouseEvent) => {
  emit('show-context-menu', conversation, event)
}

const handleSaveTitle = (conversationId: number) => {
  if (editingTitle.value.trim() && editingConversationId.value === conversationId) {
    emit('update-title', conversationId, editingTitle.value.trim())
  }
  cancelEditTitle()
}

const cancelEditTitle = () => {
  editingConversationId.value = null
  editingTitle.value = ''
}

// 新增格式化函数
const formatResetTime = (timestamp: string | undefined | null): string => {
  if (!timestamp) return '未知'
  
  try {
    const resetTime = new Date(timestamp)
    
    // 检查是否为无效日期
    if (isNaN(resetTime.getTime())) {
      return '未知'
    }
    
    // 转换为北京时间（如果后端返回的是UTC）
    const beijingTime = new Date(resetTime.getTime() + 8 * 60 * 60 * 1000)
    
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000)
    
    const resetDate = new Date(
      beijingTime.getUTCFullYear(),
      beijingTime.getUTCMonth(),
      beijingTime.getUTCDate()
    )
    
    // 判断是否是今天重置
    if (resetDate.getTime() === today.getTime()) {
      const hours = String(beijingTime.getUTCHours()).padStart(2, '0')
      const minutes = String(beijingTime.getUTCMinutes()).padStart(2, '0')
      return `今天 ${hours}:${minutes}`
    }
    // 判断是否是明天重置
    else if (resetDate.getTime() === tomorrow.getTime()) {
      const hours = String(beijingTime.getUTCHours()).padStart(2, '0')
      const minutes = String(beijingTime.getUTCMinutes()).padStart(2, '0')
      return `明天 ${hours}:${minutes}`
    }
    // 其他时间
    else {
      const month = String(beijingTime.getUTCMonth() + 1).padStart(2, '0')
      const day = String(beijingTime.getUTCDate()).padStart(2, '0')
      const hours = String(beijingTime.getUTCHours()).padStart(2, '0')
      const minutes = String(beijingTime.getUTCMinutes()).padStart(2, '0')
      return `${month}月${day}日 ${hours}:${minutes}`
    }
  } catch (error) {
    console.error('重置时间格式化错误:', error, timestamp)
    return '未知'
  }
}

// 简单日期格式化
const formatDate = (dateStr: string | undefined): string => {
  if (!dateStr) return '未知'
  
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) {
      return dateStr
    }
    
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    
    return `${year}-${month}-${day}`
  } catch {
    return dateStr
  }
}

// 暴露方法供父组件调用
defineExpose({
  startEditingTitle: (conversation: Conversation) => {
    editingConversationId.value = conversation.id
    editingTitle.value = conversation.title || ''
    nextTick(() => {
      titleInput.value?.focus()
      titleInput.value?.select()
    })
  },
  cancelEditTitle
})
</script>

<style scoped>
/* 左侧边栏 */
.left-sidebar {
  width: 320px;
  min-width: 320px;
  border-right: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.08);
}

/* 侧边栏收起状态 */
.left-sidebar.collapsed {
  width: 48px;
  min-width: 48px;
  overflow: visible;
}

/* 侧边栏收起时隐藏内容 */
.left-sidebar.collapsed .sidebar-header h2,
.left-sidebar.collapsed .conversations-list,
.left-sidebar.collapsed .usage-info,
.left-sidebar.collapsed .sidebar-footer,
.left-sidebar.collapsed .btn-new-chat {
  display: none;
}

.sidebar.collapsed {
  min-height: 100vh;
  position: relative;
}

/* 侧边栏头部 */
.sidebar-header {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.9);
}

.sidebar.collapsed .sidebar-header {
  padding: 16px 8px;
  justify-content: center;
  border-bottom: none;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #202123;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sidebar.collapsed .sidebar-header-actions {
  flex-direction: column;
  gap: 8px;
  align-items: center;
  justify-content: center;
  width: 100%;
}

/* 侧边栏内容区域 */
.conversations-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  min-height: 0;
}

/* 侧边栏页脚 */
.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.username {
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-email {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 用量信息 */
.usage-info {
  padding: 16px 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(249, 250, 251, 0.8);
  flex-shrink: 0;
}

.usage-title {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
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
  font-size: 12px;
  margin-bottom: 4px;
}

.usage-text {
  color: #666;
}

.usage-percentage {
  font-weight: 600;
  color: #3b82f6;
}

.usage-date {
  font-size: 11px;
  color: #888;
  text-align: center;
}

/* 对话项 */
.conversation-item {
  padding: 12px 16px 12px 12px;
  border-radius: 8px;
  margin-bottom: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  position: relative;
  background: rgba(255, 255, 255, 0.7);
  gap: 8px;
}

.conversation-item:hover {
  background: rgba(0, 0, 0, 0.04);
  border-color: rgba(0, 0, 0, 0.1);
  transform: translateX(2px);
}

.conversation-item.active {
  background: rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.3);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
}

.conversation-item.editing {
  background: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.2);
}

/* 对话图标 */
.conv-icon {
  font-size: 16px;
  flex-shrink: 0;
  width: 20px;
  text-align: center;
}

/* 对话标题容器 */
.conv-title-container {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 4px;
}

.conv-title {
  font-weight: 500;
  font-size: 13px;
  color: #374151;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.conv-title-edit {
  width: 100%;
  border: 2px solid #3b82f6;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  background: white;
  box-sizing: border-box;
}

.conv-title-edit:focus {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* 对话时间 */
.conv-time {
  font-size: 11px;
  color: #888;
  flex-shrink: 0;
  margin-left: auto;
  margin-right: 8px;
  white-space: nowrap;
}

/* 三点菜单按钮 */
.conversation-menu-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  padding: 0;
  flex-shrink: 0;
  opacity: 0;
  margin-left: 4px;
}

.conversation-item:hover .conversation-menu-btn {
  opacity: 1;
  border-color: rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.9);
}

.conversation-menu-btn:hover {
  background: rgba(0, 0, 0, 0.05) !important;
  border-color: rgba(0, 0, 0, 0.15) !important;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.conversation-menu-icon {
  width: 16px;
  height: 16px;
  color: #6b7280;
  transition: color 0.2s ease;
}

.conversation-menu-btn:hover .conversation-menu-icon {
  color: #374151;
}

/* 当侧边栏收起时，隐藏三点按钮 */
.left-sidebar.collapsed .conversation-menu-btn {
  display: none;
}

/* 空状态提示 */
.empty-tip {
  padding: 20px 12px;
  text-align: center;
  color: #999;
  font-size: 13px;
  font-style: italic;
}

/* 新对话按钮 */
.btn-new-chat {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: white;
  font-weight: 500;
  padding: 10px 16px;
  border-radius: 10px;
  border: none;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.btn-new-chat:hover {
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);
}

.btn-new-chat:active {
  transform: translateY(0);
}

.new-chat-icon {
  transition: transform 0.3s ease;
  width: 18px;
  height: 18px;
}

.btn-new-chat:hover .new-chat-icon {
  transform: rotate(90deg);
}

/* 左侧边栏收起按钮样式 - 与右侧统一 */
.btn-toggle-sidebar {
  width: 36px;
  height: 36px;
  border: none;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(168, 85, 247, 0.1));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: #8b5cf6;
  padding: 0;
  flex-shrink: 0;
  backdrop-filter: blur(8px);
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.2);
}

.btn-toggle-sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.btn-toggle-sidebar:hover {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(168, 85, 247, 0.2));
  color: #7c3aed;
  transform: scale(1.05) translateY(-1px);
  box-shadow: 0 8px 20px rgba(139, 92, 246, 0.3);
}

.btn-toggle-sidebar:hover::before {
  opacity: 1;
}

.btn-toggle-sidebar:active {
  transform: scale(0.95) translateY(0);
}

.sidebar-icon {
  transition: transform 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  width: 20px;
  height: 20px;
}

.btn-toggle-sidebar:hover .sidebar-icon {
  transform: scale(1.2);
}
</style>