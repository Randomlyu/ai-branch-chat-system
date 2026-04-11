<template>
  <div class="messages-container" ref="messagesContainerRef">
    <div v-for="(msg, index) in messages" :key="msg.id" class="message-item-wrapper">
      <MessageItem
        :msg="msg"
        :is-streaming="isStreaming"
        :is-latest-message="index === messages.length - 1"
        :can-regenerate="canRegenerateMessage(msg)"
        :regenerate-title="getRegenerateButtonTitle(msg)"
        :can-create-branch="canCreateBranch(msg)"
        :branch-title="getBranchButtonTitle(msg)"
        :is-branching-point="checkIsMessageBranchingPoint(msg.id)"
        :delete-title="getDeleteButtonTitle(msg)"
        :can-edit="canEditMessage(msg)"
        :edit-title="getEditButtonTitle(msg)"
        :formatted-time="formatDateTime(msg.created_at)"
        :formatted-content="getFormattedMessageContent(msg)"
        :formatted-model-name="msg.model_used ? getModelDisplayName(msg.model_used) : ''"
        @copy="handleCopyMessage"
        @regenerate="handleRegenerateMessage"
        @branch="handleCreateBranch"
        @delete="handleDeleteMessage"
        @edit="handleEditMessage"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onUpdated } from 'vue'
import MessageItem from './MessageItem.vue'
import { 
  formatDateTime
} from '@/utils/formatters'
import { renderMarkdown, initCodeCopyButtons } from '@/utils/markdown-renderer'  // 添加导入
import type { Message } from '@/types/chat'

// 定义 Props
const props = defineProps<{
  messages: Message[]
  isStreaming: boolean
  isMessageBranchingPoint?: (messageId: number) => boolean
  availableModels?: Array<{id: string, name: string}>
}>()

// 定义 Events
const emit = defineEmits<{
  'copy': [content: string]
  'regenerate': [messageId: number]
  'branch': [messageId: number]
  'delete': [messageId: number]
  'edit': [messageId: number]
}>()

// 模板引用
const messagesContainerRef = ref<HTMLElement>()

// 获取模型友好名称
const getModelDisplayName = (modelId: string): string => {
  if (!modelId) return ''
  
  // 如果有availableModels，从中查找
  if (props.availableModels && props.availableModels.length > 0) {
    const model = props.availableModels.find(m => m.id === modelId)
    if (model) {
      return model.name || model.id
    }
  }
  
  // 特殊处理模拟模式
  if (modelId === 'mock' || modelId === '模拟模式') {
    return '模拟模式'
  }
  
  // 默认返回ID
  return modelId
}

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

// ===== 用户消息编辑相关方法 =====
const canEditMessage = (msg: Message): boolean => {
  if (props.isStreaming) return false
  if (msg.role !== 'user') return false
  
  // 检查是否是最新的用户消息
  const latestUserMessage = getLatestUserMessage()
  if (!latestUserMessage || latestUserMessage.id !== msg.id) {
    return false
  }
  
  // 检查是否被分支引用
  if (checkIsMessageBranchingPoint(msg.id)) {
    return false
  }
  
  return true
}

const getEditButtonTitle = (msg: Message): string => {
  if (props.isStreaming) {
    return '请等待生成完成'
  }
  
  if (msg.role !== 'user') {
    return '只能编辑用户消息'
  }
  
  // 检查是否是最新的用户消息
  const latestUserMessage = getLatestUserMessage()
  if (!latestUserMessage) {
    return '当前没有消息'
  }
  
  if (msg.id !== latestUserMessage.id) {
    return '只能编辑最新的用户消息'
  }
  
  // 检查是否被分支引用
  if (checkIsMessageBranchingPoint(msg.id)) {
    return '此消息已被分支引用，无法编辑'
  }
  
  return '编辑此消息'
}
// ====================================

// 工具方法
const getLatestMessage = (): Message | null => {
  if (props.messages.length === 0) return null
  return props.messages[props.messages.length - 1] || null
}

// 获取最新的用户消息
const getLatestUserMessage = (): Message | null => {
  if (props.messages.length === 0) return null
  
  // 从后往前查找第一个用户消息
  for (let i = props.messages.length - 1; i >= 0; i--) {
    const message = props.messages[i]
    if (message?.role === 'user') {
      return message
    }
  }
  return null
}

// 检查消息是否为分支点
const checkIsMessageBranchingPoint = (messageId: number): boolean => {
  // 如果父组件传递了检查方法，使用父组件的方法
  if (props.isMessageBranchingPoint) {
    return props.isMessageBranchingPoint(messageId)
  }
  return false
}

// 格式化消息内容
const getFormattedMessageContent = (msg: Message): string => {
  if (!msg.content) return ''
  
  if (msg.role === 'assistant') {
    // AI消息：使用Markdown渲染，包裹在markdown-content类中
    const rendered = renderMarkdown(msg.content)
    return `<div class="markdown-content">${rendered}</div>`
  } else {
    // 用户消息：简单处理，保持纯文本
    return msg.content
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;')
      .replace(/\n/g, '<br>')
  }
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

// ===== 编辑消息事件处理 =====
const handleEditMessage = (messageId: number) => {
  emit('edit', messageId)
}
// ================================

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainerRef.value) {
    nextTick(() => {
      messagesContainerRef.value!.scrollTop = messagesContainerRef.value!.scrollHeight
    })
  }
}

// 初始化复制按钮
onUpdated(() => {
  // 等待DOM更新后初始化复制按钮
  setTimeout(() => {
    if (messagesContainerRef.value) {
      initCodeCopyButtons(messagesContainerRef.value)
    }
  }, 100)
})

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
  gap: 12px;
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
</style>