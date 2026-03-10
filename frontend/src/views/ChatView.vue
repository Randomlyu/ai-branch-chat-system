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

    <!-- 在侧边栏顶部添加调试信息 -->
    <div v-if="false" style="position: fixed; top: 10px; right: 10px; background: red; color: white; padding: 10px; z-index: 9999;">
      <div>isLoading: {{ isLoading }}</div>
      <div>对话数量: {{ conversations.length }}</div>
      <div>当前对话: {{ currentConversation?.id }}</div>
    </div>
    
    <!-- 左侧边栏：对话列表 -->
    <aside class="sidebar left-sidebar">
      <div class="sidebar-header">
        <h2>AI对话</h2>
        <button class="btn-new-chat" @click="createNewConversation" title="新对话">
          <span class="icon">+</span> 新对话
        </button>
      </div>
      <div class="conversations-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="conversation-item"
          :class="{ active: currentConversation?.id === conv.id }"
          @click="switchConversation(conv.id)"
        >
          <span class="conv-icon">💬</span>
          <!-- 对话标题 - 双击编辑 -->
          <span 
               v-if="!editingConversation || editingConversation.id !== conv.id"
               class="conv-title"   
              @dblclick.stop="startEditConversationTitle(conv)"
            >
              {{ conv.title || '未命名对话' }}
          </span>
          <!-- 编辑输入框 -->
          <input
            v-else
            ref="titleInput"
            v-model="editingTitle"
            class="conv-title-edit"
            @blur="saveConversationTitle(conv.id)"
            @keyup.enter="saveConversationTitle(conv.id)"
            @keyup.esc="cancelEditConversationTitle"
          />
          <span class="conv-time">{{ formatTime(conv.updated_at) }}</span>
          <!-- 删除按钮 -->
          <button
          class="delete-conv-btn"
          @click.stop="confirmDeleteConversation(conv.id, conv.title)"
          title="删除对话"
          >
           <span class="icon">🗑️</span>
          </button>
        </div>
        <div v-if="conversations.length === 0" class="empty-tip">
          暂无对话，点击上方按钮开始
        </div>
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
          <button class="btn-icon" title="设置">
            <span class="icon">⚙️</span>
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
            </div>
            <div class="message-text" v-html="formatMessage(msg.content)"></div>
            <div class="message-actions" v-if="msg.role === 'assistant'">
              <button 
                  class="btn-action" 
                  @click="copyMessage(msg.content)"
                  title="复制"
                >
                  <span class="icon">📄</span>
              </button>
              <button 
                  class="btn-action" 
                  @click="regenerateMessage(msg.id)"
                  title="重新生成"
              >
                  <span class="icon">🔄</span>
              </button>
              <button 
                 class="btn-action" 
                 @click="createBranchFromMessage(msg.id)"
                 title="从此回复创建分支"
              >
                 <span class="icon">🌿</span> 分支
              </button>
            </div>
          </div>
        </div>
        <div v-if="isLoading" class="thinking-indicator">
          <div class="thinking-dots">
            <span></span><span></span><span></span>
          </div>
          <div class="thinking-text">AI正在思考...</div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-container">
        <div class="input-area-wrapper">
          <textarea
            v-model="userInput"
            placeholder="发送消息给AI... (Shift+Enter换行，Enter发送)"
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.shift.enter.exact="userInput += '\n'"
            :disabled="isLoading"
            rows="1"
            ref="inputTextarea"
            class="message-input"
            @input="autoResizeTextarea"
          ></textarea>
          <button
            class="btn-send"
            @click="sendMessage"
            :disabled="!userInput.trim() || isLoading"
            :class="{ disabled: !userInput.trim() || isLoading }"
            title="发送消息"
          >
            <span class="icon" v-if="!isLoading">⬆</span>
            <span class="icon loading" v-else>⏳</span>
          </button>
        </div>
        <div class="input-footer">
          <div class="model-info">当前模型: <strong>DeepSeek</strong></div>
          <div class="input-hints">
            <span class="hint">对话ID: {{ currentConversation?.id || '--' }}</span>
            <span class="hint">线程ID: {{ currentThread?.id || '--' }}</span>
          </div>
        </div>
      </div>
    </main>

    <!-- 右侧边栏：分支树 -->
    <aside class="sidebar right-sidebar">
      <div class="sidebar-header">
        <h3>分支树</h3>
        <button class="btn-icon" @click="refreshThreadTree" title="刷新">
          <span class="icon">🔄</span>
        </button>
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
import { ref, onMounted, nextTick, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chat'
import ThreadTreeNode from '@/components/ThreadTreeNode.vue'
import type { Conversation } from '@/types/chat'


// ---------- 状态与Store ----------
const chatStore = useChatStore()
const {
  conversations,
  currentConversation,
  currentThread,
  messages,
  isLoading,
  threadTree,
  threadPath
} = storeToRefs(chatStore)

// ---------- 本地响应式数据 ----------
const userInput = ref('')
const messagesContainer = ref<HTMLElement>()
const inputTextarea = ref<HTMLTextAreaElement>()

// ---------- 方法 ----------
const createNewConversation = async () => {
  await chatStore.createConversation('新对话')
  // 创建后会自动设为当前对话，并清空消息列表
  userInput.value = ''
  scrollToBottom()
}

const switchConversation = async (convId: number) => {
  await chatStore.switchConversation(convId)
  scrollToBottom()
}

const sendMessage = async () => {
  const text = userInput.value.trim()
  if (!text || isLoading.value) return

  await chatStore.sendMessage(text)
  userInput.value = ''
  // 等待DOM更新后滚动到底部
  nextTick(() => {
    scrollToBottom()
  })
  // 保持输入框焦点
  inputTextarea.value?.focus()
}

const createBranchFromMessage = async (messageId: number) => {
  const newThread = await chatStore.createBranch(messageId)
  if (newThread) {
    // 成功创建分支后，系统应自动切换到新线程，此处只需滚动到底部
    nextTick(() => {
      scrollToBottom()
    })
  }
}

const switchThread = async (threadId: number) => {
  await chatStore.switchThread(threadId)
  scrollToBottom()
}

const refreshThreadTree = () => {
  chatStore.fetchThreadTree()
}

// ---------- 消息操作方法 ----------
const copyMessage = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content)
    showToast('消息已复制到剪贴板')
  } catch (err) {
    console.error('复制失败:', err)
    // 降级方案
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
  // 重新生成消息的逻辑
  // 这需要后端支持重新生成特定消息的功能
  // 目前先留空，稍后实现
  console.log('重新生成消息:', messageId)
  alert('重新生成功能待实现')
}



