<template>
  <div class="chat-container">
    
    <!-- Toast提示 -->
    <div v-if="toast.show" class="toast" :class="toast.type">
        {{ toast.message }}
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="showDeleteConfirm" class="modal-overlay">
      <div class="modal-content">
        <h3>确认删除</h3>
        <p>确定要删除对话 "{{ deletingConversationTitle }}" 吗？此操作不可恢复。</p>
        <div class="modal-actions">
          <button class="btn-cancel" @click="cancelDelete">取消</button>
          <button class="btn-delete" @click="confirmDelete">删除</button>
        </div>
      </div>
    </div>

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
        v-model:streaming-enabled="streamingEnabled"
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
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed, onBeforeUnmount } from 'vue'
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chat'
import type { Conversation, Message } from '@/types/chat'
// 导入侧边栏组件
import ConversationSidebar from '@/components/ConversationSidebar.vue'
import ThreadTreeSidebar from '@/components/ThreadTreeSidebar.vue'
// 导入头部组件
import ChatHeader from '@/components/ChatHeader.vue'
//导入聊天组件
import ChatMessages from '@/components/ChatMessages.vue'  // 新增
// 导入工具函数
import { 
  formatNumber, 
  getModelDisplayName 
} from '@/utils/formatters'

// 导入组合式函数
import { useToast } from '@/composables/useToast'

// 导入输入组件
import MessageInput from '@/components/MessageInput.vue'

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

const {
  deleteMessage: deleteMessageInStore,
  isMessageBranchingPoint
} = chatStore

// ---------- 本地响应式数据 ----------
const userInput = ref('')
const messageInputRef = ref<InstanceType<typeof MessageInput>>()
const conversationSidebarRef = ref<InstanceType<typeof ConversationSidebar>>()
const chatMessagesRef = ref<InstanceType<typeof ChatMessages>>()  // 新增
const streamingEnabled = ref(true) // 默认启用流式
const isRightSidebarCollapsed = ref(false)
const isLeftSidebarCollapsed = ref(false)

// 对话菜单状态
const conversationMenu = ref({
  visible: false,
  conversation: null as Conversation | null,
  position: {
    top: '0px',
    left: '0px'
  }
})

// ---------- 删除对话相关状态 ----------
const showDeleteConfirm = ref(false)
const deletingConversationId = ref<number | null>(null)
const deletingConversationTitle = ref('')

// ---------- 计算属性 ----------
const canSendMessage = computed(() => {
  return !!userInput.value.trim() && !isLoading.value && !isTokenLimitReached.value
})

const isMockModeAvailable = computed(() => {
  return availableModels.value.includes('模拟模式')
})

// ---------- 侧边栏方法 ----------
const toggleRightSidebar = () => {
  isRightSidebarCollapsed.value = !isRightSidebarCollapsed.value
}

const toggleLeftSidebar = () => {
  isLeftSidebarCollapsed.value = !isLeftSidebarCollapsed.value
}

// ---------- 对话列表方法 ----------
// 显示对话菜单
const showConversationMenu = (conversation: Conversation, event: MouseEvent) => {
  event.stopPropagation()
  event.preventDefault()
  
  // 计算菜单位置（在点击位置显示）
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

// 隐藏对话菜单
const hideConversationMenu = () => {
  conversationMenu.value.visible = false
  conversationMenu.value.conversation = null
}

// 处理菜单重命名点击
const handleRenameClick = () => {
  if (!conversationMenu.value.conversation) return
  
  const conversation = conversationMenu.value.conversation
  hideConversationMenu()
  
  if (isStreaming.value) {
    showToast('请等待生成完成后再编辑标题', 'error')
    return
  }
  
  // 调用 ConversationSidebar 组件的方法开始编辑标题
  conversationSidebarRef.value?.startEditingTitle(conversation)
}

// 处理菜单删除点击
const handleDeleteClick = () => {
  if (!conversationMenu.value.conversation) return
  
  const conversation = conversationMenu.value.conversation
  hideConversationMenu()
  
  handleDeleteConversation(conversation.id)
}

// 点击外部关闭菜单
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.conversation-context-menu') && 
      !target.closest('.conversation-menu-btn') &&
      !target.closest('.modal-overlay')) {
    hideConversationMenu()
  }
}

// 对话点击处理
const handleConversationClick = async (convId: number) => {
  // 如果菜单打开，不切换对话
  if (conversationMenu.value.visible) {
    hideConversationMenu()
    return
  }
  
  await chatStore.switchConversation(convId)
  scrollToBottom()
}

