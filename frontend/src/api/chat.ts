import axios from 'axios'
import type { 
  Conversation, 
  Thread, 
  Message, 
  ThreadTree,
  CreateConversationRequest,
  SendMessageRequest,
  SendMessageResponse,
  CreateBranchRequest,
  ApiResponse,
  ThreadUpdate
} from '@/types/chat'

// 创建axios实例
const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 30000, // 30秒超时
  headers: {
    'Content-Type': 'application/json',
  }
})

// 请求拦截器
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

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    // 统一处理响应格式
    const data = response.data
    
    // 情况1：如果后端返回的是我们期望的标准格式
    if (data && typeof data === 'object' && 'data' in data && 'code' in data) {
      return data
    }
    
    // 情况2：如果后端返回的是直接的对象或数组（您的实际情况）
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

// 流式响应接口定义
export interface StreamResponseData {
  content: string
  done: boolean
  error?: boolean
}

// 流式请求配置
export interface StreamRequestConfig {
  onMessage: (data: StreamResponseData) => void
  onError?: (error: Error) => void
  onComplete?: () => void
  signal?: AbortSignal
}

// 发送流式请求
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
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    if (!response.body) {
      throw new Error('Response body is null')
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
                console.error('Failed to parse SSE data:', e, 'Data:', dataStr)
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
        console.log('Stream request aborted')
        return
      }
      
      console.error('Stream request failed:', error)
      if (onError) {
        onError(error)
      }
    } else {
      console.error('Stream request failed with unknown error:', error)
      if (onError) {
        onError(new Error('Unknown error occurred during stream request'))
      }
    }
  }
}

// 对话相关API
export const getConversations = async (): Promise<ApiResponse<Conversation[]>> => {
  return apiClient.get('/conversations/')
}

export const getConversation = async (id: number): Promise<ApiResponse<Conversation>> => {
  return apiClient.get(`/conversations/${id}`)
}

export const createConversation = async (data: CreateConversationRequest): Promise<ApiResponse<Conversation>> => {
  return apiClient.post('/conversations/', data)
}

export const updateConversation = async (id: number, data: Partial<Conversation>): Promise<ApiResponse<Conversation>> => {
  return apiClient.put(`/conversations/${id}`, data)
}

export const deleteConversation = async (id: number): Promise<ApiResponse<void>> => {
  return apiClient.delete(`/conversations/${id}`)
}

// 线程相关API
export const getThread = async (id: number): Promise<ApiResponse<Thread>> => {
  return apiClient.get(`/threads/${id}`)
}

// 新增：更新线程标题
export const updateThreadTitle = async (threadId: number, data: ThreadUpdate): Promise<ApiResponse<Thread>> => {
  return apiClient.put(`/threads/${threadId}`, data)
}

export const getConversationThreads = async (conversationId: number): Promise<ApiResponse<Thread[]>> => {
  return apiClient.get(`/conversations/${conversationId}/threads`)
}

export const getThreadTree = async (conversationId: number): Promise<ApiResponse<ThreadTree[]>> => {
  return apiClient.get(`/conversations/${conversationId}/thread-tree`)
}

// 消息相关API
export const getThreadMessages = async (threadId: number): Promise<ApiResponse<Message[]>> => {
  return apiClient.get(`/threads/${threadId}/messages`)
}

export const sendMessage = async (data: SendMessageRequest): Promise<ApiResponse<SendMessageResponse>> => {
  return apiClient.post('/chat/', data)
}

// 新增：流式发送消息
export const sendMessageStream = async (
  data: SendMessageRequest,
  config: StreamRequestConfig
): Promise<void> => {
  await sendStreamRequest('/chat/stream/', data, config)
}

// 新增：停止生成
export const stopGeneration = async (): Promise<ApiResponse<void>> => {
  return apiClient.post('/chat/stop/')
}

// 新增：获取AI用量信息
export const getAIUsage = async (): Promise<ApiResponse<unknown>> => {
  return apiClient.get('/chat/usage/')
}

// 新增：获取可用模型列表
export const getAvailableModels = async (): Promise<ApiResponse<{ models: string[], default_model: string }>> => {
  return apiClient.get('/chat/models/')
}

export const createBranch = async (data: CreateBranchRequest): Promise<ApiResponse<Thread>> => {
  return apiClient.post('/branch/', data)
}

// 默认导出
export default {
  getConversations,
  getConversation,
  createConversation,
  updateConversation,
  deleteConversation,
  getThread,
  updateThreadTitle,
  getConversationThreads,
  getThreadMessages,
  sendMessage,
  sendMessageStream,  // 新增
  stopGeneration,     // 新增
  getAIUsage,         // 新增
  getAvailableModels, // 新增
  createBranch,
  getThreadTree
}