// ---------- 工具函数 ----------
const formatTime = (timestamp: string | Date | undefined): string => {
  if (!timestamp) return '--'
  const date = new Date(timestamp)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const formatMessage = (content: string): string => {
  // 简单处理：将换行转换为<br>，实际应使用安全的Markdown渲染库
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
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// ---------- 生命周期与侦听器 ----------
onMounted(async () => {
  console.log('ChatView 组件挂载')
  
  try {
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
})

// 当消息列表变化时，自动滚动到底部
watch(messages, () => {
  nextTick(() => {
    scrollToBottom()
  })
}, { deep: true })

// ---------- 对话标题编辑相关状态 ----------
const editingConversation = ref<Conversation | null>(null)
const editingTitle = ref('')
const titleInput = ref<HTMLInputElement>()

// ---------- 对话标题编辑方法 ----------
const startEditConversationTitle = (conversation: Conversation) => {
  editingConversation.value = conversation
  editingTitle.value = conversation.title
  // 下一个tick聚焦输入框
  nextTick(() => {
    titleInput.value?.focus()
    titleInput.value?.select()
  })
}

const saveConversationTitle = async (conversationId: number) => {
  if (editingTitle.value.trim() && editingConversation.value) {
    try {
      await chatStore.updateConversationTitle(conversationId, editingTitle.value.trim())
    } catch (error) {
      console.error('更新标题失败:', error)
    }
  }
  cancelEditConversationTitle()
}

const cancelEditConversationTitle = () => {
  editingConversation.value = null
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
const confirmDeleteConversation = (convId: number, convTitle: string) => {
  deletingConversationId.value = convId
  deletingConversationTitle.value = convTitle
  showDeleteConfirm.value = true
}

const cancelDelete = () => {
  showDeleteConfirm.value = false
  deletingConversationId.value = null
  deletingConversationTitle.value = ''
}

const confirmDelete = async () => {
  if (deletingConversationId.value !== null) {
    try {
      await chatStore.deleteConversation(deletingConversationId.value)
      // 删除后重置删除状态
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
.chat-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  color: #333;
}

/* ---------- 侧边栏通用样式 ---------- */
.sidebar {
  width: 260px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  z-index: 10;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}
.right-sidebar {
  border-right: none;
  border-left: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.05);
}
.sidebar-header {
  padding: 20px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}
.sidebar-header h2, .sidebar-header h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: 600;
  color: #202123;
}
.conversations-list, .thread-tree {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 12px;
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
}
.username {
  font-weight: 600;
  font-size: 14px;
}
.user-email {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ---------- 对话项 ---------- */
.conversation-item {
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 4px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}
.conversation-item:hover {
  background: rgba(0, 0, 0, 0.04);
  border-color: rgba(0, 0, 0, 0.1);
}
.conversation-item.active {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.3);
}
.conv-icon {
  font-size: 14px;
  margin-bottom: 4px;
}
.conv-title {
  font-weight: 500;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}
.conv-time {
  font-size: 11px;
  color: #888;
  align-self: flex-start;
}
.empty-tip {
  padding: 20px 12px;
  text-align: center;
  color: #999;
  font-size: 13px;
}

/* ---------- 主聊天区域 ---------- */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  min-width: 0; /* 保证flex收缩 */
}
.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
}
.chat-title h3 {
  margin: 0 0 6px 0;
  font-size: 18px;
  color: #202123;
}
.thread-path {
  font-size: 13px;
  color: #666;
}
.path-segment {
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: background 0.2s;
}
.path-segment:hover {
  background: rgba(0, 0, 0, 0.06);
  text-decoration: underline;
}
.path-arrow {
  margin: 0 4px;
  color: #999;
}
.chat-actions {
  display: flex;
  gap: 8px;
}

/* ---------- 消息容器 ---------- */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f9f9f9;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.message-wrapper {
  display: flex;
  gap: 16px;
  max-width: 768px;
  margin: 0 auto;
  width: 100%;
}
.message-wrapper.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}
.message-wrapper.user .message-content {
  align-items: flex-end;
}
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
.message-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.message-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}
.message-role {
  font-weight: 600;
}
.user .message-role {
  color: #3b82f6;
}
.assistant .message-role {
  color: #10b981;
}
.message-text {
  line-height: 1.6;
  padding: 12px 16px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.06);
  font-size: 15px;
  word-wrap: break-word;
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
.message-actions {
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}
.message-wrapper:hover .message-actions {
  opacity: 1;
}

