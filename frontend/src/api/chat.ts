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
  ApiResponse
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
    // 这里可以添加token等认证信息
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
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
      
      if (data && data.message) {
        message = data.message
      } else if (status === 401) {
        message = '未授权，请登录'
      } else if (status === 404) {
        message = '资源不存在'
      } else if (status >= 500) {
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

export const createBranch = async (data: CreateBranchRequest): Promise<ApiResponse<Thread>> => {
  return apiClient.post('/branch/', data)
}

export default {
  getConversations,
  getConversation,
  createConversation,
  updateConversation,
  deleteConversation,
  getThread,
  getConversationThreads,
  getThreadMessages,
  sendMessage,
  createBranch,
  getThreadTree
}