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
  CreateBranchRequest
} from '@/types/chat'

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
    // 添加固定Token（使用alice的Token）
    if (config.headers) {
      config.headers.Authorization = 'Bearer dev_token_alice'
    } else {
      config.headers = new axios.AxiosHeaders({ Authorization: 'Bearer dev_token_alice' })
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
  (error) => {
    console.error('API请求错误:', error)
    
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
  
  try {
    const response = await fetch(`${apiClient.defaults.baseURL}${url}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer dev_token_alice'
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
export const getAIUsage = async (): Promise<ApiResponse<unknown>> => {
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
  
  // AI相关
  stopGeneration,
  getAIUsage,
  getAvailableModels,
  
  // 分支相关
  createBranch
}