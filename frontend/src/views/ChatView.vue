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

    <!-- 在侧边栏顶部添加调试信息 -->
    <div v-if="false" style="position: fixed; top: 10px; right: 10px; background: red; color: white; padding: 10px; z-index: 9999;">
      <div>isLoading: {{ isLoading }}</div>
      <div>对话数量: {{ conversations.length }}</div>
      <div>当前对话: {{ currentConversation?.id }}</div>
    </div>
    
    <!-- 左侧边栏：对话列表 -->
    <aside class="sidebar left-sidebar" :class="{ 'collapsed': isLeftSidebarCollapsed }">
      <div class="sidebar-header">
        <h2>AI对话</h2>
        <div class="sidebar-header-actions">
          <!-- 在非收起状态下显示新建对话按钮 -->
          <button v-if="!isLeftSidebarCollapsed" class="btn-new-chat" @click="createNewConversation" title="新对话">
            <span class="icon">+</span> 新对话
          </button>
          <!-- 收起按钮始终显示 -->
          <button class="btn-toggle-sidebar" @click="toggleLeftSidebar" :title="isLeftSidebarCollapsed ? '展开侧边栏' : '收起侧边栏'">
            <span v-if="isLeftSidebarCollapsed" class="icon">▶</span>
            <span v-else class="icon">◀</span>
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
              @blur="saveConversationTitle(conv.id)"
              @keyup.enter="saveConversationTitle(conv.id)"
              @keyup.esc="cancelEditConversationTitle"
            />
            <span v-else class="conv-title">
              {{ conv.title || '未命名对话' }}
            </span>
          </div>
          
          <span class="conv-time">{{ formatTime(conv.updated_at) }}</span>
          
          <!-- 三点菜单按钮 -->
          <button 
            class="conversation-menu-btn"
            @click.stop="showConversationMenu(conv, $event)"
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
      
      <!-- 新增：AI用量信息 -->
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
        <div class="usage-date">重置时间: {{ aiUsage.current_date }}</div>
      </div>
      
      <div class="sidebar-footer">
        <div class="user-avatar">U</div>
        <div class="user-info">
          <div class="username">开发者</div>
          <div class="user-email">dev@example.com</div>
        </div>
      </div>
    </aside>

    <!-- 主聊天区域 -->
    <main class="main-content">
      <!-- 当前对话/线程的标题栏 -->
      <div class="chat-header">
        <div class="chat-title">
          <h3>{{ currentConversation?.title || '新对话' }}</h3>
          <div class="thread-path" v-if="currentThread">
            <span v-for="(thread, idx) in threadPath" :key="thread.id">
              <span class="path-segment" @click="switchThread(thread.id)">{{ thread.title || `分支-${idx+1}` }}</span>
              <span v-if="idx < threadPath.length - 1" class="path-arrow"> › </span>
            </span>
          </div>
        </div>
        <div class="chat-actions">
          <!-- 新增：模型选择器 -->
          <div class="model-selector" v-if="availableModels.length > 0">
            <select v-model="currentModel" @change="onModelChange" class="model-select">
              <option 
                v-for="model in availableModels" 
                :key="model" 
                :value="model"
                :disabled="model === '模拟模式' && !isMockModeAvailable"
              >
                {{ getModelDisplayName(model) }}
              </option>
            </select>
          </div>
          <button class="btn-icon" title="刷新用量" @click="refreshUsage">
            <span class="icon">🔄</span>
          </button>
        </div>
      </div>

      <!-- 消息列表区域 -->
      <div class="messages-container" ref="messagesContainer">
        <div v-for="msg in messages" :key="msg.id" class="message-wrapper" :class="msg.role">
          <div class="message-avatar">
            {{ msg.role === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="message-content">
            <div class="message-meta">
              <span class="message-role">{{ msg.role === 'user' ? '您' : 'AI助手' }}</span>
              <span class="message-time">{{ formatTime(msg.created_at) }}</span>
              <span v-if="msg.model_used" class="message-model">({{ getModelDisplayName(msg.model_used) }})</span>
            </div>
            <div class="message-text" v-html="formatMessage(msg.content)"></div>
            <!-- 在消息操作区域 -->
            <div class="message-actions" v-if="msg.role === 'assistant'">
              <!-- 复制按钮 -->
              <button 
                class="btn-action copy-btn"
                @click="copyMessage(msg.content)"
                title="复制消息"
              >
                <svg class="action-icon" viewBox="0 0 24 24" width="16" height="16">
                  <path fill="currentColor" d="M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z"/>
                </svg>
              </button>
              <!-- 重新生成按钮 -->
              <button 
                class="btn-action regenerate-btn"
                @click="regenerateMessage(msg.id)"
                title="重新生成"
                :disabled="isStreaming"
              >
                <svg class="action-icon" viewBox="0 0 24 24" width="16" height="16">
                  <path fill="currentColor" d="M12,5V1L7,6L12,11V7A6,6 0 0,1 18,13A6,6 0 0,1 12,19A6,6 0 0,1 6,13H4A8,8 0 0,0 12,21A8,8 0 0,0 20,13A8,8 0 0,0 12,5Z"/>
                </svg>
              </button>
              <!-- 分支按钮 -->
              <button 
                class="btn-action branch-btn"
                @click="createBranchFromMessage(msg.id)"
                :disabled="!canCreateBranch(msg) || isStreaming"
                :title="getBranchButtonTitle(msg)"
              >
                <svg class="action-icon" viewBox="0 0 24 24" width="16" height="16">
                  <path fill="currentColor" d="M9.5,3A2.5,2.5 0 0,1 12,5.5A2.5,2.5 0 0,1 9.5,8A2.5,2.5 0 0,1 7,5.5A2.5,2.5 0 0,1 9.5,3M14.5,3A2.5,2.5 0 0,1 17,5.5A2.5,2.5 0 0,1 14.5,8A2.5,2.5 0 0,1 12,5.5A2.5,2.5 0 0,1 14.5,3M9.5,9C11,9 12,10 12,11.5C12,13 11,14 9.5,14C8,14 7,13 7,11.5C7,10 8,9 9.5,9M14.5,9C16,9 17,10 17,11.5C17,13 16,14 14.5,14C13,14 12,13 12,11.5C12,10 13,9 14.5,9M4.5,13A2.5,2.5 0 0,1 7,15.5A2.5,2.5 0 0,1 4.5,18A2.5,2.5 0 0,1 2,15.5A2.5,2.5 0 0,1 4.5,13M19.5,13A2.5,2.5 0 0,1 22,15.5A2.5,2.5 0 0,1 19.5,18A2.5,2.5 0 0,1 17,15.5A2.5,2.5 0 0,1 19.5,13Z"/>
                </svg>
              </button>
              <!-- 新增：删除按钮 -->
              <button 
                class="btn-action delete-btn"
                @click="deleteMessage(msg.id)"
                :disabled="isStreaming"
                title="删除此消息及其上下文"
              >
                <svg class="action-icon" viewBox="0 0 24 24" width="16" height="16">
                  <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
        <!-- 修改：流式生成指示器 -->
        <div v-if="isStreaming" class="streaming-indicator">
          <div class="streaming-dots">
            <span></span><span></span><span></span>
          </div>
          <div class="streaming-text">{{ streamingModel ? getModelDisplayName(streamingModel) : 'AI' }}正在生成...</div>
          <button class="btn-stop" @click="stopGenerating" title="停止生成">
            停止
          </button>
        </div>
        <div v-else-if="isLoading" class="thinking-indicator">
          <div class="thinking-dots">
            <span></span><span></span><span></span>
          </div>
          <div class="thinking-text">AI正在思考...</div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-container">
        <!-- 新增：Token用量警告 -->
        <div v-if="isTokenLimitReached" class="token-limit-warning">
          <span class="warning-icon">⚠️</span>
          <span class="warning-text">当日API用量已达上限，请明日再试</span>
        </div>
        <!-- 添加相对定位的包装器，用于放置深度提示 -->
  <div class="input-wrapper">
    <!-- 深度提示组件 -->
    <BranchDepthHint 
      v-if="currentThread"
      :currentDepth="currentThread.depth || 0"
      :maxDepth="3"
    />
    
    <div class="input-area-wrapper">
      <textarea
        v-model="userInput"
        :placeholder="getInputPlaceholder()"
        @keydown.enter.exact.prevent="sendMessage"
        @keydown.shift.enter.exact="userInput += '\n'"
        :disabled="isLoading || isStreaming || isTokenLimitReached"
        rows="1"
        ref="inputTextarea"
        class="message-input"
        @input="autoResizeTextarea"
      ></textarea>
      <div class="send-controls">
        <!-- 新增：流式控制开关 -->
        <div class="streaming-toggle" title="流式响应">
          <input
            type="checkbox"
            id="streaming-toggle"
            v-model="streamingEnabled"
            :disabled="isLoading || isStreaming"
            class="toggle-checkbox"
          />
          <label for="streaming-toggle" class="toggle-label">
            <span class="toggle-text">流式</span>
          </label>
        </div>
        <button
          class="btn-send"
          @click="sendMessage"
          :disabled="!canSendMessage"
          :class="{ 
            disabled: !canSendMessage,
            streaming: isStreaming
          }"
          :title="getSendButtonTitle()"
        >
          <span v-if="isStreaming" class="icon stop-icon" title="停止生成">⏹️</span>
          <span v-else class="icon send-icon">⬆</span>
        </button>
      </div>
    </div>
  </div>
  
  <div class="input-footer">
    <div class="model-info">
      当前模型: <strong>{{ getModelDisplayName(currentModel) }}</strong>
      <span v-if="streamingEnabled" class="streaming-badge">流式</span>
      <span v-else class="streaming-badge off">非流式</span>
    </div>
    <div class="input-hints">
      <span class="hint">对话ID: {{ currentConversation?.id || '--' }}</span>
      <span class="hint">线程ID: {{ currentThread?.id || '--' }}</span>
      <span v-if="isTokenLimitReached" class="hint warning">用量已达上限</span>
      <span v-else-if="aiUsage" class="hint">剩余: {{ formatNumber(aiUsage.remaining_tokens) }} tokens</span>
    </div>
  </div>
</div>
       
    </main>

    <!-- 右侧边栏：分支树 -->
    <aside class="sidebar right-sidebar" :class="{ 'collapsed': isRightSidebarCollapsed }">
      <div class="sidebar-header">
        <h3>分支树</h3>
        <div class="sidebar-header-actions">
          <!-- 在非收起状态下显示刷新按钮 -->
          <button v-if="!isRightSidebarCollapsed" class="btn-icon" @click="refreshThreadTree" title="刷新" :disabled="isStreaming">
            <span class="icon">🔄</span>
          </button>
          <!-- 收起按钮始终显示 -->
          <button class="btn-toggle-sidebar" @click="toggleRightSidebar" :title="isRightSidebarCollapsed ? '展开侧边栏' : '收起侧边栏'">
            <span v-if="isRightSidebarCollapsed" class="icon">◀</span>
            <span v-else class="icon">▶</span>
          </button>
       </div>
      </div>
      <div class="thread-tree">
        <div v-if="threadTree.length === 0" class="empty-tip">
          当前对话暂无分支
        </div>
        <ThreadTreeNode
          v-for="thread in threadTree"
          :key="thread.id"
          :thread="thread"
          :current-thread-id="currentThread?.id"
          @switch="switchThread"
        />
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed, onBeforeUnmount } from 'vue'
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chat'
import ThreadTreeNode from '@/components/ThreadTreeNode.vue'
import type { Conversation, Message } from '@/types/chat'
import BranchDepthHint from '@/components/BranchDepthHint.vue'

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
const messagesContainer = ref<HTMLElement>()
const inputTextarea = ref<HTMLTextAreaElement>()
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

