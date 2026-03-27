<template>
  <div class="chat-container">
    <!-- 使用新的 Toast 组件 -->
    <AppToast
      v-model:visible="toast.show"
      :message="toast.message"
      :type="toast.type"
    />
    
    <!-- 对话菜单（Teleport到body，避免层级问题） -->
    <Teleport to="body">
      <div 
        v-if="conversationMenu.visible" 
        class="conversation-context-menu"
        :style="conversationMenu.position"
        @click.stop
      >
        <div class="menu-content">
          <button class="menu-item" @click="handleRenameClick">
            <svg class="menu-icon" viewBox="0 0 24 24" width="16" height="16">
              <path fill="currentColor" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
            </svg>
            重命名
          </button>
          <button class="menu-item delete-item" @click="handleDeleteClick">
            <svg class="menu-icon" viewBox="0 0 24 24" width="16" height="16">
              <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
            </svg>
            删除对话
          </button>
        </div>
      </div>
    </Teleport>

    <!-- 删除确认对话框 -->
    <ConfirmDialog
      v-model:visible="showDeleteConfirm"
      title="确认删除"
      :message="`确定要删除对话 ${deletingConversationTitle} 吗？此操作不可恢复。`"
      confirm-text="删除"
      cancel-text="取消"
      danger
      icon="warning"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />
    
    <!-- 删除消息确认对话框 -->
    <ConfirmDialog
      v-model:visible="showDeleteMessageConfirm"
      title="确认删除"
      message="确定要删除此AI回复及其对应的提问吗？此操作不可撤销。"
      confirm-text="删除"
      cancel-text="取消"
      :danger="true"
      icon="warning"
      @confirm="confirmDeleteMessage"
      @cancel="cancelDeleteMessage"
    />
    
    <!-- 重新生成消息确认对话框 -->
    <ConfirmDialog
      v-model:visible="showRegenerateConfirm"
      title="确认重新生成"
      message="确定要重新生成此消息吗？原来的回复将被替换。"
      confirm-text="重新生成"
      cancel-text="取消"
      icon="info"
      @confirm="confirmRegenerateMessage"
      @cancel="cancelRegenerateMessage"
    />
    
    <!-- 删除线程确认对话框 -->
    <ConfirmDialog
      v-model:visible="showDeleteThreadConfirm"
      title="确认删除分支"
      :message="`确定要删除此子分支吗？此操作不可恢复。`"
      confirm-text="删除"
      cancel-text="取消"
      danger
      icon="warning"
      @confirm="confirmDeleteThread"
      @cancel="cancelDeleteThread"
    />

    <!-- 左侧边栏：对话列表 -->
    <ConversationSidebar
      :conversations="conversations"
      :current-conversation="currentConversation"
      :ai-usage="aiUsage"
      :is-collapsed="isLeftSidebarCollapsed"
      :is-streaming="isStreaming"
      @create-conversation="createNewConversation"
      @select-conversation="handleConversationClick"
      @update-title="saveConversationTitle"
      @delete-conversation="handleDeleteConversation"
      @toggle-collapse="toggleLeftSidebar"
      @show-context-menu="showConversationMenu"
      ref="conversationSidebarRef"
    />

    <!-- 主聊天区域 -->
    <main class="main-content">
      <!-- 聊天头部 -->
      <ChatHeader
        :current-conversation="currentConversation"
        :current-thread="currentThread"
        :thread-path="threadPath"
        :available-models="availableModels"
        :current-model="currentModel"
        :is-mock-mode-available="isMockModeAvailable"
        :is-streaming="isStreaming"
        @switch-thread="switchThread"
        @model-change="onModelChange"
      />

      <!-- 消息列表区域 -->
      <ChatMessages
        :messages="messages"
        :is-streaming="isStreaming"
        :is-loading="isLoading"
        :streaming-model="streamingModel"
        :is-message-branching-point="isMessageBranchingPoint"
        :can-regenerate-message="chatStore.validateMessageForRegeneration"
        :get-regenerate-button-title="(msg: Message) => chatStore.getMessageActionTitles(msg).regenerate"
        :can-create-branch="chatStore.validateMessageForBranching"
        :get-branch-button-title="(msg: Message) => chatStore.getMessageActionTitles(msg).branch"
        :get-delete-button-title="(msg: Message) => chatStore.getMessageActionTitles(msg).delete"
        @copy="copyMessage"
        @regenerate="regenerateMessage"
        @branch="createBranchFromMessage"
        @delete="deleteMessage"
        @stop="stopGenerating"
        ref="chatMessagesRef"
      />

      <!-- 输入区域 -->
      <MessageInput
        v-model:user-input="userInput"
        :is-loading="isLoading"
        :is-streaming="isStreaming"
        :is-token-limit-reached="isTokenLimitReached"
        :current-model="currentModel"
        :current-thread="currentThread"
        :current-conversation="currentConversation"
        :ai-usage="aiUsage"
        :can-send="canSendMessage"
        :input-placeholder="getInputPlaceholder()"
        :send-button-title="getSendButtonTitle()"
        :formatted-model-name="getModelDisplayName(currentModel)"
        :remaining-tokens="aiUsage ? formatNumber(aiUsage.remaining_tokens) : ''"
        @send="sendMessage"
        @stop="stopGenerating"
        ref="messageInputRef"
      />
    </main>

    <!-- 右侧边栏：分支树 -->
    <ThreadTreeSidebar
      :thread-tree="threadTree"
      :current-thread-id="currentThread?.id"
      :is-collapsed="isRightSidebarCollapsed"
      :is-streaming="isStreaming"
      @refresh="refreshThreadTree"
      @toggle-collapse="toggleRightSidebar"
      @switch="switchThread"
      @thread-deleted="onThreadDeleted"
      @request-delete-thread="handleRequestDeleteThread"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed, onBeforeUnmount } from 'vue'
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chat'
import type { Conversation, Message } from '@/types/chat'

