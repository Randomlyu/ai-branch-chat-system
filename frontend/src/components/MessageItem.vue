<template>
  <div 
    class="message-wrapper" 
    :class="[
      msg.role, 
      { 'is-editing': msg.is_editing }
    ]"
  >
    <!-- 简约头像区域 -->
    <div class="message-avatar-container">
      <div class="message-avatar">
        <template v-if="msg.role === 'user'">
          <!-- 简约用户图标 -->
          <svg class="avatar-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 12C14.7614 12 17 9.76142 17 7C17 4.23858 14.7614 2 12 2C9.23858 2 7 4.23858 7 7C7 9.76142 9.23858 12 12 12Z" fill="currentColor"/>
            <path d="M12 14.5C7.99 14.5 4.5 16.36 4.5 20.5C4.5 20.78 4.72 21 5 21H19C19.28 21 19.5 20.78 19.5 20.5C19.5 16.36 16.01 14.5 12 14.5Z" fill="currentColor"/>
          </svg>
        </template>
        <template v-else>
            <svg class="avatar-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#4F46E5"/>
      <stop offset="100%" stop-color="#8B5CF6"/>
    </linearGradient>
  </defs>
  <circle cx="12" cy="12" r="11" fill="url(#bgGrad2)"/>
  
  <!-- 外侧半透明轨道 -->
  <path d="M18.5 12 A6.5 6.5 0 0 1 12 18.5" stroke="#FFFFFF" stroke-opacity="0.3" stroke-width="1.2" fill="none" stroke-linecap="round"/>
  <path d="M5.5 12 A6.5 6.5 0 0 1 12 5.5" stroke="#FFFFFF" stroke-opacity="0.3" stroke-width="1.2" fill="none" stroke-linecap="round"/>
  
  <!-- 微调后的火花（稍微圆润的角） -->
  <path d="M12 5.5L13.2 9.8L17.5 11L13.2 12.2L12 16.5L10.8 12.2L6.5 11L10.8 9.8L12 5.5Z" 
        fill="#FFFFFF" stroke="#FFFFFF" stroke-width="0.3" stroke-linejoin="round"/>
