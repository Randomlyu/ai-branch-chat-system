<template>
  <div class="chat-header">
    <!-- 左侧：标题和路径 -->
    <div class="chat-title-area">
      <!-- 主标题 -->
      <div class="title-wrapper">
        <h3 class="conversation-title">
          <span class="title-text">{{ conversationTitle }}</span>
          <span v-if="isStreaming" class="streaming-indicator">
            <span class="streaming-dot"></span>
            正在生成
          </span>
        </h3>
      </div>
      
      <!-- 线程路径 - 简洁面包屑 -->
      <div v-if="threadPath.length > 0" class="thread-path-simple">
        <div class="breadcrumb-container">
          <div 
            v-for="(thread, idx) in threadPath" 
            :key="thread.id"
            class="breadcrumb-item"
            :class="{ 'current': idx === threadPath.length - 1 }"
          >
            <button 
              v-if="idx < threadPath.length - 1"
              class="breadcrumb-link"
              @click="handleSwitchThread(thread.id)"
              :title="`切换到: ${thread.title || '分支' + (idx + 1)}`"
            >
              <span class="breadcrumb-text">{{ formatThreadTitle(thread) }}</span>
              <span v-if="idx < threadPath.length - 1" class="breadcrumb-separator">/</span>
            </button>
            <div v-else class="breadcrumb-current">
              <span class="breadcrumb-text">{{ formatThreadTitle(thread) }}</span>
              <span v-if="currentThreadDepth !== undefined" class="depth-indicator">
                深度 {{ currentThreadDepth }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 右侧：控制区域 -->
    <div class="chat-controls">
      <!-- 简洁模型选择器 -->
      <div v-if="availableModels.length > 0" class="model-selector-simple">
        <select 
          v-model="selectedModel" 
          @change="handleModelChange"
          class="model-select-simple"
          :disabled="isStreaming"
        >
          <option 
            v-for="model in availableModels" 
            :key="model" 
            :value="model"
          >
            {{ getModelDisplayName(model) }}
          </option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { getModelDisplayName } from '@/utils/formatters'
import type { Conversation, Thread } from '@/types/chat'

// 定义 ThreadPath 类型
interface ThreadPath {
  id: number
  title?: string
  depth?: number
}

const props = defineProps<{
  currentConversation: Conversation | null
  currentThread: Thread | null
  threadPath: ThreadPath[]
  availableModels: string[]
  currentModel: string
  isMockModeAvailable: boolean
  isStreaming: boolean
}>()

const emit = defineEmits<{
  'switch-thread': [threadId: number]
  'model-change': [model: string]
}>()

// 本地模型选择
const selectedModel = ref(props.currentModel)

// 监听props变化更新本地值
watch(() => props.currentModel, (newVal) => {
  selectedModel.value = newVal
})

// 计算属性
const conversationTitle = computed(() => {
  return props.currentConversation?.title || '新对话'
})

const currentThreadDepth = computed(() => {
  return props.currentThread?.depth
})

// 方法
const formatThreadTitle = (thread: ThreadPath) => {
  if (thread.title) return thread.title
  
  // 如果是主线程
  if (thread.depth === 0) return '主对话'
  
  // 其他分支
  return `分支${thread.depth || 1}`
}

// 事件处理方法
const handleSwitchThread = (threadId: number) => {
  emit('switch-thread', threadId)
}

const handleModelChange = () => {
  emit('model-change', selectedModel.value)
}
</script>

<style scoped>
.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #ffffff;
  backdrop-filter: blur(8px);
  flex-shrink: 0;
  width: 100%;
  position: relative;
  z-index: 5;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* 左侧区域 */
.chat-title-area {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.conversation-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 32px;
}

.title-text {
  color: #1a1a1a;
  padding: 2px 0;
  letter-spacing: -0.01em;
}

.streaming-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: #f0f9ff;
  border: 1px solid #e0f2fe;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  color: #0284c7;
  animation: pulse 2s infinite;
}

.streaming-dot {
  width: 8px;
  height: 8px;
  background: #0ea5e9;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

/* 简洁线程路径 */
.thread-path-simple {
  display: flex;
  align-items: center;
}

.breadcrumb-container {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  padding: 2px 0;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #666;
  font-size: 13px;
  transition: all 0.2s ease;
}

.breadcrumb-item.current {
  color: #1a1a1a;
  font-weight: 500;
}

.breadcrumb-link {
  display: flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.2s ease;
  font: inherit;
  outline: none;
}

.breadcrumb-link:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #2563eb;
}

.breadcrumb-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
  line-height: 1.4;
}

.breadcrumb-separator {
  color: #999;
  margin-left: 4px;
  opacity: 0.6;
}

.breadcrumb-current {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 2px 6px;
}

.depth-indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 8px;
  background: #f3f4f6;
  color: #6b7280;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  border: 1px solid #e5e7eb;
}

/* 右侧控制区域 */
.chat-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

/* 简洁模型选择器 */
.model-selector-simple {
  position: relative;
  min-width: 160px;
}

.model-select-simple {
  width: 100%;
  padding: 8px 12px;
  padding-right: 32px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #ffffff;
  color: #1a1a1a;
  font-size: 13px;
  font-weight: 400;
  outline: none;
  cursor: pointer;
  appearance: none;
  transition: all 0.2s ease;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 16px;
}

.model-select-simple:hover {
  border-color: #9ca3af;
  background-color: #f9fafb;
}

.model-select-simple:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.model-select-simple:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #f9fafb;
}

.model-select-simple option {
  padding: 8px 12px;
  background: white;
  color: #1a1a1a;
  font-size: 13px;
}

.model-select-simple option:disabled {
  color: #9ca3af;
  background: #f9fafb;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .chat-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .chat-controls {
    width: 100%;
  }
  
  .model-selector-simple {
    min-width: 100%;
  }
}

@media (max-width: 768px) {
  .chat-header {
    padding: 12px 16px;
  }
  
  .conversation-title {
    font-size: 16px;
  }
  
  .breadcrumb-text {
    max-width: 100px;
  }
  
  .breadcrumb-current {
    gap: 4px;
  }
  
  .depth-indicator {
    font-size: 10px;
    padding: 2px 6px;
  }
}
</style>