// 导入组件
import AppToast from '@/components/AppToast.vue'
import ConversationSidebar from '@/components/ConversationSidebar.vue'
import ThreadTreeSidebar from '@/components/ThreadTreeSidebar.vue'
import ChatHeader from '@/components/ChatHeader.vue'
import ChatMessages from '@/components/ChatMessages.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import MessageInput from '@/components/MessageInput.vue'

// 导入工具函数
import { 
  formatNumber, 
  getModelDisplayName 
} from '@/utils/formatters'

// 导入组合式函数
import { useToast } from '@/composables/useToast'

// ---------- 使用组合式函数 ----------
const { toast, showToast } = useToast()

// ---------- 状态与Store ----------
const chatStore = useChatStore()
const {
  conversations,
  currentConversation,
  currentThread,
  messages,
  isLoading,
  threadTree,
  threadPath,
  isStreaming,
  streamingModel,
  aiUsage,
  availableModels,
  currentModel,
  isTokenLimitReached
} = storeToRefs(chatStore)

// ---------- 本地响应式数据 ----------
const userInput = ref('')
const messageInputRef = ref<InstanceType<typeof MessageInput>>()
const conversationSidebarRef = ref<InstanceType<typeof ConversationSidebar>>()
const chatMessagesRef = ref<InstanceType<typeof ChatMessages>>()
const isRightSidebarCollapsed = ref(false)
const isLeftSidebarCollapsed = ref(false)

// ---------- 删除对话相关状态 ----------
const showDeleteConfirm = ref(false)
const deletingConversationId = ref<number | null>(null)
const deletingConversationTitle = ref('')

// ---------- 删除消息确认对话框状态 ----------
const showDeleteMessageConfirm = ref(false)
const deletingMessageId = ref<number | null>(null)

// ---------- 重新生成消息确认对话框状态 ----------
const showRegenerateConfirm = ref(false)
const regeneratingMessageId = ref<number | null>(null)

// ---------- 删除线程确认对话框状态 ----------
const showDeleteThreadConfirm = ref(false)
const deletingThreadInfo = ref<{
  threadId: number | null
  threadTitle: string
  canDelete: boolean
  reason?: string
}>({
  threadId: null,
  threadTitle: '',
  canDelete: true
})

// ---------- 计算属性 ----------
const canSendMessage = computed(() => {
  return chatStore.canSendMessage(userInput.value)
})

const isMockModeAvailable = computed(() => {
  return availableModels.value.includes('模拟模式')
})

// ---------- 侧边栏方法 ----------
/**
 * 切换右侧边栏折叠状态
 */
const toggleRightSidebar = () => {
  isRightSidebarCollapsed.value = !isRightSidebarCollapsed.value
}

/**
 * 切换左侧边栏折叠状态
 */
const toggleLeftSidebar = () => {
  isLeftSidebarCollapsed.value = !isLeftSidebarCollapsed.value
}

// ---------- 对话列表方法 ----------
// 对话菜单状态
const conversationMenu = ref({
  visible: false,
  conversation: null as Conversation | null,
  position: {
    top: '0px',
    left: '0px'
  }
})

