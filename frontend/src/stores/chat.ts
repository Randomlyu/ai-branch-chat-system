import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Conversation, Thread, Message, ThreadTree, ApiResponse } from '@/types/chat'
import * as chatApi from '@/api/chat'

export const useChatStore = defineStore('chat', () => {
  // ---------- 状态 ----------
  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<Conversation | null>(null)
  const currentThread = ref<Thread | null>(null)
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const threadTree = ref<ThreadTree[]>([])
  const error = ref<string | null>(null)

  // ---------- 计算属性 ----------
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

  // ---------- 动作 ----------
  // 获取对话列表
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
      console.log('finally 块：设置 isLoading = false')
    }
  }

  // 创建新对话
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

  // 切换对话
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
  
    // 更新对话标题
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

  // 删除对话
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

  // 获取当前线程的消息
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

  // 发送消息
  const sendMessage = async (content: string): Promise<void> => {
    if (!currentConversation.value || !currentThread.value) {
      console.error('没有活跃的对话或线程')
      return
    }
    
    try {
      isLoading.value = true
      
      // 添加用户消息到本地
      const userMessage: Message = {
        id: Date.now(), // 临时ID
        thread_id: currentThread.value.id,
        role: 'user',
        content,
        created_at: new Date().toISOString(),
        parent_id: messages.value.length > 0 ? messages.value[messages.value.length - 1]!.id : undefined
      }
      messages.value.push(userMessage)
      
      // 调用API发送消息
      const response = await chatApi.sendMessage({
        thread_id: currentThread.value.id,
        content
      })
      
      // 用服务器返回的消息替换临时消息
      messages.value[messages.value.length - 1] = response.data.user_message
      
      // 添加AI回复
      if (response.data.ai_message) {
        messages.value.push(response.data.ai_message)
      }
      
      error.value = null
    } catch (err: unknown) {
      console.error('发送消息失败:', err)
      error.value = err instanceof Error ? err.message : '发送消息失败'
      // 移除临时消息
      messages.value.pop()
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // 创建分支
  const createBranch = async (parentMessageId: number, newMessageContent?: string): Promise<Thread | null> => {
    if (!currentConversation.value) {
      console.error('没有活跃的对话')
      return null
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
      console.error('创建分支失败:', err)
      error.value = err instanceof Error ? err.message : '创建分支失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // 切换线程
  const switchThread = async (threadId: number): Promise<void> => {
    try {
      isLoading.value = true
      
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

  // 获取分支树
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

  // 清除错误
  const clearError = (): void => {
    error.value = null
  }

  return {
    // 状态
    conversations,
    currentConversation,
    currentThread,
    messages,
    isLoading,
    threadTree,
    error,
    
    // 计算属性
    threadPath,
    
    // 动作
    fetchConversations,
    createConversation,
    switchConversation,
    updateConversationTitle,
    deleteConversation,
    fetchMessages,
    sendMessage,
    createBranch,
    switchThread,
    fetchThreadTree,
    clearError
  }
})