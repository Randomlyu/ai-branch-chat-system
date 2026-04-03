import axios from 'axios'
import type { 
  Conversation, 
  Thread, 
  Message, 
  ThreadTree,
  CreateConversationRequest,
  SendMessageRequest,
  ApiResponse,
  ThreadUpdate,
  RegenerateMessageRequest,
  ThreadDeleteInfo,
  CreateBranchRequest,
  AIUsageInfo,
  CheckMessageEditableRequest,
  CheckMessageEditableResponse,
  UpdateUserMessageRequest,
  UpdateUserMessageResponse
} from '@/types/chat'

// 导入认证存储
import { useAuthStore } from '@/stores/auth'

// ========== 创建axios实例 ==========
const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 30000, // 30秒超时
  headers: {
    'Content-Type': 'application/json',
  }
})

// ========== 请求拦截器 ==========
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    
    // 添加认证Token
    if (authStore.accessToken) {
      if (config.headers) {
        config.headers.Authorization = `Bearer ${authStore.accessToken}`
      } else {
        config.headers = new axios.AxiosHeaders({ Authorization: `Bearer ${authStore.accessToken}` })
      }
    }
    
    console.log(`请求: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// ========== 响应拦截器 ==========
apiClient.interceptors.response.use(
  (response) => {
    // 统一处理响应格式
    const data = response.data
    
    // 情况1：如果后端返回的是我们期望的标准格式
    if (data && typeof data === 'object' && 'data' in data && 'code' in data) {
      return data
    }
    
    // 情况2：如果后端返回的是直接的对象或数组
    return {
      data: data,
      code: response.status,
      message: 'success'
    }
  },
  async (error) => {
    console.error('API请求错误:', error)
    
    // 处理401未授权错误 - 尝试刷新令牌
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      
      // 检查是否是登录端点，如果是则直接返回错误
      if (error.config.url?.includes('/auth/login')) {
        return Promise.reject(error)
      }
      
      // 尝试刷新令牌
      try {
        await authStore.refreshAccessToken()
        
        // 使用新令牌重试原始请求
        if (authStore.accessToken) {
          error.config.headers.Authorization = `Bearer ${authStore.accessToken}`
          return apiClient(error.config)
        }
      } catch (refreshError) {
        // 刷新失败，跳转到登录页
        authStore.logout()
        window.location.href = '/login'
        return Promise.reject(new Error('会话已过期，请重新登录'))
      }
    }
    
    // 统一错误处理
    if (error.response) {
      const { status, data } = error.response
      let message = '请求失败'
      
      if (data && typeof data === 'object' && 'message' in data) {
        message = (data as { message: string }).message
      } else if (status === 401) {
        message = '未授权，请登录'
      } else if (status === 403) {
        message = '拒绝访问'
      } else if (status === 404) {
        message = '资源不存在'
      } else if (status === 429) {
        message = '当日API用量已达上限，请明日再试'
      } else if (status && status >= 500) {
        message = '服务器错误'
      }
      
      return Promise.reject(new Error(message))
    } else if (error.request) {
      return Promise.reject(new Error('网络连接失败，请检查网络'))
    } else {
      return Promise.reject(error)
    }
  }
)

// ========== 流式相关类型和函数 ==========
/**
 * 流式响应数据结构
 */
export interface StreamResponseData {
  content: string
  done: boolean
  error?: boolean
  message_id?: number
  user_message_id?: number
  model_used?: string
}

/**
 * 流式请求配置
 */
export interface StreamRequestConfig {
  onMessage: (data: StreamResponseData) => void
  onError?: (error: Error) => void
  onComplete?: () => void
  signal?: AbortSignal
}

/**
 * 发送流式请求
 */
export async function sendStreamRequest(
  url: string,
  data: unknown,
  config: StreamRequestConfig
): Promise<void> {
  const { onMessage, onError, onComplete, signal } = config
  const authStore = useAuthStore()
  
  try {
    const response = await fetch(`${apiClient.defaults.baseURL}${url}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify(data),
      signal
    })

    if (!response.ok) {
      throw new Error(`HTTP错误! 状态码: ${response.status}`)
    }

    if (!response.body) {
      throw new Error('响应体为空')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    try {
      // 使用for循环避免eslint警告
      for (;;) {
        const { done, value } = await reader.read()
        
        if (done) {
          if (onComplete) onComplete()
          break
        }

        buffer += decoder.decode(value, { stream: true })
        
        // 处理可能的多条SSE消息
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // 最后一行可能不完整

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.substring(6).trim()
            if (dataStr) {
              try {
                const parsedData: StreamResponseData = JSON.parse(dataStr)
                onMessage(parsedData)
              } catch (e) {
                console.error('解析SSE数据失败:', e, '数据:', dataStr)
              }
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  } catch (error) {
    // 正确处理TypeScript的unknown类型
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        console.log('流式请求被中止')
        return
      }
      
      console.error('流式请求失败:', error)
      if (onError) {
        onError(error)
      }
    } else {
      console.error('流式请求失败，未知错误:', error)
      if (onError) {
        onError(new Error('流式请求过程中发生未知错误'))
      }
    }
  }
}