/**
 * 显示对话菜单
 */
const showConversationMenu = (conversation: Conversation, event: MouseEvent) => {
  event.stopPropagation()
  event.preventDefault()
  
  const x = event.clientX
  const y = event.clientY
  
  conversationMenu.value = {
    visible: true,
    conversation,
    position: {
      top: `${y}px`,
      left: `${x}px`
    }
  }
}

/**
 * 隐藏对话菜单
 */
const hideConversationMenu = () => {
  conversationMenu.value.visible = false
  conversationMenu.value.conversation = null
}

/**
 * 处理菜单重命名点击
 */
const handleRenameClick = () => {
  if (!conversationMenu.value.conversation) return
  
  const conversation = conversationMenu.value.conversation
  hideConversationMenu()
  
  if (isStreaming.value) {
    showToast('请等待生成完成后再编辑标题', 'error')
    return
  }
  
  conversationSidebarRef.value?.startEditingTitle(conversation)
}

/**
 * 处理菜单删除点击
 */
const handleDeleteClick = () => {
  if (!conversationMenu.value.conversation) return
  
  const conversation = conversationMenu.value.conversation
  hideConversationMenu()
  
  handleDeleteConversation(conversation.id)
}

/**
 * 点击外部关闭菜单
 */
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.conversation-context-menu') && 
      !target.closest('.conversation-menu-btn') &&
      !target.closest('.modal-overlay')) {
    hideConversationMenu()
  }
}

/**
 * 对话点击处理
 */
const handleConversationClick = async (convId: number) => {
  if (conversationMenu.value.visible) {
    hideConversationMenu()
    return
  }
  
  await chatStore.switchConversation(convId)
  scrollToBottom()
}

/**
 * 创建新对话
 */
const createNewConversation = async () => {
  await chatStore.createConversation('新对话')
  userInput.value = ''
  scrollToBottom()
}

/**
 * 保存对话标题
 */
const saveConversationTitle = async (conversationId: number, title: string) => {
  try {
    await chatStore.updateConversationTitle(conversationId, title)
  } catch (error) {
    console.error('更新标题失败:', error)
  }
}

/**
 * 处理删除对话
 */
const handleDeleteConversation = (conversationId: number) => {
  if (isStreaming.value) {
    showToast('请等待生成完成后再删除对话', 'error')
    return
  }
  
  deletingConversationId.value = conversationId
  const conversation = conversations.value.find(c => c.id === conversationId)
  deletingConversationTitle.value = conversation?.title || ''
  showDeleteConfirm.value = true
}

// ---------- 删除对话方法 ----------
/**
 * 取消删除对话
 */
const cancelDelete = () => {
  showDeleteConfirm.value = false
  deletingConversationId.value = null
  deletingConversationTitle.value = ''
}

/**
 * 确认删除对话
 */
const confirmDelete = async () => {
  if (deletingConversationId.value !== null) {
    try {
      await chatStore.deleteConversation(deletingConversationId.value)
      cancelDelete()
      showToast('对话删除成功')
    } catch (error) {
      console.error('删除对话失败:', error)
      showToast('删除对话失败', 'error')
    }
  }
}

// ---------- 主聊天方法 ----------
/**
 * 发送消息
 */
const sendMessage = async () => {
  const text = userInput.value.trim()
  if (!text || isLoading.value || isTokenLimitReached.value) return

  try {
    // 总是使用流式发送消息
    await chatStore.sendMessageStream(text)
    
    userInput.value = ''
    nextTick(() => {
      scrollToBottom()
      messageInputRef.value?.focusInput()
    })
  } catch (error) {
    console.error('发送消息失败:', error)
  }
}

// ---------- 输入相关方法 ----------
/**
 * 获取输入框占位符
 */
const getInputPlaceholder = (): string => {
  return chatStore.getInputPlaceholder()
}

/**
 * 获取发送按钮标题
 */
const getSendButtonTitle = (): string => {
  return chatStore.getSendButtonTitle(userInput.value)
}

/**
 * 停止生成
 */
const stopGenerating = async () => {
  await chatStore.stopStreaming()
}

/**
 * 模型变更处理
 */
const onModelChange = (newModel: string) => {
  chatStore.setCurrentModel(newModel)
  showToast(`已切换到模型: ${getModelDisplayName(newModel)}`, 'success')
}

// ---------- 分支相关方法 ----------
/**
 * 从消息创建分支
 */
