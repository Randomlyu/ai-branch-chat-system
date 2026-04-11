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
    
    <!-- 对话列表区域 -->
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
    
    <UserInfo
      :collapsed="isCollapsed"
      :ai-usage="aiUsage"
      :show-change-password-button="!isCollapsed"
      @change-password="$emit('change-password')"
      @logout="$emit('logout')"
      @toggle-collapsed="$emit('toggle-collapse')"
    />
  </aside>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { formatTime } from '@/utils/formatters'
import type { Conversation } from '@/types/chat'
import UserInfo from '@/components/UserInfo.vue'

// 定义Props
defineProps<{
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
  'change-password': [] 
  'logout': [] 
}>()

// 本地状态
const editingConversationId = ref<number | null>(null)
const editingTitle = ref('')
const titleInput = ref<HTMLInputElement>()

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
/* 左侧边栏基础布局 */
.sidebar {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: white;
  position: relative;
  transition: all 0.3s ease;
}

.left-sidebar {
  width: 320px;
  min-width: 320px;
  border-right: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.08);
}

/* 侧边栏收起状态 */
.left-sidebar.collapsed {
  width: 60px;
  min-width: 60px;
  overflow: visible;
}

/* 侧边栏收起时隐藏内容 */
.left-sidebar.collapsed .sidebar-header h2,
.left-sidebar.collapsed .conversations-list,
.left-sidebar.collapsed .btn-new-chat {
  display: none;
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

.left-sidebar.collapsed .sidebar-header {
  padding: 16px 0;
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

.left-sidebar.collapsed .sidebar-header-actions {
  flex-direction: column;
  gap: 8px;
  align-items: center;
  justify-content: center;
  width: 100%;
}

/* 对话列表区域 - 占据主要空间 */
.conversations-list {
  flex: 1; /* 占据所有可用空间 */
  overflow-y: auto;
  padding: 12px 16px;
  min-height: 0; /* 允许在flex容器内滚动 */
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.left-sidebar.collapsed .conversations-list {
  display: none;
}

/* 对话项样式保持不变 */
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

.conv-icon {
  font-size: 16px;
  flex-shrink: 0;
  width: 20px;
  text-align: center;
}

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

.conv-time {
  font-size: 11px;
  color: #888;
  flex-shrink: 0;
  margin-left: auto;
  margin-right: 8px;
  white-space: nowrap;
}

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

.left-sidebar.collapsed .conversation-menu-btn {
  display: none;
}

.empty-tip {
  padding: 20px 12px;
  text-align: center;
  color: #999;
  font-size: 13px;
  font-style: italic;
}

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