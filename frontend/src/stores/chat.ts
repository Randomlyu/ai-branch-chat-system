import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { 
  Conversation, 
  Thread, 
  Message, 
  ThreadTree, 
  ApiResponse, 
  ThreadUpdate,
  StreamRequestConfig,
  StreamResponseData,
  AIUsageInfo,
  DeleteMessageResponse,
  ThreadDeleteInfo
} from '@/types/chat'
import * as chatApi from '@/api/chat'

export const useChatStore = defineStore('chat', () => {
  // ========== 状态 ==========
  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<Conversation | null>(null)
  const currentThread = ref<Thread | null>(null)
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const threadTree = ref<ThreadTree[]>([])
  const error = ref<string | null>(null)
  
  // 流式响应相关状态
  const isStreaming = ref(false)
  const streamingController = ref<AbortController | null>(null)
  const streamingModel = ref<string>('')
  const aiUsage = ref<AIUsageInfo | null>(null)
  const availableModels = ref<string[]>([])
  const currentModel = ref<string>('')

  // ========== 计算属性 ==========
  const threadPath = computed(() => {
    if (!currentThread.value) return []
    
    const findPath = (tree: ThreadTree[], targetId: number, path: ThreadTree[] = []): ThreadTree[] | null => {
      for (const node of tree) {
        const newPath = [...path, node]
        if (node.id === targetId) {
          return newPath
        }
        if (node.children) {
          const result = findPath(node.children, targetId, newPath)
          if (result) return result
        }
      }
      return null
    }
    
    return findPath(threadTree.value, currentThread.value.id) || []
  })

  // 检查是否达到Token上限
  const isTokenLimitReached = computed(() => {
    if (!aiUsage.value) return false
    return aiUsage.value.remaining_tokens <= 0
  })

  // 获取最新消息
  const latestMessage = computed(() => {
    if (messages.value.length === 0) return null
    return messages.value[messages.value.length - 1]
  })

  // ========== 基础动作 ==========
  /**
   * 获取对话列表
   */
  const fetchConversations = async (): Promise<void> => {
    try {
      isLoading.value = true
      const response = await chatApi.getConversations()
      conversations.value = response.data
      error.value = null
    } catch (err: unknown) {
      console.error('获取对话列表失败:', err)
      error.value = err instanceof Error ? err.message : '获取对话列表失败'
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 创建新对话
   */
  const createConversation = async (title: string = '新对话'): Promise<Conversation> => {
    try {
      isLoading.value = true
      const response = await chatApi.createConversation({ title })
      const newConv = response.data
      conversations.value.unshift(newConv)
      await switchConversation(newConv.id)
      error.value = null
      return newConv
    } catch (err: unknown) {
      console.error('创建对话失败:', err)
      error.value = err instanceof Error ? err.message : '创建对话失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 切换对话
   */
  const switchConversation = async (conversationId: number): Promise<void> => {
    try {
      isLoading.value = true
      
      // 获取对话详情
      const convResponse = await chatApi.getConversation(conversationId)
      currentConversation.value = convResponse.data
      
      // 获取对话的活跃线程
      const threadsResponse = await chatApi.getConversationThreads(conversationId)
      const activeThread = threadsResponse.data.find((t: Thread) => t.is_active) || threadsResponse.data[0]
      
      if (activeThread) {
        await switchThread(activeThread.id)
      } else {
        // 如果没有线程，清空消息
        messages.value = []
        currentThread.value = null
      }
      
      // 获取分支树
      await fetchThreadTree()
      error.value = null
    } catch (err: unknown) {
      console.error('切换对话失败:', err)
      error.value = err instanceof Error ? err.message : '切换对话失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }
  
  /**
   * 更新对话标题
   */
  const updateConversationTitle = async (conversationId: number, newTitle: string): Promise<void> => {
    try {
      isLoading.value = true
      const response = await chatApi.updateConversation(conversationId, { title: newTitle })
      
      // 更新对话列表中的对应项
      const index = conversations.value.findIndex(conv => conv.id === conversationId)
      if (index !== -1) {
        conversations.value[index] = response.data
      }
      
      // 如果更新的是当前对话，更新当前对话
      if (currentConversation.value?.id === conversationId) {
        currentConversation.value = response.data
      }
      
      error.value = null
    } catch (err: unknown) {
      console.error('更新对话标题失败:', err)
      error.value = err instanceof Error ? err.message : '更新对话标题失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 更新线程标题
   */
  const updateThread = async (threadId: number, newTitle: string): Promise<void> => {
    try {
      isLoading.value = true
      const threadUpdate: ThreadUpdate = { title: newTitle }
      const response = await chatApi.updateThreadTitle(threadId, threadUpdate)
      
      // 更新当前线程（如果当前线程是更新的线程）
      if (currentThread.value?.id === threadId) {
        currentThread.value = response.data
      }
      
      // 重新获取分支树以更新树中的标题
      if (currentConversation.value) {
        await fetchThreadTree()
      }
      
      error.value = null
    } catch (err: unknown) {
      console.error('更新线程标题失败:', err)
      error.value = err instanceof Error ? err.message : '更新线程标题失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 删除对话
   */
  const deleteConversation = async (conversationId: number): Promise<void> => {
    try {
      isLoading.value = true
      
      // 调用API删除
      await chatApi.deleteConversation(conversationId)
      
      // 从列表中移除
      const index = conversations.value.findIndex(conv => conv.id === conversationId)
      if (index !== -1) {
        conversations.value.splice(index, 1)
      }
      
      // 如果删除的是当前对话，需要切换到其他对话或清空
      if (currentConversation.value?.id === conversationId) {
        if (conversations.value.length > 0) {
          // 切换到第一个对话
          await switchConversation(conversations.value[0]!.id)
        } else {
          // 没有对话了，清空状态
          currentConversation.value = null
          currentThread.value = null
          messages.value = []
          threadTree.value = []
          
          // 自动创建新对话
          setTimeout(async () => {
            await createConversation('新对话')
          }, 100)
        }
      }
      
      error.value = null
      
    } catch (err: unknown) {
      console.error('删除对话失败:', err)
      error.value = err instanceof Error ? err.message : '删除对话失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // ========== 消息相关 ==========
  /**
   * 获取当前线程的消息
   */
  const fetchMessages = async (): Promise<void> => {
    if (!currentThread.value) return
    
    try {
      isLoading.value = true
      const response = await chatApi.getThreadMessages(currentThread.value.id)
      messages.value = response.data
      error.value = null
    } catch (err: unknown) {
      console.error('获取消息失败:', err)
      error.value = err instanceof Error ? err.message : '获取消息失败'
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 发送消息（流式版本）
   */
  const sendMessageStream = async (content: string): Promise<void> => {
    if (!currentConversation.value || !currentThread.value) {
      console.error('没有活跃的对话或线程')
      return
    }
    
    // 检查是否达到Token上限
    if (isTokenLimitReached.value) {
      error.value = '当日API用量已达上限，请明日再试'
      throw new Error('Token limit reached')
    }
    
    // 在外部定义变量，以便catch块中可以访问
    let userMessage: Message | null = null
    let tempAiMessageId: number | null = null
    
    try {
      // 停止之前的流式请求
      if (isStreaming.value && streamingController.value) {
        streamingController.value.abort()
      }
      
      // 创建新的AbortController
      const controller = new AbortController()
      streamingController.value = controller
      isStreaming.value = true
      streamingModel.value = currentModel.value
      
      // 添加用户消息到本地
      const parentMsg = messages.value.length > 0 ? messages.value[messages.value.length - 1] : undefined
      userMessage = {
        id: Date.now(), // 临时ID
        thread_id: currentThread.value.id,
        role: 'user',
        content,
        created_at: new Date().toISOString(),
        parent_id: parentMsg?.id
      }
      messages.value.push(userMessage)
      
      // 为AI消息创建占位符
      tempAiMessageId = Date.now() + 1
      const aiMessagePlaceholder: Message = {
        id: tempAiMessageId,
        thread_id: currentThread.value.id,
        role: 'assistant',
        content: '', // 初始为空
        created_at: new Date().toISOString(),
        parent_id: userMessage.id,
        model_used: currentModel.value
      }
      messages.value.push(aiMessagePlaceholder)
      
      // 准备流式配置
      const streamConfig: StreamRequestConfig = {
        onMessage: (data: StreamResponseData) => {
          if (data.error) {
            // 处理错误
            const errorMsg = data.content || 'AI服务发生错误'
            error.value = errorMsg
            
            // 更新消息内容
            const messageIndex = messages.value.findIndex(msg => msg.id === tempAiMessageId)
            if (messageIndex !== -1) {
              const message = messages.value[messageIndex]
              if (message) {
                message.content += errorMsg
                // 强制响应式更新
                messages.value = [...messages.value]
              }
            }
          } else if (data.done) {
            // 流式完成
            isStreaming.value = false
            streamingController.value = null
            
            // 处理消息ID更新
            if (data.message_id && data.user_message_id) {
              // 如果有消息ID，直接更新本地消息
              setTimeout(() => {
                // 更新用户消息ID
                const userMsgIndex = messages.value.findIndex(msg => 
                  msg.role === 'user' && msg.id === userMessage?.id
                )
                if (userMsgIndex !== -1 && messages.value[userMsgIndex]) {
                  messages.value[userMsgIndex].id = data.user_message_id!
                }
                
                // 更新AI消息ID
                if (tempAiMessageId !== null) {
                  const aiMsgIndex = messages.value.findIndex(msg => msg.id === tempAiMessageId)
                  if (aiMsgIndex !== -1 && messages.value[aiMsgIndex]) {
                    messages.value[aiMsgIndex].id = data.message_id!
                    // 确保模型信息完整
                    if (data.model_used) {
                      messages.value[aiMsgIndex].model_used = data.model_used
                    }
                  }
                }
                
                // 触发响应式更新
                messages.value = [...messages.value]
                console.log('已更新消息ID:', { 
                  userMsgId: data.user_message_id, 
                  aiMsgId: data.message_id 
                })
              }, 0)
            } else {
              // 如果没有消息ID，重新获取消息列表
              setTimeout(async () => {
                try {
                  console.log('重新获取消息列表以获取真实ID...')
                  await fetchMessages()
                } catch (fetchError) {
                  console.error('重新获取消息失败:', fetchError)
                }
              }, 300) // 等待300ms确保后端已保存消息
            }
            
            // 更新线程的活跃状态
            if (currentThread.value) {
              currentThread.value.is_active = true
              currentThread.value.updated_at = new Date().toISOString()
            }
            
            // 刷新用量信息
            fetchAIUsage()
          } else {
            // 正常内容 - 确保内容不为空
            if (data.content && data.content.trim()) {
              // 更新消息内容
              const messageIndex = messages.value.findIndex(msg => msg.id === tempAiMessageId)
              if (messageIndex !== -1) {
                const message = messages.value[messageIndex]
                if (message) {
                  // 使用Vue的响应式更新
                  message.content += data.content
                  messages.value = [...messages.value]
                }
              }
            }
          }
        },
        onError: (err: Error) => {
          console.error('流式请求错误:', err)
          error.value = err.message
          isStreaming.value = false
          streamingController.value = null
          
          if (tempAiMessageId !== null) {
            // 更新错误消息
            const messageIndex = messages.value.findIndex(msg => msg.id === tempAiMessageId)
            if (messageIndex !== -1) {
              const message = messages.value[messageIndex]
              if (message) {
                message.content += `\n[错误: ${err.message}]`
                messages.value = [...messages.value]
              }
            }
          }
        },
        onComplete: () => {
          // 流式请求完成
          console.log('流式请求完成')
        },
        signal: controller.signal
      }
      
      // 调用API发送流式消息
      await chatApi.sendMessageStream({
        thread_id: currentThread.value.id,
        content,
        model: currentModel.value
      }, streamConfig)
      
      error.value = null
      
    } catch (err: unknown) {
      console.error('发送消息失败:', err)
      error.value = err instanceof Error ? err.message : '发送消息失败'
      isStreaming.value = false
      streamingController.value = null
      
      // 移除临时消息
      if (messages.value.length >= 2) {
        const lastMessage = messages.value[messages.value.length - 1]
        const secondLastMessage = messages.value[messages.value.length - 2]
        
        // 检查最后两条消息是否是我们刚刚添加的
        const shouldRemoveLastTwo = 
          (userMessage && lastMessage?.id === userMessage.id) ||
          (tempAiMessageId && lastMessage?.id === tempAiMessageId) ||
          (userMessage && secondLastMessage?.id === userMessage.id) ||
          (tempAiMessageId && secondLastMessage?.id === tempAiMessageId)
        
        if (shouldRemoveLastTwo) {
          messages.value.splice(messages.value.length - 2, 2)
          // 触发响应式更新
          messages.value = [...messages.value]
        }
      }
      
      throw err
    }
  }

  /**
   * 重新生成消息
   */
  const regenerateMessage = async (
    threadId: number,
    messageId: number,
    model?: string
  ): Promise<{
    success: boolean;
    error?: string;
    data?: Message;
  }> => {
    try {
      isLoading.value = true
      
      // 流式重新生成
      const tempNewMessageId = Date.now()
      const oldMessage = messages.value.find(msg => msg.id === messageId)
      const parentId = oldMessage?.parent_id
      
      const controller = new AbortController()
      streamingController.value = controller
      isStreaming.value = true
      streamingModel.value = model || currentModel.value
      
      // 在流式开始前，先移除旧消息
      const oldMessageIndex = messages.value.findIndex(msg => msg.id === messageId)
      if (oldMessageIndex !== -1) {
        messages.value.splice(oldMessageIndex, 1)
        messages.value = [...messages.value] // 触发响应式更新
      }
      
      // 准备流式配置
      const streamConfig: StreamRequestConfig = {
        onMessage: (data: StreamResponseData) => {
          if (data.error) {
            // 处理错误
            const errorMsg = data.content || '重新生成失败'
            error.value = errorMsg
            
            const messageIndex = messages.value.findIndex(msg => msg.id === tempNewMessageId)
            if (messageIndex !== -1) {
              const message = messages.value[messageIndex]
              if (message) {
                message.content += errorMsg
                messages.value = [...messages.value]
              }
            }
          } else if (data.done) {
            // 流式完成
            isStreaming.value = false
            streamingController.value = null
            
            // 处理消息ID更新
            if (data.message_id) {
              const messageIndex = messages.value.findIndex(msg => msg.id === tempNewMessageId)
              if (messageIndex !== -1 && messages.value[messageIndex]) {
                messages.value[messageIndex].id = data.message_id
                if (data.model_used) {
                  messages.value[messageIndex].model_used = data.model_used
                }
                
                // 触发响应式更新
                messages.value = [...messages.value]
                console.log('已更新重新生成的消息ID:', data.message_id)
              }
            } else {
              // 重新获取消息列表
              setTimeout(async () => {
                try {
                  await fetchMessages()
                } catch (fetchError) {
                  console.error('重新获取消息失败:', fetchError)
                }
              }, 300)
            }
            
            // 刷新用量信息
            fetchAIUsage()
          } else {
            // 正常内容
            if (data.content && data.content.trim()) {
              // 查找或创建临时消息
              const messageIndex = messages.value.findIndex(msg => msg.id === tempNewMessageId)
              
              if (messageIndex === -1) {
                // 创建临时消息
                const tempMessage: Message = {
                  id: tempNewMessageId,
                  thread_id: threadId,
                  role: 'assistant',
                  content: data.content,
                  created_at: new Date().toISOString(),
                  parent_id: parentId,
                  model_used: model || currentModel.value
                }
                // 通过创建新数组触发响应式更新
                messages.value = [...messages.value, tempMessage]  // 一次性添加
              } else {
                // 更新现有消息
                const message = messages.value[messageIndex]
                if (message) {
                  // 直接更新对象属性
                  message.content += data.content
                  // 只在特定时机触发响应式更新
                  if (data.content.length > 20 || data.content.includes('\n')) {
                    messages.value = [...messages.value]
                  }
                }
              }
            }
          }
        },
        onError: (err: Error) => {
          console.error('流式重新生成失败:', err)
          error.value = err.message
          isStreaming.value = false
          streamingController.value = null
          
          // 如果发生错误，重新获取消息列表恢复状态
          setTimeout(async () => {
            try {
              await fetchMessages()
            } catch (fetchError) {
              console.error('重新获取消息失败:', fetchError)
            }
          }, 300)
        },
        onComplete: () => {
          console.log('流式重新生成完成')
        },
        signal: controller.signal
      }
      
      // 调用API
      await chatApi.regenerateMessageStream(
        threadId,
        messageId,
        { model, stream: true },
        streamConfig
      )
      
      error.value = null
      return { success: true, data: undefined }
      
    } catch (err: unknown) {
      console.error('重新生成消息失败:', err)
      error.value = err instanceof Error ? err.message : '重新生成消息失败'
      return { 
        success: false, 
        error: err instanceof Error ? err.message : '重新生成消息失败' 
      }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 删除消息
   */
  const deleteMessage = async (threadId: number, messageId: number): Promise<{
    success: boolean;
    error?: string;
    data?: DeleteMessageResponse;
  }> => {
    try {
      isLoading.value = true
      const response = await chatApi.deleteMessage(threadId, messageId)
      
      if (response.code === 200) {
        // 1. 从本地消息列表中移除被删除的消息
        const deletedIds = response.data.deleted_messages
        messages.value = messages.value.filter(msg => !deletedIds.includes(msg.id))
        
        // 2. 修复被影响消息的parent_id
        if (response.data.fixed_messages && response.data.fixed_messages.length > 0) {
          // 重新获取消息以确保数据一致性
          await fetchMessages()
        }
        
        // 3. 如果删除的是最新消息，刷新消息列表
        if (response.data.is_latest_deleted) {
          await fetchMessages()
        }
        
        error.value = null
        return { success: true, data: response.data }
      } else {
        error.value = response.message || '删除消息失败'
        return { success: false, error: response.message }
      }
    } catch (err: unknown) {
      console.error('删除消息失败:', err)
      error.value = err instanceof Error ? err.message : '删除消息失败'
      return { 
        success: false, 
        error: err instanceof Error ? err.message : '删除消息失败' 
      }
    } finally {
      isLoading.value = false
    }
  }

  // ========== 分支相关 ==========
  /**
   * 创建分支
   */
  const createBranch = async (parentMessageId: number, newMessageContent?: string): Promise<Thread | null> => {
    if (!currentConversation.value) {
      const errorMsg = '没有活跃的对话，请先创建或选择对话'
      console.error(errorMsg)
      error.value = errorMsg
      throw new Error(errorMsg)
    }
    
    try {
      isLoading.value = true
      const response = await chatApi.createBranch({
        conversation_id: currentConversation.value.id,
        parent_message_id: parentMessageId,
        new_message_content: newMessageContent
      })
      
      const newThread = response.data
      
      // 切换到新分支
      await switchThread(newThread.id)
      
      // 刷新分支树
      await fetchThreadTree()
      
      error.value = null
      return newThread
    } catch (err: unknown) {
      let errorMessage = '创建分支失败'
      
      if (err && typeof err === 'object') {
        // 处理 Axios 错误响应
        if ('response' in err && err.response) {
          const axiosError = err as { response: { data: { detail?: string; message?: string } } }
          
          if (axiosError.response.data?.detail) {
            const detail = axiosError.response.data.detail
            
            if (detail.includes('分支深度已达上限')) {
              errorMessage = '分支深度已达上限（3层），请在更上层创建分支'
            } else if (detail.includes('仅允许在当前线程的最新消息处创建分支')) {
              errorMessage = '只能在当前对话的最新消息处创建分支'
            } else if (detail.includes('线程无消息')) {
              errorMessage = '当前线程没有消息，无法创建分支'
            } else {
              errorMessage = detail
            }
          } else if (axiosError.response.data?.message) {
            errorMessage = axiosError.response.data.message
          }
        } else if ('message' in err && typeof err.message === 'string') {
          errorMessage = err.message
        }
      }
      
      console.error('创建分支失败:', err)
      error.value = errorMessage
      throw new Error(errorMessage)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 切换线程
   */
  const switchThread = async (threadId: number): Promise<void> => {
    try {
      isLoading.value = true
      
      // 停止当前流式生成
      await stopStreaming()
      
      // 获取线程详情
      const threadResponse = await chatApi.getThread(threadId)
      currentThread.value = threadResponse.data
      
      // 获取线程消息
      await fetchMessages()
      
      error.value = null
    } catch (err: unknown) {
      console.error('切换线程失败:', err)
      error.value = err instanceof Error ? err.message : '切换线程失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 删除线程（仅限叶子节点）
   */
  const deleteThread = async (threadId: number): Promise<{
    success: boolean;
    error?: string;
    data?: ThreadDeleteInfo;
    newActiveThreadId?: number;
  }> => {
    try {
      isLoading.value = true
      const response = await chatApi.deleteThread(threadId)
      
      if (response.code === 200) {
        const deleteInfo = response.data
        
        // 1. 从本地线程树中移除被删除的线程
        const removeThreadFromTree = (tree: ThreadTree[], targetId: number): ThreadTree[] => {
          return tree.filter(node => {
            if (node.id === targetId) {
              return false
            }
            if (node.children && node.children.length > 0) {
              node.children = removeThreadFromTree(node.children, targetId)
            }
            return true
          })
        }
        
        threadTree.value = removeThreadFromTree(threadTree.value, threadId)
        
        // 2. 处理当前线程状态
        let newActiveThreadId: number | undefined
        
        if (currentThread.value?.id === threadId) {
          // 如果删除的是当前正在查看的线程
          if (deleteInfo.parent_thread_id) {
            // 如果有父线程，切换到父线程
            newActiveThreadId = deleteInfo.parent_thread_id
          } else {
            // 如果没有父线程，找到对话的主线程
            const findRootThread = (tree: ThreadTree[]): ThreadTree | null => {
              for (const node of tree) {
                if (node.depth === 0) {
                  return node
                }
                if (node.children && node.children.length > 0) {
                  const result = findRootThread(node.children)
                  if (result) return result
                }
              }
              return null
            }
            
            const rootThread = findRootThread(threadTree.value)
            if (rootThread) {
              newActiveThreadId = rootThread.id
            }
          }
          
          // 切换到新线程
          if (newActiveThreadId) {
            await switchThread(newActiveThreadId)
          } else {
            // 没有其他线程了，清空当前线程和消息
            currentThread.value = null
            messages.value = []
          }
        }
        
        error.value = null
        return { 
          success: true, 
          data: deleteInfo,
          newActiveThreadId
        }
      } else {
        error.value = response.message || '删除线程失败'
        return { success: false, error: response.message }
      }
    } catch (err: unknown) {
      console.error('删除线程失败:', err)
      error.value = err instanceof Error ? err.message : '删除线程失败'
      return { 
        success: false, 
        error: err instanceof Error ? err.message : '删除线程失败' 
      }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 获取分支树
   */
  const fetchThreadTree = async (): Promise<void> => {
    if (!currentConversation.value) return
    
    try {
      const response = await chatApi.getThreadTree(currentConversation.value.id)
      threadTree.value = response.data
      error.value = null
    } catch (err: unknown) {
      console.error('获取分支树失败:', err)
      error.value = err instanceof Error ? err.message : '获取分支树失败'
    }
  }

  /**
   * 检查消息是否被分支引用
   */
  const isMessageBranchingPoint = (messageId: number): boolean => {
    if (!threadTree.value || threadTree.value.length === 0) {
      return false
    }
    
    // 递归检查分支树
    const checkTree = (nodes: ThreadTree[]): boolean => {
      for (const node of nodes) {
        if (node.parent_message_id === messageId) {
          return true
        }
        if (node.children && node.children.length > 0) {
          if (checkTree(node.children)) {
            return true
          }
        }
      }
      return false
    }
    
    return checkTree(threadTree.value)
  }

  // ========== AI相关 ==========
  /**
   * 获取AI用量信息
   */
  const fetchAIUsage = async (): Promise<void> => {
    try {
      const response = await chatApi.getAIUsage()
      // 使用类型断言，因为我们知道API返回的数据结构
      aiUsage.value = response.data as AIUsageInfo
    } catch (err: unknown) {
      console.error('获取AI用量失败:', err)
      // 不抛出错误，因为用量信息不是关键功能
    }
  }

  /**
   * 获取可用模型
   */
  const fetchAvailableModels = async (): Promise<void> => {
    try {
      const response = await chatApi.getAvailableModels()
      // 使用类型断言
      const modelsData = response.data as { models: string[], default_model: string }
      
      // 确保包含模拟模式
      const allModels = [...modelsData.models]
      if (!allModels.includes('mock') && !allModels.includes('模拟模式')) {
        allModels.push('模拟模式')
      }
      
      availableModels.value = allModels
      currentModel.value = modelsData.default_model ?? (allModels.length > 0 ? allModels[0] : '模拟模式')
    } catch (err: unknown) {
      console.error('获取模型列表失败:', err)
      // 设置默认值，确保包含模拟模式
      availableModels.value = ['模拟模式']
      currentModel.value = '模拟模式'
    }
  }

  /**
   * 设置当前模型
   */
  const setCurrentModel = (model: string): void => {
    currentModel.value = model
  }

  /**
   * 停止流式生成
   */
  const stopStreaming = async (): Promise<void> => {
    if (isStreaming.value && streamingController.value) {
      try {
        console.log('正在停止流式生成...')
        
        // 1. 先通知后端停止生成（但不要立即中止前端流式请求）
        await chatApi.stopGeneration()
        
        console.log('已发送停止请求，等待后端处理...')
        
        // 2. 等待一小段时间，让后端有机会保存中断消息
        // 注意：我们不立即中止流式请求，让后端返回完成事件
        await new Promise(resolve => setTimeout(resolve, 1000)) // 等待1秒
        
        // 3. 然后中止前端的流式请求
        if (streamingController.value) {
          streamingController.value.abort()
        }
        
        // 4. 重置流式状态
        isStreaming.value = false
        streamingController.value = null
        streamingModel.value = ''
        
        // 5. 重新获取消息，以获取后端保存的中断消息
        console.log('重新获取消息列表...')
        await fetchMessages()
        
        // 6. 刷新用量信息
        await fetchAIUsage()
        
        console.log('已停止流式生成')
        
      } catch (err: unknown) {
        console.error('停止生成失败:', err)
        error.value = err instanceof Error ? err.message : '停止生成失败'
        
        // 即使API调用失败，也要重置前端状态
        isStreaming.value = false
        streamingController.value = null
        streamingModel.value = ''
        
        // 重新获取消息，以确保状态一致
        await fetchMessages()
      }
    }
  }

  // ========== 工具方法 ==========
  /**
   * 验证消息是否存在
   */
  const validateMessageExists = async (messageId: number): Promise<boolean> => {
    if (!currentThread.value) return false
    
    try {
      // 首先在本地消息列表中查找
      const localMessage = messages.value.find(msg => msg.id === messageId)
      if (localMessage) {
        return true
      }
      
      // 如果本地没有，尝试从服务器获取最新消息列表
      await fetchMessages()
      
      // 再次检查
      const refreshedMessage = messages.value.find(msg => msg.id === messageId)
      return !!refreshedMessage
      
    } catch (err) {
      console.error('验证消息存在失败:', err)
      return false
    }
  }

  /**
   * 获取模型显示名称
   */
  const getModelDisplayName = (model: string): string => {
    const modelDisplayNames: Record<string, string> = {
      'mock': '模拟模式',
      '模拟模式': '模拟模式',
      'deepseek-chat': 'DeepSeek Chat',
      'deepseek-ai/DeepSeek-V3': 'DeepSeek V3',
      'gpt-4': 'GPT-4',
      'gpt-3.5-turbo': 'GPT-3.5 Turbo'
    }
    
    return modelDisplayNames[model] || model
  }

  /**
   * 获取输入框占位符
   */
  const getInputPlaceholder = (): string => {
    if (isTokenLimitReached.value) {
      return '当日API用量已达上限，请明日再试'
    }
    if (isStreaming.value) {
      return 'AI正在生成，请稍后...'
    }
    return '发送消息给AI... (Shift+Enter换行，Enter发送)'
  }

  /**
   * 获取发送按钮标题
   */
  const getSendButtonTitle = (userInput: string): string => {
    if (isTokenLimitReached.value) {
      return '用量已达上限'
    }
    if (isStreaming.value) {
      return '停止生成'
    }
    if (!userInput.trim()) {
      return '请输入消息'
    }
    return '发送消息'
  }

  /**
   * 检查是否可以发送消息
   */
  const canSendMessage = (userInput: string): boolean => {
    if (!userInput.trim()) return false
    if (isStreaming.value) return false
    if (isTokenLimitReached.value) return false
    return true
  }

  /**
   * 复制到剪贴板
   */
  const copyToClipboard = async (content: string): Promise<boolean> => {
    try {
      await navigator.clipboard.writeText(content)
      return true
    } catch (err) {
      console.error('复制失败:', err)
      // 降级方案
      try {
        const textArea = document.createElement('textarea')
        textArea.value = content
        document.body.appendChild(textArea)
        textArea.select()
        const success = document.execCommand('copy')
        document.body.removeChild(textArea)
        return success
      } catch (fallbackErr) {
        console.error('降级复制失败:', fallbackErr)
        return false
      }
    }
  }

  /**
   * 验证消息是否可以重新生成
   */
  const validateMessageForRegeneration = (message: Message): boolean => {
    if (isStreaming.value) return false
    if (message.role !== 'assistant') return false
    
    // 检查是否是最新消息
    if (!latestMessage.value || latestMessage.value.id !== message.id) {
      return false
    }
    
    // 检查是否被分支引用
    if (isMessageBranchingPoint(message.id)) {
      return false
    }
    
    return true
  }

  /**
   * 验证消息是否可以创建分支
   */
  const validateMessageForBranching = (message: Message): boolean => {
    if (isStreaming.value) return false
    if (message.role !== 'assistant') return false
    
    if (!latestMessage.value) return false
    return message.id === latestMessage.value.id
  }

  /**
   * 验证消息是否可以删除
   */
  const validateMessageForDeletion = (message: Message): boolean => {
    if (isStreaming.value) return false
    
    if (isMessageBranchingPoint(message.id)) {
      return false
    }
    
    if (message.role !== 'assistant') {
      return false
    }
    
    return true
  }

  /**
   * 获取消息操作的工具提示
   */
  const getMessageActionTitles = (message: Message) => {
    const titles = {
      regenerate: '',
      branch: '',
      delete: ''
    }
    
    // 重新生成按钮标题
    if (isStreaming.value) {
      titles.regenerate = '请等待生成完成'
    } else if (message.role !== 'assistant') {
      titles.regenerate = '只能重新生成AI消息'
    } else if (!latestMessage.value) {
      titles.regenerate = '当前没有消息'
    } else if (message.id !== latestMessage.value.id) {
      titles.regenerate = '只能重新生成最新AI消息'
    } else if (isMessageBranchingPoint(message.id)) {
      titles.regenerate = '此消息已被分支引用，无法重新生成'
    } else {
      titles.regenerate = '重新生成此AI回复'
    }
    
    // 创建分支按钮标题
    if (isStreaming.value) {
      titles.branch = '请等待生成完成'
    } else if (message.role !== 'assistant') {
      titles.branch = '只能在AI回复处创建分支'
    } else if (!latestMessage.value) {
      titles.branch = '当前没有消息'
    } else if (message.id !== latestMessage.value.id) {
      titles.branch = '只能在最新消息处创建分支'
    } else {
      titles.branch = '从此回复创建新分支'
    }
    
    // 删除按钮标题
    if (isStreaming.value) {
      titles.delete = '请等待生成完成'
    } else if (isMessageBranchingPoint(message.id)) {
      titles.delete = '此消息已被分支引用，无法删除'
    } else if (message.role !== 'assistant') {
      titles.delete = '只能删除AI消息'
    } else {
      titles.delete = '删除此AI回复及其对应的用户提问'
    }
    
    return titles
  }

  /**
   * 验证消息是否可以操作
   */
  const validateMessageOperation = (messageId: number, operation: 'regenerate' | 'branch' | 'delete'): {
    can: boolean
    reason?: string
  } => {
    const message = messages.value.find(msg => msg.id === messageId)
    if (!message) {
      return { can: false, reason: '消息不存在' }
    }
    
    switch (operation) {
      case 'regenerate':
        if (isStreaming.value) {
          return { can: false, reason: '请等待生成完成' }
        }
        if (message.role !== 'assistant') {
          return { can: false, reason: '只能重新生成AI消息' }
        }
        if (!latestMessage.value || message.id !== latestMessage.value.id) {
          return { can: false, reason: '只能重新生成最新AI消息' }
        }
        if (isMessageBranchingPoint(message.id)) {
          return { can: false, reason: '此消息已被分支引用，无法重新生成' }
        }
        return { can: true }
        
      case 'branch':
        if (isStreaming.value) {
          return { can: false, reason: '请等待生成完成' }
        }
        if (message.role !== 'assistant') {
          return { can: false, reason: '只能在AI回复处创建分支' }
        }
        if (!latestMessage.value || message.id !== latestMessage.value.id) {
          return { can: false, reason: '只能在最新消息处创建分支' }
        }
        if (currentThread.value?.depth !== undefined && currentThread.value.depth >= 3) {
          return { can: false, reason: '分支深度已达上限（3层）' }
        }
        return { can: true }
        
      case 'delete':
        if (isStreaming.value) {
          return { can: false, reason: '请等待生成完成' }
        }
        if (isMessageBranchingPoint(message.id)) {
          return { can: false, reason: '此消息已被分支引用，无法删除' }
        }
        if (message.role !== 'assistant') {
          return { can: false, reason: '只能删除AI消息' }
        }
        return { can: true }
        
      default:
        return { can: false, reason: '未知操作' }
    }
  }

  /**
   * 清除错误
   */
  const clearError = (): void => {
    error.value = null
  }

  /**
   * 初始化store
   */
  const initialize = async (): Promise<void> => {
    await fetchAvailableModels()
    await fetchAIUsage()
  }

  // ========== 返回所有状态和方法 ==========
  return {
    // 状态
    conversations,
    currentConversation,
    currentThread,
    messages,
    isLoading,
    threadTree,
    error,
    
    // 流式相关状态
    isStreaming,
    streamingModel,
    aiUsage,
    availableModels,
    currentModel,
    
    // 计算属性
    threadPath,
    isTokenLimitReached,
    latestMessage,

    // 基础动作
    fetchConversations,
    createConversation,
    switchConversation,
    updateConversationTitle,
    updateThread,
    deleteConversation,
    
    // 消息相关动作
    fetchMessages,
    sendMessageStream,
    regenerateMessage,
    deleteMessage,
    stopStreaming,
    
    // 分支相关动作
    createBranch,
    switchThread,
    deleteThread,
    fetchThreadTree,
    isMessageBranchingPoint,
    
    // AI相关动作
    fetchAIUsage,
    fetchAvailableModels,
    setCurrentModel,
    
    // 工具方法
    getModelDisplayName,
    validateMessageExists,
    validateMessageForRegeneration,
    validateMessageForBranching,
    validateMessageForDeletion,
    getMessageActionTitles,
    getInputPlaceholder,
    getSendButtonTitle,
    canSendMessage,
    copyToClipboard,
    validateMessageOperation,
    clearError,
    initialize
  }
})