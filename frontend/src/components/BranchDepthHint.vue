<template>
  <!-- 在输入框上方显示，但不遮挡输入框 -->
  <div 
    v-if="showHint" 
    class="branch-depth-hint" 
    :class="hintClass"
    :title="hintTooltip"
  >
    <!-- SVG图标，与前端其他图标风格统一 -->
    <div class="hint-icon">
      <svg v-if="currentDepth === 0" class="depth-icon" viewBox="0 0 24 24" width="16" height="16">
        <path fill="currentColor" d="M12,2A2,2 0 0,1 14,4C14,4.74 13.6,5.39 13,5.73V7H14A7,7 0 0,1 21,14H22A1,1 0 0,1 23,15V18A1,1 0 0,1 22,19H21V20A2,2 0 0,1 19,22H5A2,2 0 0,1 3,20V19H2A1,1 0 0,1 1,18V15A1,1 0 0,1 2,14H3A7,7 0 0,1 10,7H11V5.73C10.4,5.39 10,4.74 10,4A2,2 0 0,1 12,2M7.5,13A2.5,2.5 0 0,0 5,15.5A2.5,2.5 0 0,0 7.5,18A2.5,2.5 0 0,0 10,15.5A2.5,2.5 0 0,0 7.5,13M16.5,13A2.5,2.5 0 0,0 14,15.5A2.5,2.5 0 0,0 16.5,18A2.5,2.5 0 0,0 19,15.5A2.5,2.5 0 0,0 16.5,13Z"/>
      </svg>
      <svg v-else-if="currentDepth === 1" class="depth-icon" viewBox="0 0 24 24" width="16" height="16">
        <path fill="currentColor" d="M9.5,3A2.5,2.5 0 0,1 12,5.5A2.5,2.5 0 0,1 9.5,8A2.5,2.5 0 0,1 7,5.5A2.5,2.5 0 0,1 9.5,3M14.5,3A2.5,2.5 0 0,1 17,5.5A2.5,2.5 0 0,1 14.5,8A2.5,2.5 0 0,1 12,5.5A2.5,2.5 0 0,1 14.5,3M9.5,9C11,9 12,10 12,11.5C12,13 11,14 9.5,14C8,14 7,13 7,11.5C7,10 8,9 9.5,9M14.5,9C16,9 17,10 17,11.5C17,13 16,14 14.5,14C13,14 12,13 12,11.5C12,10 13,9 14.5,9M4.5,13A2.5,2.5 0 0,1 7,15.5A2.5,2.5 0 0,1 4.5,18A2.5,2.5 0 0,1 2,15.5A2.5,2.5 0 0,1 4.5,13M19.5,13A2.5,2.5 0 0,1 22,15.5A2.5,2.5 0 0,1 19.5,18A2.5,2.5 0 0,1 17,15.5A2.5,2.5 0 0,1 19.5,13Z"/>
      </svg>
      <svg v-else-if="currentDepth === 2" class="depth-icon" viewBox="0 0 24 24" width="16" height="16">
        <path fill="currentColor" d="M12,2A2,2 0 0,1 14,4C14,4.74 13.6,5.39 13,5.73V7H14A7,7 0 0,1 21,14H22A1,1 0 0,1 23,15V18A1,1 0 0,1 22,19H21V20A2,2 0 0,1 19,22H5A2,2 0 0,1 3,20V19H2A1,1 0 0,1 1,18V15A1,1 0 0,1 2,14H3A7,7 0 0,1 10,7H11V5.73C10.4,5.39 10,4.74 10,4A2,2 0 0,1 12,2M7.5,13A1.5,1.5 0 0,0 6,14.5A1.5,1.5 0 0,0 7.5,16A1.5,1.5 0 0,0 9,14.5A1.5,1.5 0 0,0 7.5,13M16.5,13A1.5,1.5 0 0,0 15,14.5A1.5,1.5 0 0,0 16.5,16A1.5,1.5 0 0,0 18,14.5A1.5,1.5 0 0,0 16.5,13M12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17A2,2 0 0,0 14,15A2,2 0 0,0 12,13Z"/>
      </svg>
      <svg v-else class="depth-icon" viewBox="0 0 24 24" width="16" height="16">
        <path fill="currentColor" d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4M12,10.5A1.5,1.5 0 0,1 13.5,12A1.5,1.5 0 0,1 12,13.5A1.5,1.5 0 0,1 10.5,12A1.5,1.5 0 0,1 12,10.5M7.5,10.5A1.5,1.5 0 0,1 9,12A1.5,1.5 0 0,1 7.5,13.5A1.5,1.5 0 0,1 6,12A1.5,1.5 0 0,1 7.5,10.5M16.5,10.5A1.5,1.5 0 0,1 18,12A1.5,1.5 0 0,1 16.5,13.5A1.5,1.5 0 0,1 15,12A1.5,1.5 0 0,1 16.5,10.5Z"/>
      </svg>
    </div>
    
    <!-- 简洁的内容显示 -->
    <div class="hint-content">
      <div class="hint-text">{{ displayText }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  /** 当前分支深度 */
  currentDepth: number
  /** 最大允许深度，默认为3 */
  maxDepth?: number
}