// ---------- 计算属性 ----------
const canSendMessage = computed(() => {
  return userInput.value.trim() && !isLoading.value && !isTokenLimitReached.value
})

const isMockModeAvailable = computed(() => {
  return availableModels.value.includes('模拟模式')
})

// ---------- 方法 ----------
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
  
  editingConversationId.value = conversation.id
  editingTitle.value = conversation.title || ''
  nextTick(() => {
    titleInput.value?.focus()
    titleInput.value?.select()
  })
}

// 处理菜单删除点击
const handleDeleteClick = () => {
  if (!conversationMenu.value.conversation) return
  
  const conversation = conversationMenu.value.conversation
  hideConversationMenu()
  
  if (isStreaming.value) {
    showToast('请等待生成完成后再删除对话', 'error')
    return
  }
  
  deletingConversationId.value = conversation.id
  deletingConversationTitle.value = conversation.title || ''
  showDeleteConfirm.value = true
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
  // 如果正在编辑，不切换对话
  if (editingConversationId.value === convId) return
  
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
    })
  } catch (error) {
    console.error('发送消息失败:', error)
    // 错误信息已在store中处理
  } finally {
    // 保持输入框焦点
    inputTextarea.value?.focus()
  }
}

// 停止生成
const stopGenerating = async () => {
  await chatStore.stopStreaming()
}

