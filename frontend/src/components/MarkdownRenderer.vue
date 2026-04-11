<template>
  <div 
    class="markdown-content" 
    :class="{ 'streaming': isStreaming }"
    ref="contentRef"
    v-html="renderedContent"
  ></div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, nextTick, onUpdated } from 'vue'
import { renderMarkdown, initCodeCopyButtons, renderStreamingMarkdown } from '@/utils/markdown-renderer'

const props = defineProps<{
  content: string
  isStreaming?: boolean
}>()

const contentRef = ref<HTMLElement>()
const renderedContent = ref('')

// 渲染Markdown
const renderContent = () => {
  if (props.isStreaming) {
    // 流式生成时使用特殊处理
    renderedContent.value = renderStreamingMarkdown(props.content)
  } else {
    renderedContent.value = renderMarkdown(props.content)
  }
  
  // 在下次DOM更新后初始化代码复制按钮
  nextTick(() => {
    if (contentRef.value) {
      initCodeCopyButtons(contentRef.value)
    }
  })
}

// 监听内容变化
watch(() => props.content, renderContent, { immediate: true })

// 组件挂载时初始化
onMounted(() => {
  renderContent()
})

// DOM更新后重新初始化复制按钮
onUpdated(() => {
  if (contentRef.value) {
    initCodeCopyButtons(contentRef.value)
  }
})
</script>

<style scoped>
.markdown-content {
  width: 100%;
  overflow-x: auto; /* 允许水平滚动 */
  word-wrap: break-word; /* 长单词换行 */
  overflow-wrap: break-word; /* 溢出换行 */
}

/* 流式生成时的特殊样式 */
.markdown-content.streaming {
  min-height: 1.5em; /* 确保有最小高度 */
}
</style>