const createBranchFromMessage = async (messageId: number) => {
  if (isStreaming.value) {
    showToast('请等待当前生成完成', 'error')
    return
  }
  
  // 验证消息是否存在
  try {
    const isValid = await validateMessageExists(messageId)
    if (!isValid) {
      showToast('消息不存在或已被删除', 'error')
      return
    }
  } catch (error) {
    console.error('验证消息失败:', error)
    showToast('验证消息失败，请稍后重试', 'error')
    return
  }
  
  if (currentThread.value?.depth !== undefined && currentThread.value.depth >= 3) {
    showToast('分支深度已达上限（3层），无法创建更深层的分支', 'error')
    return
  }
  
  // 使用 store 中的最新消息
  if (!chatStore.latestMessage) {
    showToast('当前没有消息，无法创建分支', 'error')
    return
  }
  
  if (messageId !== chatStore.latestMessage.id) {
    showToast('只能在最新消息处创建分支', 'error')
    return
  }
  
  if (chatStore.latestMessage.role !== 'assistant') {
    showToast('只能在AI回复处创建分支', 'error')
    return
  }
  
  try {
    const newThread = await chatStore.createBranch(messageId)
    if (newThread) {
      showToast('分支创建成功')
      nextTick(() => {
        scrollToBottom()
      })
    }
  } catch (error: unknown) {
    console.error('创建分支失败:', error)
  }
}

/**
 * 切换线程
 */
const switchThread = async (threadId: number) => {
  if (isStreaming.value) {
    showToast('请等待生成完成后再切换', 'error')
    return
  }
  await chatStore.switchThread(threadId)
  scrollToBottom()
}

/**
 * 刷新线程树
 */
const refreshThreadTree = () => {
  if (isStreaming.value) {
    showToast('请等待生成完成后再刷新', 'error')
    return
  }
  chatStore.fetchThreadTree()
}

/**
 * 处理线程被删除
 */
const onThreadDeleted = async (threadId: number, parentThreadId?: number | null) => {
  console.log(`线程 ${threadId} 已被删除，父线程ID: ${parentThreadId}`)
  await chatStore.fetchThreadTree()
}

/**
 * 处理删除线程请求
 */
const handleRequestDeleteThread = (payload: { 
  threadId: number; 
  threadTitle: string;
  canDelete?: boolean;
  reason?: string;
}) => {
  if (isStreaming.value) {
    showToast('请等待生成完成后再删除线程', 'error')
    return
  }
  
  // 如果不能删除，直接显示原因
  if (payload.canDelete === false && payload.reason) {
    showToast(payload.reason, 'error')
    return
  }
  
  // 设置删除信息
  deletingThreadInfo.value = {
    threadId: payload.threadId,
    threadTitle: payload.threadTitle,
    canDelete: payload.canDelete ?? true,
    reason: payload.reason
  }
  
  // 显示确认对话框
  showDeleteThreadConfirm.value = true
}

/**
 * 确认删除线程
 */
const confirmDeleteThread = async () => {
  if (deletingThreadInfo.value.threadId === null) {
    return
  }
  
  try {
    const result = await chatStore.deleteThread(deletingThreadInfo.value.threadId)
    
    if (result.success) {
      showToast('线程删除成功', 'success')
      // 重新获取线程树
      await chatStore.fetchThreadTree()
      
      // 如果删除的是当前线程，store 应该已经处理了切换
      if (result.newActiveThreadId) {
        showToast(`已切换到新的线程`, 'success')
      }
    } else {
      showToast(result.error || '删除线程失败', 'error')
    }
  } catch (error) {
    console.error('删除线程失败:', error)
    showToast('删除线程失败', 'error')
  } finally {
    cancelDeleteThread()
  }
}

/**
 * 取消删除线程
 */
const cancelDeleteThread = () => {
  showDeleteThreadConfirm.value = false
  deletingThreadInfo.value = {
    threadId: null,
    threadTitle: '',
    canDelete: true
  }
}

// ---------- 消息操作方法 ----------
/**
 * 检查消息是否为分支点
 */
const isMessageBranchingPoint = (messageId: number): boolean => {
  return chatStore.isMessageBranchingPoint(messageId)
}

/**
 * 复制消息
 */
const copyMessage = async (content: string) => {
  const success = await chatStore.copyToClipboard(content)
  if (success) {
    showToast('消息已复制到剪贴板')
  } else {
    showToast('复制失败，请重试', 'error')
  }
}

/**
 * 重新生成消息
 */
