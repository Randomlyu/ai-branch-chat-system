<template>
  <div 
    class="markdown-content" 
    :class="{
      'streaming': isStreaming,
      'rendering': isRendering,
      'has-error': hasError
    }"
    ref="contentRef"
  >
    <!-- 渲染错误时的回退显示 -->
    <div v-if="hasError" class="error-fallback">
      <div class="error-icon">⚠️</div>
      <div class="error-message">内容渲染失败，显示原始文本：</div>
      <pre class="raw-content">{{ content }}</pre>
    </div>
    
    <!-- 正常渲染的内容 -->
    <div v-else v-html="renderedContent"></div>
    
    <!-- 流式生成指示器 -->
    <div v-if="isStreaming && !hasError" class="streaming-indicator">
      <span class="dot"></span>
      <span class="dot"></span>
      <span class="dot"></span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  ref, 
  watch, 
  onMounted, 
  nextTick, 
  onUpdated, 
  onBeforeUnmount,
  computed 
} from 'vue'
import { 
  renderMarkdown, 
  initCodeCopyButtons, 
  renderStreamingMarkdown,
  cleanupCodeCopyButtons 
} from '@/utils/markdown-renderer'

const props = defineProps<{
  content: string
  isStreaming?: boolean
}>()

const contentRef = ref<HTMLElement>()
const renderedContent = ref('')
const isRendering = ref(false)
const hasError = ref(false)
const lastContentLength = ref(0)
const debounceTimer = ref<number>()  // 修复：改为 number 类型
const copyButtonsInitialized = ref(false)

// 计算属性：内容是否有实际变化
const hasContentChanged = computed(() => {
  return props.content.length !== lastContentLength.value
})

// 防抖渲染
const debouncedRender = () => {
  if (debounceTimer.value) {
    clearTimeout(debounceTimer.value)
  }
  
  // 流式生成时使用更短的延迟，非流式生成时立即渲染
  const delay = props.isStreaming ? 50 : 0
  
  debounceTimer.value = setTimeout(() => {
    renderContent()
  }, delay) as unknown as number
}

// 渲染Markdown
const renderContent = async () => {
  if (!props.content) {
    renderedContent.value = ''
    hasError.value = false
    return
  }
  
  isRendering.value = true
  hasError.value = false
  
  try {
    if (props.isStreaming) {
      // 流式生成时使用特殊处理
      renderedContent.value = renderStreamingMarkdown(props.content)
    } else {
      // 非流式生成时使用标准渲染
      renderedContent.value = renderMarkdown(props.content)
    }
    
    lastContentLength.value = props.content.length
    
    // 等待DOM更新后初始化代码复制按钮
    await nextTick()
    
    if (contentRef.value && !copyButtonsInitialized.value) {
      // 只在首次或内容变化较大时初始化复制按钮
      initCodeCopyButtons(contentRef.value)
      copyButtonsInitialized.value = true
    }
  } catch (error) {
    console.error('Markdown渲染失败:', error)
    hasError.value = true
    renderedContent.value = ''
  } finally {
    isRendering.value = false
  }
}

// 优化：只在内容实际变化时重新渲染
watch(() => props.content, (newContent, oldContent) => {
  // 处理 oldContent 为 undefined 的情况（首次渲染）
  const oldLength = oldContent?.length || 0
  
  // 如果内容长度变化很小（比如流式生成的逐字增加），使用防抖
  if (props.isStreaming && Math.abs(newContent.length - oldLength) <= 5) {
    debouncedRender()
  } else {
    // 内容变化较大时立即重新渲染
    renderContent()
  }
}, { immediate: true })

// 监听流式状态变化
watch(() => props.isStreaming, (isStreaming) => {
  if (!isStreaming) {
    // 流式生成结束时，重新渲染以确保格式正确
    setTimeout(() => {
      if (hasContentChanged.value) {
        renderContent()
      }
    }, 100)
  }
})

// 组件挂载时初始化
onMounted(() => {
  if (props.content) {
    renderContent()
  }
})

// DOM更新后检查是否需要重新初始化复制按钮
onUpdated(() => {
  if (contentRef.value && !copyButtonsInitialized.value && renderedContent.value) {
    // 延迟初始化，确保DOM完全更新
    setTimeout(() => {
      if (contentRef.value) {
        initCodeCopyButtons(contentRef.value)
        copyButtonsInitialized.value = true
      }
    }, 100)
  }
})

// 组件卸载前清理
onBeforeUnmount(() => {
  if (debounceTimer.value) {
    clearTimeout(debounceTimer.value)
  }
  
  if (contentRef.value) {
    cleanupCodeCopyButtons(contentRef.value)
  }
})

// 暴露方法给父组件
defineExpose({
  getRenderedContent: () => renderedContent.value,
  hasRenderingError: () => hasError.value
})
</script>

<style scoped>
.markdown-content {
  width: 100%;
  overflow-x: auto; /* 允许水平滚动 */
  word-wrap: break-word; /* 长单词换行 */
  overflow-wrap: break-word; /* 溢出换行 */
  position: relative;
  min-height: 1.5em; /* 确保有最小高度 */
  transition: opacity 0.2s ease;
}

/* 渲染中的状态 */
.markdown-content.rendering {
  opacity: 0.8;
}

/* 流式生成时的特殊样式 */
.markdown-content.streaming {
  opacity: 0.95;
}

/* 错误状态 */
.markdown-content.has-error {
  border-left: 3px solid #ef4444;
  padding-left: 12px;
  margin-left: -12px;
  background-color: rgba(239, 68, 68, 0.05);
}

/* 错误回退样式 */
.error-fallback {
  padding: 12px;
  color: #6b7280;
  font-size: 13px;
  line-height: 1.5;
}

.error-icon {
  font-size: 18px;
  margin-bottom: 8px;
}

.error-message {
  color: #ef4444;
  font-weight: 500;
  margin-bottom: 8px;
}

.raw-content {
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  color: #374151;
  margin: 0;
  max-height: 200px;
  overflow-y: auto;
}

/* 流式生成指示器 */
.streaming-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 0;
  opacity: 0.7;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 0.7; }
}

.streaming-indicator .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #6b7280;
  animation: pulse 1.4s infinite ease-in-out both;
}

.streaming-indicator .dot:nth-child(1) { animation-delay: -0.32s; }
.streaming-indicator .dot:nth-child(2) { animation-delay: -0.16s; }
.streaming-indicator .dot:nth-child(3) { animation-delay: 0s; }

@keyframes pulse {
  0%, 80%, 100% { 
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% { 
    transform: scale(1.1);
    opacity: 1;
  }
}

/* 响应式调整 */
@media (max-width: 768px) {
  .markdown-content {
    font-size: 14px;
  }
  
  .raw-content {
    font-size: 11px;
    padding: 8px;
  }
}
</style>