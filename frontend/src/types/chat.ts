// 基础实体类型
export interface Conversation {
  id: number
  title: string
  user_id?: number
  created_at: string
  updated_at: string
}

export interface Thread {
  id: number
  conversation_id: number
  parent_message_id?: number
  title?: string
  is_active: boolean
  created_at: string
  updated_at: string
  depth: number 
}

export interface Message {
  id: number
  thread_id: number
  role: 'user' | 'assistant'
  content: string
  parent_id?: number | undefined
  model_used?: string
  tokens?: number
  created_at: string
}

// API请求/响应类型
export interface CreateConversationRequest {
  title: string
}

export interface SendMessageRequest {
  thread_id: number
  content: string
  model?: string
}

export interface SendMessageResponse {
  user_message: Message
  ai_message: Message
  conversation_id: number
  thread_id: number
}

export interface CreateBranchRequest {
  conversation_id: number
  parent_message_id: number
  new_message_content?: string
}

// 添加 ThreadUpdate 接口
export interface ThreadUpdate {
  title: string
}

// 分支树类型
export interface ThreadTree {
  id: number
  conversation_id: number
  parent_message_id?: number
  title?: string
  depth: number 
  is_active: boolean
  created_at: string
  updated_at: string
  children?: ThreadTree[]
}

// API通用响应类型
export interface ApiResponse<T = unknown> {
  data: T
  code: number
  message: string
}