const regenerateMessage = async (messageId: number) => {
  // 验证消息是否存在
  try {
    const isValid = await validateMessageExists(messageId)
    if (!isValid) {
      showToast('消息不存在或已被删除', 'error')
      return
    }
  } catch (error) {
    console.error('验证消息失败:', error)
    showToast('验证消息失败，请稍后重试', 'error')
    return
  }
  
  const message = messages.value.find(msg => msg.id === messageId)
  if (!message) {
    showToast('消息不存在', 'error')
    return
  }
  
  // 使用 store 的验证方法
  const validation = chatStore.validateMessageOperation(messageId, 'regenerate')
  if (!validation.can) {
    showToast(validation.reason || '无法重新生成', 'error')
    return
  }
  
  // 设置要重新生成的消息ID，并显示确认对话框
  regeneratingMessageId.value = messageId
  showRegenerateConfirm.value = true
}

/**
 * 确认重新生成消息
 */
const confirmRegenerateMessage = async () => {
  if (regeneratingMessageId.value === null) {
    return
  }
  
  // 立即关闭对话框
  showRegenerateConfirm.value = false
  const messageId = regeneratingMessageId.value
  regeneratingMessageId.value = null
  
  try {
    const result = await chatStore.regenerateMessage(
      chatStore.currentThread?.id!,
      messageId,
      chatStore.currentModel
    )
    
    if (result.success) {
      // 成功开始重新生成
      // 不需要额外提示，因为流式生成指示器会显示
    } else {
      showToast(result.error || '重新生成失败', 'error')
    }
  } catch (error) {
    console.error('重新生成失败:', error)
    showToast('重新生成失败', 'error')
  }
}

/**
 * 取消重新生成消息
 */
const cancelRegenerateMessage = () => {
  showRegenerateConfirm.value = false
  regeneratingMessageId.value = null
}

/**
 * 删除消息
 */
const deleteMessage = async (messageId: number) => {
  if (isStreaming.value) {
    showToast('请等待当前生成完成', 'error')
    return
  }
  
  // 验证消息是否存在
  try {
    const isValid = await validateMessageExists(messageId)
    if (!isValid) {
      showToast('消息不存在或已被删除', 'error')
      return
    }
  } catch (error) {
    console.error('验证消息失败:', error)
    showToast('验证消息失败，请稍后重试', 'error')
    return
  }
  
  if (chatStore.isMessageBranchingPoint(messageId)) {
    showToast('此消息已被分支引用，无法删除', 'error')
    return
  }

  // 设置要删除的消息ID，并显示确认对话框
  deletingMessageId.value = messageId
  showDeleteMessageConfirm.value = true
}

/**
 * 验证消息是否存在
 */
const validateMessageExists = async (messageId: number): Promise<boolean> => {
  if (!currentThread.value) {
    console.warn('验证消息失败：当前没有活跃的线程')
    return false
  }
  
  try {
    const localMessage = messages.value.find(msg => msg.id === messageId)
    if (localMessage) {
      return true
    }
    
    await chatStore.fetchMessages()
    
    const refreshedMessage = messages.value.find(msg => msg.id === messageId)
    return !!refreshedMessage
  } catch (err) {
    console.error('验证消息存在失败:', err)
    return false
  }
}

/**
 * 确认删除消息
 */
const confirmDeleteMessage = async () => {
  if (deletingMessageId.value === null) {
    return
  }
  
  try {
    if (!currentThread.value) {
      showToast('当前没有活跃的线程', 'error')
      return
    }

    const result = await chatStore.deleteMessage(currentThread.value.id, deletingMessageId.value)
    
    if (result.success) {
      showToast('消息删除成功', 'success')
      scrollToBottom()
    } else {
      showToast(result.error || '删除失败', 'error')
    }
  } catch (error) {
    console.error('删除消息失败:', error)
    const errorMsg = error instanceof Error ? error.message : '删除消息失败'
    showToast(errorMsg, 'error')
  } finally {
    // 重置状态
    showDeleteMessageConfirm.value = false
    deletingMessageId.value = null
  }
}

/**
 * 取消删除消息
 */
const cancelDeleteMessage = () => {
  showDeleteMessageConfirm.value = false
  deletingMessageId.value = null
}

// ---------- 工具函数 ----------
/**
 * 滚动到底部
 */
const scrollToBottom = () => {
  chatMessagesRef.value?.scrollToBottom()
}

