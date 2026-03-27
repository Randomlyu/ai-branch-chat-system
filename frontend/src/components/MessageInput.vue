<template>
  <div class="input-container">
    <!-- Token用量警告 -->
    <div v-if="isTokenLimitReached" class="token-limit-warning">
      <span class="warning-icon">⚠️</span>
      <span class="warning-text">当日API用量已达上限，请明日再试</span>
    </div>
    
    <!-- 添加相对定位的包装器，用于放置深度提示 -->
    <div class="input-wrapper">
      <!-- 深度提示组件 -->
      <BranchDepthHint 
        v-if="currentThread"
        :currentDepth="currentThread.depth || 0"
        :maxDepth="3"
      />
      
      <div class="input-area-wrapper">
        <textarea
          v-model="localUserInput"
          :placeholder="inputPlaceholder"
          @keydown.enter.exact.prevent="handleSend"
          @keydown.shift.enter.exact="handleShiftEnter"
          :disabled="isLoading || isStreaming || isTokenLimitReached"
          rows="1"
          ref="inputTextarea"
          class="message-input"
          @input="autoResizeTextarea"
        ></textarea>
        <div class="send-controls">
          <!-- 编辑模式下的取消按钮 -->
          <button
            v-if="isEditMode"
            class="btn-cancel"
            @click="handleCancelEdit"
            :disabled="isLoading || isStreaming"
            title="取消编辑"
          >
            <span class="icon cancel-icon">✕</span>
          </button>
          <button
            class="btn-send"
            @click="handleButtonClick"
            :disabled="!isButtonEnabled"
            :class="{ 
              disabled: !isButtonEnabled,
              streaming: isStreaming
            }"
            :title="sendButtonTitle"
          >
            <span v-if="isStreaming" class="icon stop-icon" title="停止生成">⏹️</span>
            <span v-else-if="isEditMode" class="icon update-icon">✓</span>
            <span v-else class="icon send-icon">⬆</span>
          </button>
        </div>
      </div>
    </div>
    
    <div class="input-footer">
      <div class="model-info">
        当前模型: <strong>{{ formattedModelName }}</strong>
      </div>
      <div class="input-hints">
        <span class="hint">对话ID: {{ conversationId || '--' }}</span>
        <span class="hint">线程ID: {{ threadId || '--' }}</span>
        <span v-if="isTokenLimitReached" class="hint warning">用量已达上限</span>
        <span v-else-if="remainingTokens" class="hint">剩余: {{ remainingTokens }} tokens</span>
        <span v-if="isEditMode" class="hint editing">正在编辑消息</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import BranchDepthHint from '@/components/BranchDepthHint.vue'
import type { Thread } from '@/types/chat'

// 定义AI用量的接口
interface AIUsage {
  current_date: string
  total_tokens: number
  max_daily_tokens: number
  remaining_tokens: number
  // 添加其他已知的可能属性
  last_reset?: string
  available_models?: string[]
  default_model?: string
  streaming_enabled?: boolean
}

// 定义Props
const props = defineProps<{
  // 输入文本
  userInput: string
  // 状态
  isLoading: boolean
  isStreaming: boolean
  isTokenLimitReached: boolean
  // 模型信息
  currentModel: string
  // 对话线程信息 - 接受 null
  currentThread?: Thread | null
  currentConversation?: { id?: number } | null
  // 用量信息 - 接受 null
  aiUsage?: AIUsage | null
  // 计算属性
  canSend: boolean
  inputPlaceholder: string
  sendButtonTitle: string
  formattedModelName: string
  remainingTokens: string
  // ===== 新增：编辑模式相关 =====
  isEditMode: boolean
  // ============================
}>()

// 定义事件
const emit = defineEmits<{
  'update:userInput': [value: string]
  send: []
  stop: []
  // ===== 新增：取消编辑事件 =====
  cancelEdit: []
  // ============================
}>()

// 本地数据 - 使用计算属性来同步props和emit
const localUserInput = computed({
  get: () => props.userInput,
  set: (value) => emit('update:userInput', value)
})

// 计算属性
const conversationId = computed(() => props.currentConversation?.id)
const threadId = computed(() => props.currentThread?.id)
const isButtonEnabled = computed(() => {
  if (props.isStreaming) {
    // 流式生成时，停止按钮始终可用
    return true
  }
  // 非流式生成时，使用 canSend
  return props.canSend
})

// 模板引用
const inputTextarea = ref<HTMLTextAreaElement>()

/**
 * 处理发送消息
 */
const handleSend = () => {
  if (props.canSend) {
    emit('send')
  }
}

/**
 * 处理按钮点击
 */