const createNewConversation = async () => {
  await chatStore.createConversation('新对话')
  userInput.value = ''
  scrollToBottom()
}

// 处理删除对话
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

// 保存对话标题
const saveConversationTitle = async (conversationId: number, title: string) => {
  try {
    await chatStore.updateConversationTitle(conversationId, title)
  } catch (error) {
    console.error('更新标题失败:', error)
  }
}

// ---------- 删除对话方法 ----------
const cancelDelete = () => {
  showDeleteConfirm.value = false
  deletingConversationId.value = null
  deletingConversationTitle.value = ''
}

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
const sendMessage = async () => {
  const text = userInput.value.trim()
  if (!text || isLoading.value || isTokenLimitReached.value) return

  try {
    if (streamingEnabled.value) {
      // 使用流式发送
      await chatStore.sendMessageStream(text)
    } else {
      // 使用非流式发送
      await chatStore.sendMessage(text)
    }
    
    userInput.value = ''
    // 等待DOM更新后滚动到底部
    nextTick(() => {
      scrollToBottom()
      // 聚焦输入框
      messageInputRef.value?.focusInput()
    })
  } catch (error) {
    console.error('发送消息失败:', error)
  }
}

// ---------- 输入相关方法 ----------
const getInputPlaceholder = (): string => {
  if (isTokenLimitReached.value) {
    return '当日API用量已达上限，请明日再试'
  }
  if (isStreaming.value) {
    return 'AI正在生成，请稍后...'
  }
  return '发送消息给AI... (Shift+Enter换行，Enter发送)'
}

const getSendButtonTitle = (): string => {
  if (isTokenLimitReached.value) {
    return '用量已达上限'
  }
  if (isStreaming.value) {
    return '停止生成'
  }
  if (!userInput.value.trim()) {
    return '请输入消息'
  }
  if (streamingEnabled.value) {
    return '发送消息（流式）'
  }
  return '发送消息'
}

// 停止生成
const stopGenerating = async () => {
  await chatStore.stopStreaming()
}

// 模型变更处理
const onModelChange = () => {
  chatStore.setCurrentModel(currentModel.value)
  showToast(`已切换到模型: ${getModelDisplayName(currentModel.value)}`, 'success')
}

// ---------- 分支相关方法 ----------
const getLatestMessage = (): Message | null => {
  if (messages.value.length === 0) return null
  const latest = messages.value[messages.value.length - 1]
  return latest || null
}

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
  
  const latestMessage = getLatestMessage()
  if (!latestMessage) {
    showToast('当前没有消息，无法创建分支', 'error')
    return
  }
  
  if (messageId !== latestMessage.id) {
    showToast('只能在最新消息处创建分支', 'error')
    return
  }
  
  if (latestMessage.role !== 'assistant') {
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

const switchThread = async (threadId: number) => {
  if (isStreaming.value) {
    showToast('请等待生成完成后再切换', 'error')
    return
  }
  await chatStore.switchThread(threadId)
  scrollToBottom()
}

const refreshThreadTree = () => {
  if (isStreaming.value) {
    showToast('请等待生成完成后再刷新', 'error')
    return
  }
  chatStore.fetchThreadTree()
}

const onThreadDeleted = async (threadId: number, parentThreadId?: number | null) => {
  console.log(`线程 ${threadId} 已被删除，父线程ID: ${parentThreadId}`)
  // 可以在这里重新获取线程树或进行其他状态更新
  const chatStore = useChatStore()
  await chatStore.fetchThreadTree()  // 重新获取线程树
}

// ---------- 消息操作方法 ----------
//复制消息
const copyMessage = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content)
    showToast('消息已复制到剪贴板')
  } catch (err) {
    console.error('复制失败:', err)
    const textArea = document.createElement('textarea')
    textArea.value = content
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    showToast('消息已复制到剪贴板')
  }
}

//重新生成消息
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
  
  // 找到对应的消息对象
  const message = messages.value.find(msg => msg.id === messageId)
  if (!message) {
    showToast('消息不存在', 'error')
    return
  }
  
  // 检查是否可以重新生成（这里应该与按钮的验证一致）
  if (!canRegenerateMessage(message)) {
    const title = getRegenerateButtonTitle(message)
    showToast(title, 'error')
    return
  }
  
  // 确认操作
  if (!confirm('确定要重新生成此消息吗？')) {
    return
  }
  
  try {
    // 调用重新生成
    const result = await chatStore.regenerateMessage(
      chatStore.currentThread?.id!,
      messageId,
      chatStore.currentModel,
      true  // 默认使用流式
    )
    
    if (result.success) {
      showToast('消息重新生成中...', 'success')
    } else {
      showToast(result.error || '重新生成失败', 'error')
    }
  } catch (error) {
    console.error('重新生成失败:', error)
    showToast('重新生成失败', 'error')
  }
}