const props = withDefaults(defineProps<Props>(), {
  maxDepth: 3
})

// 计算剩余可创建深度
const remainingDepth = computed(() => {
  return Math.max(0, props.maxDepth - props.currentDepth)
})

// 判断是否显示提示
const showHint = computed(() => {
  // 只在有分支树或深度>0时显示
  return props.currentDepth >= 0 && props.currentDepth > 0
})

// 简洁的显示文本
const displayText = computed(() => {
  if (remainingDepth.value === 0) {
    return '已达最大深度'
  }
  return `${props.currentDepth}/${props.maxDepth}`
})

// 鼠标悬停时的完整提示文本
const hintTooltip = computed(() => {
  if (remainingDepth.value === 0) {
    return '已达到最大深度限制（3层），无法创建更深层的分支'
  }
  
  return `当前处于第${props.currentDepth}层分支，还可创建${remainingDepth.value}层新分支`
})

// 提示类型样式
const hintClass = computed(() => {
  if (remainingDepth.value === 0) return 'hint-max-depth'
  if (remainingDepth.value === 1) return 'hint-warning'
  return 'hint-normal'
})
</script>

<style scoped>
.branch-depth-hint {
  /* 绝对定位，放在输入框内部上方 */
  position: absolute;
  top: -28px; /* 放在输入框上方 */
  left: 50%;
  transform: translateX(-50%);
  
  /* 紧凑布局 */
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
  z-index: 5;
  min-width: 80px;
  max-width: 120px;
  pointer-events: none; /* 不干扰下方点击 */
  user-select: none;
  opacity: 0.85;
  cursor: help; /* 悬停时显示帮助光标 */
  
  /* 响应式调整 */
  @media (max-width: 768px) {
    padding: 3px 8px;
    min-width: 70px;
    max-width: 100px;
  }
}

/* 悬停时高亮 */
.branch-depth-hint:hover {
  opacity: 1;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  pointer-events: auto;
  transform: translateX(-50%) translateY(-1px);
}

/* 深度图标 */
.hint-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.depth-icon {
  width: 12px;
  height: 12px;
  display: block;
  transition: all 0.2s ease;
}

/* 悬停时图标轻微放大 */
.branch-depth-hint:hover .depth-icon {
  transform: scale(1.1);
}

/* 提示内容 */
.hint-content {
  flex: 1;
  min-width: 0;
}

.hint-text {
  font-size: 11px;
  font-weight: 500;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.2px;
}

/* 不同深度状态样式 */
.hint-normal {
  border-color: rgba(59, 130, 246, 0.3);
  background: linear-gradient(135deg, 
    rgba(239, 246, 255, 0.95) 0%, 
    rgba(219, 234, 254, 0.95) 100%);
  color: #3b82f6;
}

.hint-warning {
  border-color: rgba(245, 158, 11, 0.3);
  background: linear-gradient(135deg, 
    rgba(254, 243, 199, 0.95) 0%, 
    rgba(253, 230, 138, 0.95) 100%);
  color: #d97706;
  animation: subtle-pulse 3s ease-in-out infinite;
}

.hint-max-depth {
  border-color: rgba(239, 68, 68, 0.3);
  background: linear-gradient(135deg, 
    rgba(254, 226, 226, 0.95) 0%, 
    rgba(254, 202, 202, 0.95) 100%);
  color: #dc2626;
  animation: gentle-pulse 2s ease-in-out infinite;
}

/* 动画效果 */
@keyframes subtle-pulse {
  0%, 100% { 
    opacity: 0.9;
    box-shadow: 0 1px 3px rgba(245, 158, 11, 0.2);
  }
  50% { 
    opacity: 1;
    box-shadow: 0 1px 3px rgba(245, 158, 11, 0.3);
  }
}

@keyframes gentle-pulse {
  0%, 100% { 
    opacity: 0.9;
    box-shadow: 0 1px 3px rgba(239, 68, 68, 0.2);
  }
  50% { 
    opacity: 1;
    box-shadow: 0 1px 3px rgba(239, 68, 68, 0.3);
  }
}
</style>