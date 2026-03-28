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
  // ===== 新增字段 =====
  parent_thread_id?: number | null
}

// 在现有的类型定义中添加
export interface ThreadPath {
  id: number
  title?: string
  depth?: number
  // 根据实际需要添加其他字段
  created_at?: string
  updated_at?: string
  conversation_id?: number
  parent_thread_id?: number | null
  is_active?: boolean
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
  // ===== 新增字段 =====
  is_editing?: boolean  // 前端专用：标记消息是否正在被编辑
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

// 删除消息响应类型
export interface DeleteMessageResponse {
  deleted_messages: number[];
  fixed_messages: number[];
  connection_point: number | null;
  is_latest_deleted: boolean;
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
  parent_thread_id?: number | null
  children?: ThreadTree[]
}

// API通用响应类型
export interface ApiResponse<T = unknown> {
  data: T
  code: number
  message: string
}

// 流式响应数据
export interface StreamResponseData {
  content: string
  done: boolean
  error?: boolean
  message_id?: number
  user_message_id?: number
  model_used?: string
}

// AI用量信息
export interface AIUsageInfo {
  current_date: string
  total_tokens: number
  max_daily_tokens: number
  remaining_tokens: number
  available_models: string[]
  default_model: string
  streaming_enabled: boolean
  next_reset?: string
  next_reset_timestamp?: number
}

// 模型列表响应
export interface ModelsResponse {
  models: string[]
  default_model: string
}

// 流式请求配置
export interface StreamRequestConfig {
  onMessage: (data: StreamResponseData) => void
  onError?: (error: Error) => void
  onComplete?: () => void
  signal?: AbortSignal
}

export interface RegenerateMessageRequest {
  model?: string
  stream?: boolean
}

export interface RegenerateMessageResponse {
  code: number
  message: string
  data?: {
    new_message: Message
    old_message_id: number
    user_message_id: number
  }
}

// ===== 删除线程相关的类型 =====
export type DeleteThreadRequest = Record<string, never>  // 表示空对象，而不是空接口

export interface ThreadDeleteInfo {
  deleted_thread_id: number
  deleted_message_ids: number[]
  parent_thread_id?: number | null
}

export interface DeleteThreadResponse {
  code: number
  message: string
  data?: ThreadDeleteInfo
}
// ===================================

// ===== 新增：消息编辑相关类型 =====
export interface CheckMessageEditableRequest {
  message_id: number
}

export interface CheckMessageEditableResponse {
  is_editable: boolean
  reason?: string
}

export interface UpdateUserMessageRequest {
  content: string
  model?: string
}

export interface UpdateUserMessageResponse {
  code: number
  message: string
  data?: {
    updated_user_message: Message
    new_ai_message: Message
    conversation_id: number
    thread_id: number
  }
}
// ===================================