</svg>
        </template>
      </div>
    </div>

    <div class="message-content">
      <!-- 简约消息元数据 -->
      <div class="message-meta">
        <div class="message-header">
          <!-- 用户显示"您"，AI显示模型名称 -->
          <span class="role-name">
            {{ msg.role === 'user' ? '您' : formattedModelName }}
          </span>
          <span class="message-time">{{ formattedTime }}</span>
        </div>
      </div>

      <!-- 消息内容 -->
      <div 
        class="message-text" 
        v-html="formattedContent">
      </div>
      
      <!-- 流式生成指示器 -->
      <div v-if="isGenerating" class="generating-indicator">
        <div class="generating-dots">
          <span></span><span></span><span></span>
        </div>
        <div class="generating-text">
          <span class="model-name">{{ formattedModelName || 'AI' }}</span> 正在思考中...
        </div>
      </div>
      
      <!-- AI消息操作按钮 -->
      <div class="message-actions" v-if="msg.role === 'assistant'">
        <!-- 复制按钮 -->
        <button 
          class="btn-action copy-btn"
          @click="$emit('copy', msg.content)"
          title="复制消息"
        >
          <svg class="action-icon" viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z"/>
          </svg>
        </button>
        
        <!-- 重新生成按钮 -->
        <button 
          class="btn-action regenerate-btn"
          @click="$emit('regenerate', msg.id)"
          :disabled="!canRegenerate"
          :title="regenerateTitle"
        >
          <svg class="action-icon" viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M12,5V1L7,6L12,11V7A6,6 0 0,1 18,13A6,6 0 0,1 12,19A6,6 0 0,1 6,13H4A8,8 0 0,0 12,21A8,8 0 0,0 20,13A8,8 0 0,0 12,5Z"/>
          </svg>
        </button>
        
        <!-- 分支按钮 -->
        <button 
          class="btn-action branch-btn"
          @click="$emit('branch', msg.id)"
          :disabled="!canCreateBranch || isStreaming"
          :title="branchTitle"
        >
          <svg class="action-icon" viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M9.5,3A2.5,2.5 0 0,1 12,5.5A2,2.5 0 0,1 9.5,8A2.5,2.5 0 0,1 7,5.5A2.5,2.5 0 0,1 9.5,3M14.5,3A2.5,2.5 0 0,1 17,5.5A2.5,2.5 0 0,1 14.5,8A2.5,2.5 0 0,1 12,5.5A2.5,2.5 0 0,1 14.5,3M9.5,9C11,9 12,10 12,11.5C12,13 11,14 9.5,14C8,14 7,13 7,11.5C7,10 8,9 9.5,9M14.5,9C16,9 17,10 17,11.5C17,13 16,14 14.5,14C13,14 12,13 12,11.5C12,10 13,9 14.5,9M4.5,13A2.5,2.5 0 0,1 7,15.5A2.5,2.5 0 0,1 4.5,18A2.5,2.5 0 0,1 2,15.5A2.5,2.5 0 0,1 4.5,13M19.5,13A2.5,2.5 0 0,1 22,15.5A2.5,2.5 0 0,1 19.5,18A2.5,2.5 0 0,1 17,15.5A2.5,2.5 0 0,1 19.5,13Z"/>
          </svg>
        </button>
        
        <!-- 删除按钮 -->
        <button 
          class="btn-action delete-btn"
          @click="$emit('delete', msg.id)"
          :disabled="isStreaming || isBranchingPoint"
          :title="deleteTitle"
        >
          <svg class="action-icon" viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
          </svg>
        </button>
      </div>
      
      <!-- 用户消息操作按钮 -->
      <div class="message-actions" v-else>
        <!-- 复制按钮 -->
        <button 
          class="btn-action copy-btn"
          @click="$emit('copy', msg.content)"
          title="复制消息"
        >
          <svg class="action-icon" viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z"/>
          </svg>
        </button>
        
        <!-- 编辑按钮 -->
        <button 
          class="btn-action edit-btn"
          @click="$emit('edit', msg.id)"
          :disabled="!canEdit"
          :title="editTitle"
        >
          <svg class="action-icon" viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed} from 'vue'
import type { Message } from '@/types/chat'

// 定义Props
interface MessageItemProps {
  // 原始消息对象
  msg: Message
  // 状态相关
  isStreaming: boolean
  isLatestMessage?: boolean
  // 按钮状态相关
  canRegenerate: boolean
  canCreateBranch: boolean
  isBranchingPoint: boolean
  canEdit: boolean
  // 按钮标题相关
  regenerateTitle: string
  branchTitle: string
  deleteTitle: string
  editTitle: string
  // 格式化后的内容
  formattedTime: string
  formattedContent: string
  formattedModelName: string
}

// 使用 withDefaults 设置默认值
const props = withDefaults(defineProps<MessageItemProps>(), {
  isLatestMessage: false
})

// 定义事件
defineEmits<{
  copy: [content: string]
  regenerate: [messageId: number]
  branch: [messageId: number]
  delete: [messageId: number]
  edit: [messageId: number]
}>()

// 计算属性：是否显示生成指示器
const isGenerating = computed(() => {
  if (!props.isStreaming) return false
  if (props.msg.role !== 'assistant') return false
  if (!props.isLatestMessage) return false
  
  return true
})
</script>

<style scoped>
/* 消息包装器 */
.message-wrapper {
  display: flex;
  gap: 16px;
  max-width: 100%;
  width: 100%;
  margin: 0 auto;
  transition: all 0.3s ease;
  position: relative;
}

/* 用户消息右对齐 */
.message-wrapper.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

/* 助理消息左对齐 */
.message-wrapper.assistant {
  align-self: flex-start;
  flex-direction: row;
}