// ========== 认证相关API ==========
// 登录请求接口
export interface LoginRequest {
  username: string
  password: string
}

// 登录响应接口
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user_id: number
  username: string
  need_password_change: boolean
}

// 刷新令牌请求接口
export interface RefreshTokenRequest {
  refresh_token: string
}

// 刷新令牌响应接口
export interface RefreshTokenResponse {
  access_token: string
  token_type: string
}

// 修改密码请求接口
export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

// 用户信息接口
export interface UserInfo {
  id: number
  username: string
  email?: string
  need_password_change: boolean
  created_at: string
}

/**
 * 用户登录
 */
export const login = async (data: LoginRequest): Promise<ApiResponse<LoginResponse>> => {
  return apiClient.post('/auth/login', data)
}

/**
 * 刷新访问令牌
 */
export const refreshToken = async (data: RefreshTokenRequest): Promise<ApiResponse<RefreshTokenResponse>> => {
  return apiClient.post('/auth/refresh', data)
}

/**
 * 修改密码
 */
export const changePassword = async (data: ChangePasswordRequest): Promise<ApiResponse<void>> => {
  return apiClient.post('/auth/change-password', data)
}

/**
 * 获取当前用户信息
 */
export const getCurrentUser = async (): Promise<ApiResponse<UserInfo>> => {
  return apiClient.get('/auth/me')
}

// ========== 对话相关API ==========
/**
 * 获取对话列表
 */
export const getConversations = async (): Promise<ApiResponse<Conversation[]>> => {
  return apiClient.get('/conversations/')
}

/**
 * 获取单个对话详情
 */
export const getConversation = async (id: number): Promise<ApiResponse<Conversation>> => {
  return apiClient.get(`/conversations/${id}`)
}

/**
 * 创建对话
 */
export const createConversation = async (data: CreateConversationRequest): Promise<ApiResponse<Conversation>> => {
  return apiClient.post('/conversations/', data)
}

/**
 * 更新对话
 */
export const updateConversation = async (id: number, data: Partial<Conversation>): Promise<ApiResponse<Conversation>> => {
  return apiClient.put(`/conversations/${id}`, data)
}

/**
 * 删除对话
 */
export const deleteConversation = async (id: number): Promise<ApiResponse<void>> => {
  return apiClient.delete(`/conversations/${id}`)
}

// ========== 线程相关API ==========
/**
 * 获取线程详情
 */
export const getThread = async (id: number): Promise<ApiResponse<Thread>> => {
  return apiClient.get(`/threads/${id}`)
}

/**
 * 更新线程标题
 */
export const updateThreadTitle = async (threadId: number, data: ThreadUpdate): Promise<ApiResponse<Thread>> => {
  return apiClient.put(`/threads/${threadId}`, data)
}

/**
 * 删除线程（仅限叶子节点）
 */