// ---------- 生命周期与侦听器 ----------
onMounted(async () => {
  console.log('ChatView 组件挂载')
  
  try {
    await chatStore.initialize()
    await chatStore.fetchConversations()
    
    if (chatStore.conversations.length === 0) {
      console.log('没有对话，创建默认对话')
      await chatStore.createConversation('欢迎对话')
    } else if (!chatStore.currentConversation) {
      console.log('有对话但没有当前对话，切换到第一个')
      await chatStore.switchConversation(chatStore.conversations[0]!.id)
    }
    console.log('初始化完成，当前对话:', chatStore.currentConversation?.id)
  } catch (error) {
    console.error('初始化失败:', error)
  }
  
  nextTick(() => {
    messageInputRef.value?.focusInput()
  })
  
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 当消息列表变化时，自动滚动到底部
watch(messages, () => {
  nextTick(() => {
    scrollToBottom()
  })
}, { deep: true })
</script>

<style scoped>
/* 全局布局样式保持不变 */
.chat-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  color: #333;
  overflow: hidden;
}

/* 主聊天区域样式保持不变 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  min-width: 0;
  overflow: hidden;
  width: 100%;
  transition: all 0.3s ease;
}

/* 侧边栏收起时调整主区域 */
.chat-container:has(.left-sidebar.collapsed) .main-content,
.chat-container:has(.right-sidebar.collapsed) .main-content {
  width: calc(100% - 48px);
}

.chat-container:has(.left-sidebar.collapsed.right-sidebar.collapsed) .main-content {
  width: calc(100% - 96px);
}

/* 侧边栏收起时调整内边距 */
.left-sidebar.collapsed ~ .main-content .messages-container,
.right-sidebar.collapsed ~ .main-content .messages-container {
  padding-left: 32px;
  padding-right: 32px;
}

.left-sidebar.collapsed.right-sidebar.collapsed ~ .main-content .messages-container {
  padding-left: 40px;
  padding-right: 40px;
}

/* 保留流式生成指示器、思考指示器、按钮通用样式、对话上下文菜单、模态对话框、Toast提示、动画等样式 */
/* 这些样式不变，保持原样 */
/* ... */

/* ==================== 通用侧边栏样式 ==================== */
/* 侧边栏通用样式 - 保留 */
.sidebar {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  z-index: 10;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
}

/* 左侧边栏收起按钮特殊样式 - 保留 */
.left-sidebar .btn-toggle-sidebar {
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
}

.left-sidebar .btn-toggle-sidebar:hover {
  background: rgba(139, 92, 246, 0.2);
  color: #7c3aed;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
}

/* 右侧边栏收起按钮特殊样式 - 保留 */
.right-sidebar .btn-toggle-sidebar {
  background: rgba(14, 165, 233, 0.1);
  color: #0ea5e9;
}

.right-sidebar .btn-toggle-sidebar:hover {
  background: rgba(14, 165, 233, 0.2);
  color: #0284c7;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.2);
}

/* 收起按钮样式 - 保留基本样式 */
.btn-toggle-sidebar {
  width: 36px;
  height: 36px;
  border: none;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: #3b82f6;
  padding: 0;
  flex-shrink: 0;
  backdrop-filter: blur(4px);
}

.btn-toggle-sidebar:hover {
  background: rgba(59, 130, 246, 0.2);
  color: #2563eb;
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.btn-toggle-sidebar:active {
  transform: scale(0.95);
}

.sidebar-icon {
  transition: transform 0.3s ease;
}

.btn-toggle-sidebar:hover .sidebar-icon {
  transform: scale(1.1);
}

.icon {
  font-size: 16px;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>

<!-- 添加全局样式，用于Teleport到body的元素 -->
<style>
/* 对话上下文菜单样式 - 必须放在全局样式或非scoped样式中 */
.conversation-context-menu {
  position: fixed;
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  z-index: 10000;
  min-width: 140px;
  overflow: hidden;
  animation: menuFadeIn 0.2s ease;
  backdrop-filter: blur(8px);
}

.conversation-context-menu .menu-content {
  display: flex;
  flex-direction: column;
  padding: 6px 0;
}

.conversation-context-menu .menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: #374151;
  font-size: 13px;
  font-weight: 400;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s ease;
  outline: none;
}

.conversation-context-menu .menu-item:hover {
  background: rgba(0, 0, 0, 0.05);
}

.conversation-context-menu .menu-item.delete-item {
  color: #dc2626;
}

.conversation-context-menu .menu-item.delete-item:hover {
  background: rgba(220, 38, 38, 0.1);
}

.conversation-context-menu .menu-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

@keyframes menuFadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>