/* 消息内容容器 */
.message-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  /* 设置消息内容的最大宽度 */
  max-width: 90%; /* 默认占父容器的90% */
}

/* 消息文本气泡 */
.message-text {
  line-height: 1.6;
  padding: 12px 16px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.06);
  font-size: 15px;
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
  max-width: 100%; /* 占满.message-content，但.message-content已经有最大宽度限制 */
  width: fit-content; /* 根据内容自适应宽度 */
  min-width: auto; /* 最小宽度，避免太短的消息看起来奇怪 */
}

/* 用户消息气泡样式 */
.user .message-text {
  background: #3b82f6;
  color: white;
  border: none;
  border-bottom-right-radius: 4px;
  max-width: 85%; /* 比助理消息稍窄 */
  margin-left: auto; /* 确保右对齐 */
   min-width: auto;
}

/* 助理消息气泡样式 */
.assistant .message-text {
  border-bottom-left-radius: 4px;
  max-width: 90%; /* 比用户消息稍宽 */
  margin-right: auto; /* 确保左对齐 */
  min-width: auto;
  /* 气泡样式 */
  background: rgb(244, 237, 255);
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  padding: 12px 16px; /* 恢复内边距 */
  border-radius: 12px;
  /* 内容显示 */
  overflow-wrap: break-word;
  word-wrap: break-word;
  white-space: pre-wrap;
  line-height: inherit;
  font-family: inherit;
  color: inherit;
}

/* 响应式调整：中等屏幕 */
@media (min-width: 1200px) {
  .message-content {
    max-width: 85%; /* 在大屏幕上减小最大宽度 */
  }
  
  .user .message-text {
    max-width: 80%; /* 大屏幕上用户消息更窄 */
  }
  
  .assistant .message-text {
    max-width: 85%; /* 大屏幕上助理消息稍宽 */
  }
}

/* 响应式调整：小屏幕 */
@media (max-width: 768px) {
  .message-content {
    max-width: 95%; /* 小屏幕上增加最大宽度 */
  }
  
  .user .message-text {
    max-width: 90%; /* 小屏幕上用户消息稍宽 */
  }
  
  .assistant .message-text {
    max-width: 95%; /* 小屏幕上助理消息更宽 */
  }
  
  .message-text {
    min-width: auto; /* 小屏幕上减小最小宽度 */
  }
}

/* 响应式调整：超小屏幕 */
@media (max-width: 480px) {
  .message-content {
    max-width: 100%; /* 超小屏幕上占满可用宽度 */
  }
  
  .user .message-text {
    max-width: 95%; /* 超小屏幕上用户消息几乎占满 */
  }
  
  .assistant .message-text {
    max-width: 100%; /* 超小屏幕上助理消息占满 */
  }
  
  .message-text {
    min-width: auto; /* 进一步减小最小宽度 */
    padding: 10px 12px; /* 减小内边距 */
    font-size: 14px; /* 减小字体大小 */
  }
}

/* 编辑状态的高亮样式 */
.message-wrapper.is-editing {
  padding: 8px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%);
  border-radius: 12px;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.5);
  }
}

.message-wrapper.user .message-content {
  align-items: flex-end;
}

/* 简约头像容器样式 */
.message-avatar-container {
  position: relative;
  flex-shrink: 0;
  display: flex;
  align-items: flex-start;
  margin-top: 4px;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: #f5f5f5;
  transition: all 0.2s ease;
}

/* 用户头像样式 */
.user .message-avatar {
  background: #d2e4ff;
  color: #0664fc;
}

/* 助理头像样式 */
.assistant .message-avatar {
  background: #a9a1f0;
}

.avatar-icon {
  width: 20px;
  height: 20px;
}

