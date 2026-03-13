<template>
  <div v-if="showHint" class="branch-depth-hint" :class="hintClass">
    <div class="hint-icon">{{ depthIcon }}</div>
    <div class="hint-content">
      <div class="hint-title">{{ title }}</div>
      <div class="hint-description">{{ description }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  currentDepth: number
  maxDepth?: number
}

const props = withDefaults(defineProps<Props>(), {
  maxDepth: 3
})

const showHint = computed(() => {
  return props.currentDepth >= 0
})

const remainingDepth = computed(() => {
  return Math.max(0, props.maxDepth - props.currentDepth)
})

const title = computed(() => {
  if (props.currentDepth === 0) return '主分支'
  return `第 ${props.currentDepth} 层分支`
})

const description = computed(() => {
  if (remainingDepth.value === 0) {
    return '已达到最大深度限制，无法创建更深层的分支'
  }
  return `还可创建 ${remainingDepth.value} 层分支`
})

const hintClass = computed(() => {
  if (remainingDepth.value === 0) return 'hint-max-depth'
  if (remainingDepth.value === 1) return 'hint-warning'
  return 'hint-normal'
})

const depthIcon = computed(() => {
  const icons = ['🌳', '🌿', '🍃', '🍂']
  return icons[Math.min(props.currentDepth, icons.length - 1)] || '📌'
})
</script>

<style scoped>
.branch-depth-hint {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  margin: 12px 0;
  border: 1px solid;
  transition: all 0.3s ease;
}

.hint-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.hint-content {
  flex: 1;
}

.hint-title {
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 2px;
}

.hint-description {
  font-size: 12px;
  opacity: 0.8;
}

/* 不同状态下的样式 */
.hint-normal {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-color: #bae6fd;
  color: #0369a1;
}

.hint-warning {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-color: #fcd34d;
  color: #92400e;
}

.hint-max-depth {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  border-color: #fca5a5;
  color: #dc2626;
  animation: gentle-pulse 3s infinite;
}

@keyframes gentle-pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.9;
  }
}
</style>