// 新增：删除消息
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
  
  // 检查消息是否被分支引用
  if (isMessageBranchingPoint(messageId)) {
    showToast('此消息已被分支引用，无法删除', 'error')
    return
  }

  // 确认对话框
  if (!confirm('确定要删除此AI回复及其对应的提问吗？此操作不可撤销。')) {
    return
  }
  
  try {
    // 记录要删除的消息ID，便于后续调试
    console.log('尝试删除消息，ID:', messageId)
    
    // 检查当前线程
    if (!currentThread.value) {
      showToast('当前没有活跃的线程', 'error')
      return
    }

    // 调用store的删除消息方法
    const result = await deleteMessageInStore(currentThread.value.id, messageId)
    
    if (result.success) {
      showToast('消息删除成功', 'success')
      console.log('删除详情:', result.data)
      
      // 滚动到底部
      scrollToBottom()
    } else {
      showToast(result.error || '删除失败', 'error')
    }
    
  } catch (error) {
    console.error('删除消息失败:', error)
    const errorMsg = error instanceof Error ? error.message : '删除消息失败'
    showToast(errorMsg, 'error')
  }
}

// 验证消息是否存在
const validateMessageExists = async (messageId: number): Promise<boolean> => {
  if (!currentThread.value) {
    console.warn('验证消息失败：当前没有活跃的线程')
    return false
  }
  
  try {
    // 首先在本地消息列表中查找
    const localMessage = messages.value.find(msg => msg.id === messageId)
    if (localMessage) {
      console.log('消息在本地找到:', messageId)
      return true
    }
    
    // 如果本地没有，尝试从服务器获取最新消息列表
    console.log('消息不在本地，重新获取消息列表:', messageId)
    await chatStore.fetchMessages()
    
    // 再次检查
    const refreshedMessage = messages.value.find(msg => msg.id === messageId)
    if (refreshedMessage) {
      console.log('消息在重新获取后找到:', messageId)
      return true
    }
    
    console.warn('消息不存在，即使在重新获取后:', messageId)
    return false
    
  } catch (err) {
    console.error('验证消息存在失败:', err)
    return false
  }
}

// 检查消息是否可以重新生成
const canRegenerateMessage = (msg: Message): boolean => {
  if (isStreaming.value) return false
  if (msg.role !== 'assistant') return false
  
  // 检查是否是最新消息
  const latestMessage = getLatestMessage()
  if (!latestMessage || latestMessage.id !== msg.id) {
    return false
  }
  
  // 检查是否被分支引用
  if (isMessageBranchingPoint(msg.id)) {
    return false
  }
  
  return true
}

// 获取重新生成按钮标题
const getRegenerateButtonTitle = (msg: Message) => {
  if (isStreaming.value) {
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
  if (isMessageBranchingPoint(msg.id)) {
    return '此消息已被分支引用，无法重新生成'
  }
  
  return '重新生成此AI回复'
}

// ---------- 工具函数 ----------
const scrollToBottom = () => {
  chatMessagesRef.value?.scrollToBottom()
}

// ---------- 生命周期与侦听器 ----------
onMounted(async () => {
  console.log('ChatView 组件挂载')
  
  try {
    // 初始化store
    await chatStore.initialize()
    
    // 1. 先获取对话列表
    await chatStore.fetchConversations()
    console.log('对话列表加载完成:', chatStore.conversations.length)
    
    // 2. 如果没有对话，创建一个默认对话
    if (chatStore.conversations.length === 0) {
      console.log('没有对话，创建默认对话')
      await chatStore.createConversation('欢迎对话')
    } else if (!chatStore.currentConversation) {
      // 3. 如果有对话但没有当前对话，切换到第一个对话
      console.log('有对话但没有当前对话，切换到第一个')
      await chatStore.switchConversation(chatStore.conversations[0]!.id)
    }
    console.log('初始化完成，当前对话:', chatStore.currentConversation?.id)
  } catch (error) {
    console.error('初始化失败:', error)
  }
  
  // 聚焦输入框
  nextTick(() => {
    messageInputRef.value?.focusInput()
  })
  
  // 监听全局点击，关闭对话菜单
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