/* 简约消息元数据布局 */
.message-meta {
  margin-bottom: 6px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.role-name {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.user .role-name {
  color: #3b82f6;
}

.assistant .role-name {
  color: #4505d8;
}

.message-time {
  font-size: 12px;
  color: #9ca3af;
  white-space: nowrap;
  font-weight: 400;
}

/* 生成指示器样式 */
.generating-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0 0 0;
  font-size: 12px;
  color: #666;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  margin-top: 8px;
}

.generating-dots {
  display: flex;
  gap: 4px;
}

.generating-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #3b82f6;
  animation: bounce 1.4s infinite ease-in-out both;
}

.generating-dots span:nth-child(1) { animation-delay: -0.32s; }
.generating-dots span:nth-child(2) { animation-delay: -0.16s; }
.generating-dots span:nth-child(3) { animation-delay: 0s; }

.generating-text {
  font-size: 12px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 4px;
}

.model-name {
  font-weight: 600;
  color: #3b82f6;
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1.0); }
}

/* 消息操作按钮 */
.message-actions {
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: all 0.3s ease;
  flex-wrap: wrap;
  align-items: center;
  padding: 4px 0;
}

.message-wrapper:hover .message-actions {
  opacity: 1;
  transform: translateY(0);
}

/* 消息操作按钮通用样式 */
.btn-action {
  padding: 8px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  width: 36px;
  height: 36px;
  position: relative;
  overflow: hidden;
}

.btn-action::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: currentColor;
  opacity: 0;
  transition: opacity 0.2s ease;
  z-index: 0;
}

.btn-action:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.btn-action:active {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.btn-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

/* 消息操作图标 */
.action-icon {
  width: 16px;
  height: 16px;
  display: block;
  position: relative;
  z-index: 1;
  transition: transform 0.2s ease;
}

.btn-action:hover .action-icon {
  transform: scale(1.1);
}

.btn-action:active .action-icon {
  transform: scale(0.95);
}

/* 不同操作按钮的颜色样式 */
.copy-btn {
  color: #3b82f6;
  border-color: rgba(59, 130, 246, 0.3);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%);
}

.copy-btn:hover {
  color: white;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-color: #3b82f6;
}

.regenerate-btn {
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.3);
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%);
}

.regenerate-btn:hover {
  color: white;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-color: #10b981;
}

.regenerate-btn:disabled:hover {
  color: #10b981;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%);
  border-color: rgba(16, 185, 129, 0.3);
}

.branch-btn {
  color: #8b5cf6;
  border-color: rgba(139, 92, 246, 0.3);
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);
}

.branch-btn:hover {
  color: white;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  border-color: #8b5cf6;
}

.branch-btn:disabled {
  color: #9ca3af;
  border-color: rgba(156, 163, 175, 0.3);
  background: linear-gradient(135deg, rgba(156, 163, 175, 0.1) 0%, rgba(156, 163, 175, 0.05) 100%);
}

.branch-btn:disabled:hover {
  color: #9ca3af;
  background: linear-gradient(135deg, rgba(156, 163, 175, 0.1) 0%, rgba(156, 163, 175, 0.05) 100%);
  border-color: rgba(156, 163, 175, 0.3);
}

.delete-btn {
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.3);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%);
}

.delete-btn:hover {
  color: white;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border-color: #ef4444;
}

.delete-btn:disabled:hover {
  color: #ef4444;
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%);
  border-color: rgba(239, 68, 68, 0.3);
}

/* 编辑按钮样式 */
.edit-btn {
  color: #f59e0b;
  border-color: rgba(245, 158, 11, 0.3);
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%);
}

.edit-btn:hover {
  color: white;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border-color: #f59e0b;
}

.edit-btn:disabled:hover {
  color: #f59e0b;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%);
  border-color: rgba(245, 158, 11, 0.3);
}

/* 按钮工具提示 */
.btn-action {
  position: relative;
}

.btn-action::after {
  content: attr(title);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  margin-bottom: 8px;
  pointer-events: none;
  z-index: 1000;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.btn-action:hover::after {
  opacity: 1;
  visibility: visible;
}
</style>