const handleButtonClick = () => {
  if (props.isStreaming) {
    // 流式生成时，触发停止
    emit('stop')
  } else {
    // 非流式生成时，触发发送
    handleSend()
  }
}

/**
 * 处理Shift+Enter换行
 */
const handleShiftEnter = () => {
  localUserInput.value += '\n'
  // 调整文本框高度
  nextTick(() => {
    autoResizeTextarea()
  })
}

/**
 * 自动调整文本框高度
 */
const autoResizeTextarea = () => {
  const textarea = inputTextarea.value
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = `${textarea.scrollHeight}px`
  }
}

// ===== 新增：取消编辑 =====
/**
 * 处理取消编辑
 */
const handleCancelEdit = () => {
  emit('cancelEdit')
}
// ========================

// 暴露方法供父组件调用
defineExpose({
  /**
   * 聚焦输入框
   */
  focusInput: () => {
    nextTick(() => {
      inputTextarea.value?.focus()
    })
  },
  /**
   * 重置文本框高度
   */
  resetTextareaHeight: () => {
    const textarea = inputTextarea.value
    if (textarea) {
      textarea.style.height = 'auto'
    }
  },
  /**
   * 获取输入框的值
   */
  getInputValue: () => localUserInput.value
})

// 监听props变化，调整文本框
watch(() => props.userInput, () => {
  nextTick(() => {
    autoResizeTextarea()
  })
})

// 监听流式状态变化
watch(() => props.isStreaming, (newVal) => {
  if (!newVal) {
    // 流式生成结束，聚焦输入框
    nextTick(() => {
      inputTextarea.value?.focus()
    })
  }
})
</script>

<style scoped>
/* 输入容器 */
.input-container {
  padding: 20px 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.95);
  flex-shrink: 0;
  width: 100%;
  transition: padding 0.3s ease;
}

/* 输入包装器 */
.input-wrapper {
  position: relative;
  width: 100%;
}

/* 输入区域包装器 */
.input-area-wrapper {
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: 12px;
  max-width: 100%;
  margin: 0 auto;
  width: 100%;
  transition: max-width 0.3s ease;
}

/* 消息输入框 */
.message-input {
  flex: 1;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 12px;
  padding: 16px 20px;
  font-size: 15px;
  line-height: 1.5;
  resize: none;
  max-height: 200px;
  transition: border 0.2s, box-shadow 0.2s;
  background: white;
  outline: none;
  font-family: inherit;
  min-height: 56px;
  width: 100%;
}

.message-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.message-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

/* 发送控制区域 */
.send-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

/* 取消按钮 */
.btn-cancel {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: #6b7280;
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
  flex-shrink: 0;
  font-size: 18px;
}

.btn-cancel:hover:not(:disabled) {
  background: #4b5563;
  transform: translateY(-1px);
}

.btn-cancel:active:not(:disabled) {
  transform: scale(0.95);
}

.btn-cancel:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* 发送按钮 */
.btn-send {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: #3b82f6;
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
  flex-shrink: 0;
  font-size: 18px;
}

.btn-send:hover:not(.disabled) {
  background: #2563eb;
  transform: translateY(-1px);
}

.btn-send:active:not(.disabled) {
  transform: scale(0.95);
}

.btn-send.disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-send.streaming {
  background: #dc2626;
}

.btn-send.streaming:hover:not(.disabled) {
  background: #b91c1c;
}

/* 编辑模式下的发送按钮样式 */
.btn-send:not(.streaming) {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.btn-send:not(.streaming):hover:not(.disabled) {
  background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
}

/* 输入页脚 */
.input-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  font-size: 12px;
  color: #888;
  flex-wrap: wrap;
  gap: 8px;
}

.model-info {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.model-info strong {
  color: #10b981;
}

.input-hints {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.hint {
  color: #888;
}

.hint.warning {
  color: #dc2626;
  font-weight: 500;
}

.hint.editing {
  color: #f59e0b;
  font-weight: 500;
  background: rgba(245, 158, 11, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

/* Token限制警告 */
.token-limit-warning {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 8px;
  margin-bottom: 12px;
  color: #dc2626;
  font-size: 13px;
  animation: slideDown 0.3s ease;
}

.warning-icon {
  font-size: 16px;
}

.warning-text {
  flex: 1;
  font-weight: 500;
}

.streaming-badge {
  display: inline-block;
  padding: 2px 6px;
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  margin-left: 6px;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

/* 图标 */
.icon {
  font-size: 16px;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.stop-icon {
  font-size: 16px;
}

.send-icon {
  font-size: 20px;
  font-weight: bold;
}

.update-icon {
  font-size: 20px;
  font-weight: bold;
}

.cancel-icon {
  font-size: 18px;
  font-weight: bold;
}

/* 动画 */
@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>