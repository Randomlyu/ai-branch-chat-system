<template>
  <div class="messages-container" ref="messagesContainerRef" @scroll="handleScroll">
    <!-- 新消息提示按钮 - 使用包装函数 -->
    <div v-if="showNewMessageIndicator" class="new-message-indicator" @click="handleNewMessageClick">
      <svg class="indicator-icon" viewBox="0 0 24 24" width="16" height="16">
        <path fill="currentColor" d="M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z" />
      </svg>
      <span>新消息</span>
    </div>

    <!-- 空状态：当没有消息时显示 -->
    <div v-if="messages.length === 0" class="empty-state">
      <div class="empty-state-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
      </div>
      <div class="empty-state-title">你好！我是AI智能助手</div>
      <div class="empty-state-description">试试问点什么，我会尽力帮您！</div>
      <div class="empty-state-hint">发送消息开始对话</div>
    </div>

    <!-- 正常消息列表 -->
    <div v-else>
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
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onUpdated, onMounted, onBeforeUnmount, computed, watch } from 'vue'
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

// 滚动状态
const isUserAtBottom = ref(true)
const showNewMessageIndicator = ref(false)
const lastScrollPosition = ref(0)
const lastMessageCount = ref(0)
const isAutoScrolling = ref(false)
const scrollDebounceTimer = ref<number>()

// 计算是否有新消息
const hasNewMessages = computed(() => {
  return props.messages.length > lastMessageCount.value
})

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

// 滚动处理相关方法
const checkIsAtBottom = (): boolean => {
  if (!messagesContainerRef.value) return true
  
  const container = messagesContainerRef.value
  const threshold = 100 // 距离底部100px以内都算在底部
  
  return container.scrollTop + container.clientHeight >= container.scrollHeight - threshold
}

const handleScroll = () => {
  if (isAutoScrolling.value) {
    isAutoScrolling.value = false
    return
  }
  
  isUserAtBottom.value = checkIsAtBottom()
  
  // 用户滚动到底部时，隐藏新消息提示
  if (isUserAtBottom.value) {
    showNewMessageIndicator.value = false
  }
  
  // 防抖处理
  if (scrollDebounceTimer.value) {
    clearTimeout(scrollDebounceTimer.value)
  }
  
  scrollDebounceTimer.value = window.setTimeout(() => {
    lastScrollPosition.value = messagesContainerRef.value?.scrollTop || 0
  }, 150)
}

// 新消息点击处理
const handleNewMessageClick = () => {
  // 点击新消息提示时强制滚动到底部
  scrollToBottom(true)
}

// 智能滚动：只在用户在底部时滚动
const scrollToBottom = (force: boolean = false) => {
  if (!messagesContainerRef.value) return
  
  // 如果强制滚动或者用户在底部，就滚动
  if (force || isUserAtBottom.value) {
    isAutoScrolling.value = true
    nextTick(() => {
      if (messagesContainerRef.value) {
        messagesContainerRef.value.scrollTop = messagesContainerRef.value.scrollHeight
        isUserAtBottom.value = true
        showNewMessageIndicator.value = false
      }
    })
  } else if (hasNewMessages.value) {
    // 有消息但用户不在底部，显示新消息提示
    showNewMessageIndicator.value = true
  }
}

// 监听消息变化
watch(() => props.messages.length, (newCount, oldCount) => {
  if (newCount > oldCount) {
    // 有新消息到达
    lastMessageCount.value = newCount
    
    // AI流式生成时不强制滚动
    if (props.isStreaming) {
      // 只在用户已经在底部时滚动
      scrollToBottom(false)
    } else {
      // 非流式生成（如重新生成、分支创建等）时强制滚动
      scrollToBottom(true)
    }
  } else if (newCount < oldCount) {
    // 消息被删除，更新计数
    lastMessageCount.value = newCount
  }
})

// 监听流式状态变化
watch(() => props.isStreaming, (isStreaming) => {
  if (!isStreaming) {
    // 流式生成结束时，检查是否在底部
    nextTick(() => {
      isUserAtBottom.value = checkIsAtBottom()
      if (isUserAtBottom.value) {
        showNewMessageIndicator.value = false
      } else if (hasNewMessages.value) {
        showNewMessageIndicator.value = true
      }
    })
  }
})

// 初始化复制按钮
onUpdated(() => {
  // 等待DOM更新后初始化复制按钮
  setTimeout(() => {
    if (messagesContainerRef.value) {
      initCodeCopyButtons(messagesContainerRef.value)
    }
  }, 100)
})

onMounted(() => {
  // 初始时记录消息数量
  lastMessageCount.value = props.messages.length
  // 初始时滚动到底部
  nextTick(() => {
    scrollToBottom(true)
  })
})

onBeforeUnmount(() => {
  if (scrollDebounceTimer.value) {
    clearTimeout(scrollDebounceTimer.value)
  }
})

// 暴露方法给父组件
defineExpose({
  scrollToBottom: (force: boolean = true) => scrollToBottom(force)
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

/* 空状态样式 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
  text-align: center;
  color: #8c8c8c;
  padding: 40px 20px;
  user-select: none;
}

.empty-state-icon {
  margin-bottom: 20px;
  color: #d9d9d9;
  opacity: 0.7;
}

.empty-state-title {
  font-size: 18px;
  font-weight: 500;
  color: #595959;
  margin-bottom: 8px;
}

.empty-state-description {
  font-size: 14px;
  color: #8c8c8c;
  margin-bottom: 4px;
  line-height: 1.5;
}

.empty-state-hint {
  font-size: 13px;
  color: #bfbfbf;
  font-style: italic;
  margin-top: 8px;
}

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
  position: relative;
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

/* 新消息指示器 */
.new-message-indicator {
  position: fixed;
  bottom: 120px; /* 在输入框上方 */
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  z-index: 10;
  transition: all 0.3s ease;
  border: none;
  user-select: none;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.new-message-indicator:hover {
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  transform: translateX(-50%) translateY(-2px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
}

.new-message-indicator:active {
  transform: translateX(-50%) translateY(0);
}

.indicator-icon {
  width: 16px;
  height: 16px;
  transition: transform 0.2s ease;
}

.new-message-indicator:hover .indicator-icon {
  transform: translateY(2px);
}

/* 空状态样式 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
  text-align: center;
  color: #8c8c8c;
  padding: 40px 20px;
  user-select: none;
}

.empty-state-icon {
  margin-bottom: 20px;
  color: #d9d9d9;
  opacity: 0.7;
}

.empty-state-title {
  font-size: 18px;
  font-weight: 500;
  color: #595959;
  margin-bottom: 8px;
}

.empty-state-description {
  font-size: 14px;
  color: #8c8c8c;
  margin-bottom: 4px;
  line-height: 1.5;
}

.empty-state-hint {
  font-size: 13px;
  color: #bfbfbf;
  font-style: italic;
  margin-top: 8px;
}
</style>