// 刷新用量信息
const refreshUsage = async () => {
  await chatStore.fetchAIUsage()
  showToast('用量信息已刷新', 'success')
}

// 模型变更处理
const onModelChange = () => {
  chatStore.setCurrentModel(currentModel.value)
  showToast(`已切换到模型: ${getModelDisplayName(currentModel.value)}`, 'success')
}

// 获取模型显示名称
const getModelDisplayName = (model: string) => {
  return chatStore.getModelDisplayName(model)
}

// 获取输入框提示文本
const getInputPlaceholder = (): string => {
  if (isTokenLimitReached.value) {
    return '当日API用量已达上限，请明日再试'
  }
  if (isStreaming.value) {
    return 'AI正在生成，请稍后...'
  }
  return '发送消息给AI... (Shift+Enter换行，Enter发送)'
}

// 获取发送按钮提示
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

// 数字格式化
const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
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

const canCreateBranch = (msg: Message) => {
  if (isStreaming.value) return false
  if (msg.role !== 'assistant') return false
  if (currentThread.value?.depth !== undefined && currentThread.value.depth >= 3) {
    return false
  }
  const latestMessage = getLatestMessage()
  if (!latestMessage) return false
  return msg.id === latestMessage.id
}

const getBranchButtonTitle = (msg: Message) => {
  if (isStreaming.value) {
    return '请等待生成完成'
  }
  if (msg.role !== 'assistant') {
    return '只能在AI回复处创建分支'
  }
  if (currentThread.value?.depth !== undefined && currentThread.value.depth >= 3) {
    return '分支深度已达上限（3层）'
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

// ---------- 消息操作方法 ----------
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

const regenerateMessage = (messageId: number) => {
  if (isStreaming.value) {
    showToast('请等待当前生成完成', 'error')
    return
  }
  console.log('重新生成消息:', messageId)
  alert('重新生成功能待实现')
}

// 新增：删除消息
const deleteMessage = async (messageId: number) => {
  if (isStreaming.value) {
    showToast('请等待当前生成完成', 'error')
    return
  }
  
  if (!confirm('确定要删除这条消息及其上下文吗？此操作不可恢复。')) {
    return
  }
  
  try {
    // 记录要删除的消息ID，便于后续调试
    console.log('尝试删除消息，ID:', messageId)
    
    // 查找当前消息在消息列表中的索引
    const messageIndex = messages.value.findIndex(msg => msg.id === messageId)
    if (messageIndex === -1) {
      throw new Error('消息不存在')
    }
    
    const messageToDelete = messages.value[messageIndex]
    console.log('要删除的消息:', messageToDelete)
    
    // 这里调用store的删除消息方法
    // 注意：删除功能需要后端支持，这里先模拟实现
    // 实际实现应该是：
    // await chatStore.deleteMessage(messageId)
    
    // 模拟删除成功
    showToast('消息删除功能开发中，后端API就绪后即可使用', 'success')
    
  } catch (error) {
    console.error('删除消息失败:', error)
    showToast('删除功能开发中，后端API就绪后即可使用', 'error')
  }
}

// ---------- 工具函数 ----------
const formatTime = (timestamp: string | Date | undefined): string => {
  if (!timestamp) return '--'
  const date = new Date(timestamp)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const formatMessage = (content: string): string => {
  return content.replace(/\n/g, '<br>')
}

const autoResizeTextarea = () => {
  const textarea = inputTextarea.value
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = (textarea.scrollHeight) + 'px'
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    nextTick(() => {
      messagesContainer.value!.scrollTop = messagesContainer.value!.scrollHeight
    })
  }
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
  inputTextarea.value?.focus()
  
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

// 当流式状态变化时，可能需要调整UI
watch(isStreaming, (newVal) => {
  if (!newVal) {
    // 流式生成结束，重置输入框状态
    nextTick(() => {
      inputTextarea.value?.focus()
    })
  }
})

// ---------- 对话标题编辑相关状态 ----------
const editingConversationId = ref<number | null>(null)
const editingTitle = ref('')
const titleInput = ref<HTMLInputElement>()

// ---------- 对话标题编辑方法 ----------
const saveConversationTitle = async (conversationId: number) => {
  if (editingTitle.value.trim() && editingConversationId.value === conversationId) {
    try {
      await chatStore.updateConversationTitle(conversationId, editingTitle.value.trim())
    } catch (error) {
      console.error('更新标题失败:', error)
    }
  }
  cancelEditConversationTitle()
}

const cancelEditConversationTitle = () => {
  editingConversationId.value = null
  editingTitle.value = ''
}

// ---------- 删除对话相关状态 ----------
const showDeleteConfirm = ref(false)
const deletingConversationId = ref<number | null>(null)
const deletingConversationTitle = ref('')

// ---------- Toast提示相关 ----------
const toast = ref({
  show: false,
  message: '',
  type: 'success' as 'success' | 'error'
})

// Toast提示方法
const showToast = (message: string, type: 'success' | 'error' = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
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
</script>

<style scoped>
/* ==================== 全局布局 ==================== */
.chat-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  color: #333;
  overflow: hidden;
}

/* ==================== 侧边栏样式 ==================== */
/* 侧边栏通用样式 */
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

/* 左侧边栏 */
.left-sidebar {
  width: 320px;
  min-width: 320px;
  border-right: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.08);
}

/* 右侧边栏 */
.right-sidebar {
  width: 380px;
  min-width: 380px;
  border-left: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.08);
}

/* 侧边栏收起状态 */
.left-sidebar.collapsed {
  width: 48px;
  min-width: 48px;
  overflow: visible;
}

.right-sidebar.collapsed {
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

.right-sidebar.collapsed .sidebar-header h3,
.right-sidebar.collapsed .thread-tree,
.right-sidebar.collapsed .btn-icon:not(.btn-toggle-sidebar) {
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

.sidebar-header h2, .sidebar-header h3 {
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
.conversations-list, .thread-tree {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  min-height: 0;
}

.thread-tree {
  padding: 12px 20px;
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

/* ==================== 对话列表样式 ==================== */
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

/* ==================== 对话上下文菜单 ==================== */
.conversation-context-menu {
  position: fixed;
  z-index: 9999;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 4px 0;
  animation: slideIn 0.2s ease;
  overflow: hidden;
  min-width: 120px;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.menu-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.menu-item {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 8px 12px;
  border: none;
  background: none;
  text-align: left;
  font-size: 12px;
  color: #374151;
  cursor: pointer;
  transition: background-color 0.2s ease;
  gap: 8px;
  white-space: nowrap;
}

.menu-item:hover {
  background-color: #f3f4f6;
}

.menu-item.delete-item {
  color: #dc2626;
}

.menu-item.delete-item:hover {
  background-color: rgba(220, 38, 38, 0.1);
  color: #dc2626;
}

.menu-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: #6b7280;
}

.menu-item:hover .menu-icon {
  color: #374151;
}

.menu-item.delete-item .menu-icon {
  color: #dc2626;
}

/* ==================== 主聊天区域样式 ==================== */
/* 主内容区域 */
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

/* 聊天头部 */
.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.95);
  flex-shrink: 0;
  width: 100%;
  transition: padding 0.3s ease;
}

/* 侧边栏收起时调整内边距 */
.left-sidebar.collapsed ~ .main-content .chat-header,
.right-sidebar.collapsed ~ .main-content .chat-header {
  padding-left: 32px;
  padding-right: 32px;
}

.left-sidebar.collapsed.right-sidebar.collapsed ~ .main-content .chat-header {
  padding-left: 40px;
  padding-right: 40px;
}

.chat-title h3 {
  margin: 0 0 6px 0;
  font-size: 18px;
  color: #202123;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

/* 侧边栏收起时，允许标题显示更多内容 */
.left-sidebar.collapsed ~ .main-content .chat-title h3,
.right-sidebar.collapsed ~ .main-content .chat-title h3 {
  max-width: 500px;
}

.left-sidebar.collapsed.right-sidebar.collapsed ~ .main-content .chat-title h3 {
  max-width: 600px;
}

.thread-path {
  font-size: 13px;
  color: #666;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.path-segment {
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: background 0.2s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
  display: inline-block;
}

.path-segment:hover {
  background: rgba(0, 0, 0, 0.06);
  text-decoration: underline;
}

.path-arrow {
  color: #999;
  user-select: none;
}

.chat-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 模型选择器 */
.model-selector {
  position: relative;
}

.model-select {
  padding: 8px 12px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  background: white;
  color: #333;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  cursor: pointer;
  transition: border 0.2s, box-shadow 0.2s;
  min-width: 140px;
}

.model-select:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.model-select option:disabled {
  color: #999;
  background: #f5f5f5;
}

/* 消息容器 */
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

/* 消息包装器 */
.message-wrapper {
  display: flex;
  gap: 16px;
  max-width: 100%;
  width: 100%;
  margin: 0 auto;
  transition: all 0.3s ease;
}

/* 侧边栏状态变化时调整消息宽度 */
.left-sidebar.collapsed ~ .main-content .message-wrapper,
.right-sidebar.collapsed ~ .main-content .message-wrapper {
  max-width: 90%;
}

.left-sidebar.collapsed.right-sidebar.collapsed ~ .main-content .message-wrapper {
  max-width: 95%;
}

.message-wrapper.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-wrapper.user .message-content {
  align-items: flex-end;
}

/* 消息头像 */
.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 4px;
}

.user .message-avatar {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.assistant .message-avatar {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

/* 消息内容 */
.message-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 100%;
}

.message-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
  flex-wrap: wrap;
  gap: 8px;
}

.message-role {
  font-weight: 600;
  white-space: nowrap;
}

.user .message-role {
  color: #3b82f6;
}

.assistant .message-role {
  color: #10b981;
}

/* 消息文本 */
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
  max-width: 100%;
}

.user .message-text {
  background: #3b82f6;
  color: white;
  border: none;
  border-bottom-right-radius: 4px;
}

.assistant .message-text {
  border-bottom-left-radius: 4px;
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

.user .message-actions {
  display: none;
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

/* ==================== 输入区域样式 ==================== */
.input-container {
  padding: 20px 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.95);
  flex-shrink: 0;
  width: 100%;
  transition: padding 0.3s ease;
}

/* 侧边栏收起时调整内边距 */
.left-sidebar.collapsed ~ .main-content .input-container,
.right-sidebar.collapsed ~ .main-content .input-container {
  padding-left: 32px;
  padding-right: 32px;
}

.left-sidebar.collapsed.right-sidebar.collapsed ~ .main-content .input-container {
  padding-left: 40px;
  padding-right: 40px;
}

.input-area-wrapper {
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: 12px;
  max-width: 100%;
  margin: 0 auto;
  width: 100%;
  transition: max-width 0.3s ease;
}

/* 侧边栏状态变化时调整输入区域宽度 */
.left-sidebar.collapsed ~ .main-content .input-area-wrapper,
.right-sidebar.collapsed ~ .main-content .input-area-wrapper {
  max-width: 90%;
}

.left-sidebar.collapsed.right-sidebar.collapsed ~ .main-content .input-area-wrapper {
  max-width: 95%;
}

.message-input {
  flex: 1;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 12px;
  padding: 16px 20px;
  font-size: 15px;
  line-height: 1.5;
  resize: none;
  max-height: 200px;
  transition: border 0.2s, box-shadow 0.2s;
  background: white;
  outline: none;
  font-family: inherit;
  min-height: 56px;
  width: 100%;
}

.message-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.message-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.send-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

/* 流式控制开关 */
.streaming-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-right: 4px;
}

.toggle-checkbox {
  display: none;
}

.toggle-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
  user-select: none;
}

.toggle-checkbox:checked + .toggle-label {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
  color: #10b981;
}

.toggle-text {
  font-size: 12px;
  font-weight: 500;
}

.streaming-badge {
  display: inline-block;
  padding: 2px 6px;
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  margin-left: 6px;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.streaming-badge.off {
  background: rgba(156, 163, 175, 0.1);
  color: #6b7280;
  border-color: rgba(156, 163, 175, 0.2);
}

/* 发送按钮 */
.btn-send {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: #3b82f6;
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
  flex-shrink: 0;
  font-size: 18px;
}

.btn-send:hover:not(.disabled) {
  background: #2563eb;
  transform: translateY(-1px);
}

.btn-send:active:not(.disabled) {
  transform: scale(0.95);
}

.btn-send.disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* 输入页脚 */
.input-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  font-size: 12px;
  color: #888;
  flex-wrap: wrap;
  gap: 8px;
}

.model-info {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.model-info strong {
  color: #10b981;
}

.input-hints {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* Token限制警告 */
.token-limit-warning {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 8px;
  margin-bottom: 12px;
  color: #dc2626;
  font-size: 13px;
  animation: slideDown 0.3s ease;
}

.warning-icon {
  font-size: 16px;
}

.warning-text {
  flex: 1;
  font-weight: 500;
}

/* ==================== 加载指示器 ==================== */
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

/* 侧边栏状态变化时调整流式指示器宽度 */
.left-sidebar.collapsed ~ .main-content .streaming-indicator,
.right-sidebar.collapsed ~ .main-content .streaming-indicator {
  max-width: 90%;
}

.left-sidebar.collapsed.right-sidebar.collapsed ~ .main-content .streaming-indicator {
  max-width: 95%;
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

/* ==================== 按钮通用样式 ==================== */
button {
  border: none;
  background: none;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
  outline: none;
}

button:hover {
  background: rgba(0, 0, 0, 0.06);
  transform: translateY(-1px);
}

button:active {
  transform: translateY(0);
}

.btn-icon {
  padding: 8px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  min-height: 36px;
  color: #666;
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.btn-icon:hover {
  background: rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.12);
  color: #333;
}

.btn-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.btn-icon:disabled:hover {
  background: rgba(0, 0, 0, 0.04);
  transform: none;
}

.icon {
  font-size: 16px;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.icon.loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 收起/展开按钮样式 */
.btn-toggle-sidebar {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #666;
  font-size: 16px;
  padding: 0;
  flex-shrink: 0;
}

.btn-toggle-sidebar:hover {
  background: rgba(0, 0, 0, 0.1);
  color: #333;
  transform: scale(1.1);
}

/* 新对话按钮 */
.btn-new-chat {
  background: #3b82f6;
  color: white;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.btn-new-chat:hover {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.btn-new-chat:active {
  transform: translateY(0);
}

/* ==================== 弹窗和提示 ==================== */
/* 模态对话框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99999;
  animation: fadeIn 0.3s ease;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease;
}

.modal-content h3 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 18px;
  font-weight: 600;
}

.modal-content p {
  margin: 0 0 20px 0;
  color: #666;
  line-height: 1.5;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-cancel, .btn-delete {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
  font-size: 13px;
}

.btn-cancel {
  background: rgba(0, 0, 0, 0.05);
  color: #333;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.btn-cancel:hover {
  background: rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.btn-delete {
  background: #ef4444;
  color: white;
  border: 1px solid #dc2626;
}

.btn-delete:hover {
  background: #dc2626;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
}

/* Toast提示 */
.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: #333;
  color: white;
  padding: 12px 20px;
  border-radius: 8px;
  z-index: 99999;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease;
  font-size: 13px;
  font-weight: 500;
  max-width: 400px;
  text-align: center;
  word-break: break-word;
}

.toast.success {
  background: #10b981;
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
}

.toast.error {
  background: #ef4444;
  box-shadow: 0 8px 24px rgba(239, 68, 68, 0.3);
}

/* ==================== 动画 ==================== */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    transform: translateX(-50%) translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
  }
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

/* ==================== 响应式设计 ==================== */
/* 在大屏幕上增加消息最大宽度 */
@media (min-width: 1400px) {
  .message-wrapper {
    max-width: 900px;
  }
  
  .left-sidebar.collapsed ~ .main-content .message-wrapper,
  .right-sidebar.collapsed ~ .main-content .message-wrapper {
    max-width: 1000px;
  }
  
  .left-sidebar.collapsed.right-sidebar.collapsed ~ .main-content .message-wrapper {
    max-width: 1200px;
  }
  
  .input-area-wrapper {
    max-width: 900px;
  }
  
  .left-sidebar.collapsed ~ .main-content .input-area-wrapper,
  .right-sidebar.collapsed ~ .main-content .input-area-wrapper {
    max-width: 1000px;
  }
  
  .left-sidebar.collapsed.right-sidebar.collapsed ~ .main-content .input-area-wrapper {
    max-width: 1200px;
  }
}

/* 在小屏幕上调整布局 */
@media (max-width: 768px) {
  .conversation-item {
    padding: 10px 12px 10px 8px;
  }
  
  .conv-title {
    font-size: 12px;
  }
  
  .conv-time {
    font-size: 10px;
  }
  
  .conversation-menu-btn {
    width: 24px;
    height: 24px;
  }
  
  .conversation-context-menu {
    min-width: 100px;
  }
  
  .menu-item {
    padding: 6px 10px;
    font-size: 11px;
  }
  
  .messages-container {
    padding: 16px;
  }
  
  .message-wrapper {
    gap: 12px;
  }
  
  .message-avatar {
    width: 32px;
    height: 32px;
    font-size: 18px;
  }
  
  .message-text {
    padding: 10px 14px;
    font-size: 14px;
  }
  
  .message-actions {
    gap: 6px;
  }
  
  .btn-action {
    width: 32px;
    height: 32px;
    padding: 6px;
  }
  
  .action-icon {
    width: 14px;
    height: 14px;
  }
  
  .input-container {
    padding: 16px;
  }
  
  .message-input {
    padding: 12px 16px;
    font-size: 14px;
  }
  
  .input-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}

/* 输入区域包装器 */
.input-wrapper {
  position: relative;
  width: 100%;
}
</style>