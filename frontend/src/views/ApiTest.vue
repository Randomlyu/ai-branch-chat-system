<template>
  <div style="padding: 20px;">
    <h1>AI分支对话系统测试</h1>
    
    <div style="margin: 20px 0;">
      <button @click="testConversations">测试对话列表</button>
      <button @click="testCreateConversation">测试创建对话</button>
      <button @click="testSendMessage" :disabled="!currentThread">测试发送消息</button>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
      <div>
        <h3>状态</h3>
        <pre>{{ {
          isLoading,
          conversations: conversations.length,
          currentConversation: currentConversation?.id,
          currentThread: currentThread?.id,
          messages: messages.length
        } }}</pre>
      </div>
      
      <div>
        <h3>对话列表</h3>
        <ul>
          <li v-for="conv in conversations" :key="conv.id">
            {{ conv.id }}: {{ conv.title }}
          </li>
        </ul>
      </div>
    </div>
    
    <div v-if="error" style="color: red; margin: 20px 0;">
      错误: {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chat'

const chatStore = useChatStore()
const {
  conversations,
  currentConversation,
  currentThread,
  messages,
  isLoading,
  error
} = storeToRefs(chatStore)

const testConversations = async () => {
  console.log('开始测试获取对话列表')
  console.log('当前 store 状态:', {
    conversations: chatStore.conversations,
    isLoading: chatStore.isLoading
  })
  
  await chatStore.fetchConversations()
  
  console.log('测试完成，store 状态:', {
    conversations: chatStore.conversations,
    isLoading: chatStore.isLoading
  })
}

const testCreateConversation = async () => {
  console.log('开始测试创建对话')
  await chatStore.createConversation('测试对话')
  console.log('测试完成')
}

const testSendMessage = async () => {
  if (!currentThread.value) return
  console.log('开始测试发送消息')
  await chatStore.sendMessage('你好，这是一条测试消息')
  console.log('测试完成')
}
</script>