export const deleteThread = async (threadId: number): Promise<ApiResponse<ThreadDeleteInfo>> => {
  return apiClient.delete(`/threads/${threadId}`)
}

/**
 * 获取对话的所有线程
 */
export const getConversationThreads = async (conversationId: number): Promise<ApiResponse<Thread[]>> => {
  return apiClient.get(`/conversations/${conversationId}/threads`)
}

/**
 * 获取线程树
 */
export const getThreadTree = async (conversationId: number): Promise<ApiResponse<ThreadTree[]>> => {
  return apiClient.get(`/conversations/${conversationId}/thread-tree`)
}

// ========== 消息相关API ==========
/**
 * 获取线程消息
 */
export const getThreadMessages = async (threadId: number): Promise<ApiResponse<Message[]>> => {
  return apiClient.get(`/threads/${threadId}/messages`)
}

/**
 * 流式发送消息
 */
export const sendMessageStream = async (
  data: SendMessageRequest,
  config: StreamRequestConfig
): Promise<void> => {
  await sendStreamRequest('/chat/stream/', data, config)
}

/**
 * 删除消息
 */
export const deleteMessage = async (
  threadId: number, 
  messageId: number
): Promise<ApiResponse<{
  deleted_messages: number[];
  fixed_messages: number[];
  connection_point: number | null;
  is_latest_deleted: boolean;
}>> => {
  return apiClient.delete(`/threads/${threadId}/messages/${messageId}`);
}

/**
 * 流式重新生成消息
 */
export const regenerateMessageStream = async (
  threadId: number,
  messageId: number,
  data: RegenerateMessageRequest = {},
  config: StreamRequestConfig
): Promise<void> => {
  await sendStreamRequest(`/threads/${threadId}/messages/${messageId}/regenerate`, data, config)
}

// ===== 新增：消息编辑相关API =====
/**
 * 检查消息是否可编辑
 */
export const checkMessageEditable = async (
  messageId: number
): Promise<ApiResponse<CheckMessageEditableResponse>> => {
  return apiClient.get(`/messages/${messageId}/editable`)
}

/**
 * 流式更新用户消息
 */
export const updateUserMessageStream = async (
  messageId: number,
  data: UpdateUserMessageRequest,
  config: StreamRequestConfig
): Promise<void> => {
  await sendStreamRequest(`/messages/${messageId}/update`, data, config)
}
// ================================

// ========== AI相关API ==========
/**
 * 停止生成
 */
export const stopGeneration = async (): Promise<ApiResponse<void>> => {
  return apiClient.post('/chat/stop/')
}

/**
 * 获取AI用量信息
 */
export const getAIUsage = async (): Promise<ApiResponse<AIUsageInfo>> => {
  return apiClient.get('/chat/usage/')
}

/**
 * 获取可用模型列表
 */
export const getAvailableModels = async (): Promise<ApiResponse<{ models: string[], default_model: string }>> => {
  return apiClient.get('/chat/models/')
}

// ========== 分支相关API ==========
/**
 * 创建分支
 */
export const createBranch = async (data: CreateBranchRequest): Promise<ApiResponse<Thread>> => {
  return apiClient.post('/branch/', data)
}

// ========== 默认导出 ==========
export default {
  // 认证相关
  login,
  refreshToken,
  changePassword,
  getCurrentUser,
  
  // 对话相关
  getConversations,
  getConversation,
  createConversation,
  updateConversation,
  deleteConversation,
  
  // 线程相关
  getThread,
  updateThreadTitle,
  deleteThread,
  getConversationThreads,
  getThreadTree,
  
  // 消息相关
  getThreadMessages,
  sendMessageStream,  // 流式发送消息
  deleteMessage,
  regenerateMessageStream,  // 流式重新生成消息
  // ===== 新增：消息编辑相关API =====
  checkMessageEditable,
  updateUserMessageStream,
  // ================================
  
  // AI相关
  stopGeneration,
  getAIUsage,
  getAvailableModels,
  
  // 分支相关
  createBranch
}