/* ---------- 输入区域 ---------- */
.input-container {
  padding: 20px 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.9);
}
.input-area-wrapper {
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: 12px;
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
}
.message-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
.message-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}
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
}
.btn-send:active:not(.disabled) {
  transform: scale(0.95);
}
.btn-send.disabled {
  background: #ccc;
  cursor: not-allowed;
}
.input-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  font-size: 12px;
  color: #888;
}
.model-info strong {
  color: #10b981;
}
.input-hints {
  display: flex;
  gap: 12px;
}

/* ---------- 加载指示器 ---------- */
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

/* ---------- 按钮通用样式 ---------- */
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
  transition: background 0.2s;
}
button:hover {
  background: rgba(0, 0, 0, 0.06);
}
.btn-new-chat {
  background: #3b82f6;
  color: white;
  font-weight: 500;
  width: 100%;
  justify-content: center;
}
.btn-new-chat:hover {
  background: #2563eb;
}
.btn-icon {
  padding: 6px;
  border-radius: 6px;
}
.btn-action {
  padding: 4px 8px;
  font-size: 12px;
  color: #666;
  background: rgba(0, 0, 0, 0.04);
}
.btn-action:hover {
  background: rgba(0, 0, 0, 0.08);
}
.icon {
  font-size: 16px;
  line-height: 1;
}
.icon.loading {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 标题编辑输入框样式 */
.conv-title-edit {
  flex: 1;
  border: 1px solid #3b82f6;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  background: white;
  min-width: 0;
}

.conv-title-edit:focus {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

/* 调整对话项内元素布局 */
.conversation-item {
  /* 确保布局正确 */
  display: flex;
  align-items: center;
  position: relative;
  padding-right: 40px; /* 为删除按钮留出空间 */
}

.conv-title {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
  cursor: text;
}

.conv-time {
  font-size: 11px;
  color: #888;
  margin-left: 4px;
  flex-shrink: 0;
}

/* 删除按钮样式 */
.delete-conv-btn {
  opacity: 0;
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(255, 59, 48, 0.1);
  border: none;
  border-radius: 4px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  padding: 0;
}

.conversation-item:hover .delete-conv-btn {
  opacity: 1;
}

.delete-conv-btn:hover {
  background: rgba(255, 59, 48, 0.2);
  transform: translateY(-50%) scale(1.1);
}

/* 模态对话框样式 */
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
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-content h3 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 18px;
}

.modal-content p {
  margin: 0 0 20px 0;
  color: #666;
  line-height: 1.5;
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
  transition: all 0.2s;
}

.btn-cancel {
  background: #f0f0f0;
  color: #333;
}

.btn-cancel:hover {
  background: #e0e0e0;
}

.btn-delete {
  background: #ff3b30;
  color: white;
}

.btn-delete:hover {
  background: #d32f2f;
}

/* Toast样式 */
.toast {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: #333;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  z-index: 1001;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease;
}

.toast.success {
  background: #10b981;
}

.toast.error {
  background: #ef4444;
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

</style>