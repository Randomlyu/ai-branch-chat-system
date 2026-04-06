/**
 * 状态持久化工具
 * 使用 sessionStorage 存储会话级别的UI状态
 * sessionStorage 在标签页关闭后自动清除，适合保存当前会话的状态
 */

// ========== 类型定义 ==========

// 聊天状态接口
export interface ChatState {
  conversationId?: number
  threadId?: number
  timestamp: number  // 存储时间戳，用于过期检查
}

// 侧边栏状态接口
export interface SidebarState {
  conversationSidebarCollapsed: boolean
  threadTreeSidebarCollapsed: boolean
  timestamp: number
}

// 消息编辑状态接口
export interface MessageEditState {
  messageId?: number
  content?: string
  timestamp: number
}

// 存储键名
const STORAGE_KEYS = {
  CHAT_STATE: 'ai-chat-chat-state',
  SIDEBAR_STATE: 'ai-chat-sidebar-state',
  MESSAGE_EDIT_STATE: 'ai-chat-message-edit-state'
} as const

// 过期时间（毫秒） - 24小时
const EXPIRY_TIME = 24 * 60 * 60 * 1000

// ========== 通用工具函数 ==========

/**
 * 检查状态是否过期
 */
function isStateExpired(timestamp: number): boolean {
  return Date.now() - timestamp > EXPIRY_TIME
}

/**
 * 存储状态到 sessionStorage
 */
function saveState<T>(key: string, state: T): void {
  try {
    const data = {
      ...state,
      timestamp: Date.now()
    }
    sessionStorage.setItem(key, JSON.stringify(data))
  } catch (error) {
    console.error(`保存状态到 sessionStorage 失败 (key: ${key}):`, error)
    // 忽略错误，不影响应用运行
  }
}

/**
 * 从 sessionStorage 加载状态
 */
function loadState<T>(key: string): T | null {
  try {
    const data = sessionStorage.getItem(key)
    if (!data) return null

    const state = JSON.parse(data) as T & { timestamp: number }
    
    // 检查是否过期
    if (isStateExpired(state.timestamp)) {
      sessionStorage.removeItem(key)
      return null
    }

    return state
  } catch (error) {
    console.error(`从 sessionStorage 加载状态失败 (key: ${key}):`, error)
    // 清除可能损坏的数据
    sessionStorage.removeItem(key)
    return null
  }
}

/**
 * 清除指定的状态
 */
function clearState(key: string): void {
  try {
    sessionStorage.removeItem(key)
  } catch (error) {
    console.error(`清除状态失败 (key: ${key}):`, error)
  }
}

// ========== 聊天状态专用方法 ==========

/**
 * 保存聊天状态（当前对话和线程）
 */
export function saveChatState(conversationId: number, threadId: number): void {
  const state: ChatState = {
    conversationId,
    threadId,
    timestamp: Date.now()
  }
  saveState(STORAGE_KEYS.CHAT_STATE, state)
}

/**
 * 加载聊天状态
 */
export function loadChatState(): ChatState | null {
  return loadState<ChatState>(STORAGE_KEYS.CHAT_STATE)
}

/**
 * 清除聊天状态
 */
export function clearChatState(): void {
  clearState(STORAGE_KEYS.CHAT_STATE)
}

// ========== 侧边栏状态专用方法 ==========

/**
 * 保存侧边栏状态
 */
export function saveSidebarState(
  conversationSidebarCollapsed: boolean, 
  threadTreeSidebarCollapsed: boolean
): void {
  const state: SidebarState = {
    conversationSidebarCollapsed,
    threadTreeSidebarCollapsed,
    timestamp: Date.now()
  }
  saveState(STORAGE_KEYS.SIDEBAR_STATE, state)
}

/**
 * 加载侧边栏状态
 */
export function loadSidebarState(): SidebarState | null {
  return loadState<SidebarState>(STORAGE_KEYS.SIDEBAR_STATE)
}

/**
 * 清除侧边栏状态
 */
export function clearSidebarState(): void {
  clearState(STORAGE_KEYS.SIDEBAR_STATE)
}

// ========== 消息编辑状态专用方法 ==========

/**
 * 保存消息编辑状态
 */
export function saveMessageEditState(messageId: number, content: string): void {
  const state: MessageEditState = {
    messageId,
    content,
    timestamp: Date.now()
  }
  saveState(STORAGE_KEYS.MESSAGE_EDIT_STATE, state)
}

/**
 * 加载消息编辑状态
 */
export function loadMessageEditState(): MessageEditState | null {
  try {
    const data = sessionStorage.getItem(STORAGE_KEYS.MESSAGE_EDIT_STATE)
    if (!data) return null

    const state = JSON.parse(data) as MessageEditState & { timestamp: number }
    
    // 检查是否过期（编辑状态应该更短，比如1小时）
    const EDIT_EXPIRY_TIME = 60 * 60 * 1000 // 1小时
    if (Date.now() - state.timestamp > EDIT_EXPIRY_TIME) {
      console.log('编辑状态已过期，清除')
      clearMessageEditState()
      return null
    }

    // 验证必需字段
    if (!state.messageId || !state.content) {
      console.log('编辑状态数据不完整，清除')
      clearMessageEditState()
      return null
    }

    return state
  } catch (error) {
    console.error(`从 sessionStorage 加载编辑状态失败:`, error)
    // 清除可能损坏的数据
    clearMessageEditState()
    return null
  }
}

/**
 * 清除消息编辑状态
 */
export function clearMessageEditState(): void {
  clearState(STORAGE_KEYS.MESSAGE_EDIT_STATE)
}

// ========== 清理所有状态 ==========

/**
 * 清理所有UI状态（登出时调用）
 */
export function clearAllUIState(): void {
  clearChatState()
  clearSidebarState()
  clearMessageEditState()
}

/**
 * 初始化状态持久化
 * 检查并清理过期的状态
 */
export function initStatePersistence(): void {
  // 检查并清理所有可能过期的状态
  const keys = Object.values(STORAGE_KEYS)
  keys.forEach(key => {
    try {
      const data = sessionStorage.getItem(key)
      if (data) {
        const state = JSON.parse(data) as { timestamp: number }
        if (isStateExpired(state.timestamp)) {
          sessionStorage.removeItem(key)
        }
      }
    } catch (error) {
      // 忽略解析错误
      sessionStorage.removeItem(key)
    }
  })
}