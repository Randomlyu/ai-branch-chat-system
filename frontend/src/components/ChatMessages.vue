<template>
  <div class="messages-container" ref="messagesContainerRef">
    <div v-for="msg in messages" :key="msg.id" class="message-item-wrapper">
      <MessageItem
        :msg="msg"
        :is-streaming="isStreaming"
        :can-regenerate="canRegenerateMessage(msg)"
        :regenerate-title="getRegenerateButtonTitle(msg)"
        :can-create-branch="canCreateBranch(msg)"
        :branch-title="getBranchButtonTitle(msg)"
        :is-branching-point="checkIsMessageBranchingPoint(msg.id)"
        :delete-title="getDeleteButtonTitle(msg)"
        :formatted-time="formatTime(msg.created_at)"
        :formatted-content="formatMessage(msg.content)"
        :formatted-model-name="msg.model_used ? getModelDisplayName(msg.model_used) : ''"
        @copy="handleCopyMessage"
        @regenerate="handleRegenerateMessage"
        @branch="handleCreateBranch"
        @delete="handleDeleteMessage"
      />
    </div>
    
    <!-- 流式生成指示器 -->
    <div v-if="isStreaming" class="streaming-indicator">
      <div class="streaming-dots">
        <span></span><span></span><span></span>
      </div>
      <div class="streaming-text">{{ streamingModelName }}正在生成...</div>
      <button class="btn-stop" @click="handleStopGenerating" title="停止生成">
        停止
      </button>
    </div>
    
    <!-- 思考指示器 -->
    <div v-else-if="isLoading" class="thinking-indicator">
      <div class="thinking-dots">
        <span></span><span></span><span></span>
      </div>
      <div class="thinking-text">AI正在思考...</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import MessageItem from './MessageItem.vue'
import { 
  formatTime, 
  formatMessage, 
  getModelDisplayName 
} from '@/utils/formatters'
import type { Message } from '@/types/chat'

// 定义 Props
const props = defineProps<{
  messages: Message[]
  isStreaming: boolean
  isLoading: boolean
  streamingModel?: string
  isMessageBranchingPoint?: (messageId: number) => boolean
}>()

// 定义 Events
const emit = defineEmits<{
  'copy': [content: string]
  'regenerate': [messageId: number]
  'branch': [messageId: number]
  'delete': [messageId: number]
  'stop': []
}>()

// 模板引用
const messagesContainerRef = ref<HTMLElement>()

// 计算属性
const streamingModelName = computed(() => {
  return props.streamingModel ? getModelDisplayName(props.streamingModel) : 'AI'
})

// 消息操作验证方法
const canRegenerateMessage = (msg: Message): boolean => {
  if (props.isStreaming) return false
  if (msg.role !== 'assistant') return false
  
  // 检查是否是最新消息
  const latestMessage = getLatestMessage()
  if (!latestMessage || latestMessage.id !== msg.id) {
    return false
  }
  
  // 检查是否被分支引用
  if (checkIsMessageBranchingPoint(msg.id)) {
    return false
  }
  
  return true
}

const getRegenerateButtonTitle = (msg: Message): string => {
  if (props.isStreaming) {
    return '请等待生成完成'
  }
  
  if (msg.role !== 'assistant') {
    return '只能重新生成AI消息'
  }
  
  // 检查是否是最新消息
  const latestMessage = getLatestMessage()
  if (!latestMessage) {
    return '当前没有消息'
  }
  
  if (msg.id !== latestMessage.id) {
    return '只能重新生成最新AI消息'
  }
  
  // 检查是否被分支引用
  if (checkIsMessageBranchingPoint(msg.id)) {
    return '此消息已被分支引用，无法重新生成'
  }
  
  return '重新生成此AI回复'
}

const canCreateBranch = (msg: Message) => {
  if (props.isStreaming) return false
  if (msg.role !== 'assistant') return false
  
  const latestMessage = getLatestMessage()
  if (!latestMessage) return false
  return msg.id === latestMessage.id
}

const getBranchButtonTitle = (msg: Message) => {
  if (props.isStreaming) {
    return '请等待生成完成'
  }
  if (msg.role !== 'assistant') {
    return '只能在AI回复处创建分支'
  }
  const latestMessage = getLatestMessage()
  if (!latestMessage) {
    return '当前没有消息'
  }
  if (msg.id !== latestMessage.id) {
    return '只能在最新消息处创建分支'
  }
  return '从此回复创建新分支'
}

const getDeleteButtonTitle = (msg: Message) => {
  if (props.isStreaming) {
    return '请等待生成完成'
  }
  
  if (checkIsMessageBranchingPoint(msg.id)) {
    return '此消息已被分支引用，无法删除'
  }
  
  if (msg.role !== 'assistant') {
    return '只能删除AI消息'
  }
  
  return '删除此AI回复及其对应的用户提问'
}

// 工具方法
const getLatestMessage = (): Message | null => {
  if (props.messages.length === 0) return null
  return props.messages[props.messages.length - 1] || null
}

// 检查消息是否为分支点
const checkIsMessageBranchingPoint = (messageId: number): boolean => {
  // 如果父组件传递了检查方法，使用父组件的方法
  if (props.isMessageBranchingPoint) {
    return props.isMessageBranchingPoint(messageId)
  }
  return false
}

// 事件处理
const handleCopyMessage = (content: string) => {
  emit('copy', content)
}

const handleRegenerateMessage = (messageId: number) => {
  emit('regenerate', messageId)
}

const handleCreateBranch = (messageId: number) => {
  emit('branch', messageId)
}

const handleDeleteMessage = (messageId: number) => {
  emit('delete', messageId)
}

const handleStopGenerating = () => {
  emit('stop')
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainerRef.value) {
    nextTick(() => {
      messagesContainerRef.value!.scrollTop = messagesContainerRef.value!.scrollHeight
    })
  }
}

// 暴露方法给父组件
defineExpose({
  scrollToBottom
})
</script>

<style scoped>
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  background: #f9f9f9;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 0;
  width: 100%;
}

.message-item-wrapper {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 流式生成指示器 */
.streaming-indicator {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(59, 130, 246, 0.05);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
  margin: 12px auto;
  max-width: 100%;
  width: 100%;
  animation: slideDown 0.3s ease;
  box-sizing: border-box;
}

.streaming-dots {
  display: flex;
  gap: 4px;
  margin-right: 12px;
}

.streaming-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #3b82f6;
  animation: bounce 1.4s infinite ease-in-out both;
}

.streaming-dots span:nth-child(1) { animation-delay: -0.32s; }
.streaming-dots span:nth-child(2) { animation-delay: -0.16s; }
.streaming-dots span:nth-child(3) { animation-delay: 0s; }

.streaming-text {
  flex: 1;
  color: #3b82f6;
  font-size: 13px;
  font-weight: 500;
}

.btn-stop {
  padding: 6px 12px;
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-left: 12px;
}

.btn-stop:hover {
  background: rgba(239, 68, 68, 0.2);
  transform: translateY(-1px);
}

.btn-stop:active {
  transform: translateY(0);
}

/* 思考指示器 */
.thinking-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 20px;
  color: #666;
}

.thinking-dots {
  display: flex;
  gap: 4px;
}

.thinking-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #3b82f6;
  animation: bounce 1.4s infinite ease-in-out both;
}

.thinking-dots span:nth-child(1) { animation-delay: -0.32s; }
.thinking-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1.0); }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>