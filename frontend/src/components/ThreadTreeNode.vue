<template>
  <div class="thread-node">
    <div
      class="thread-item"
      :class="{ 
        active: thread.id === currentThreadId,
        'max-depth': thread.depth !== undefined && thread.depth >= 3 
      }"
      @click="$emit('switch', thread.id)"
    >
      <span class="thread-icon" :title="getThreadTooltip(thread)">
        {{ getThreadIcon(thread.depth) }}
      </span>
      <span class="thread-title">{{ getThreadTitle(thread) }}</span>
      
      <!-- 深度徽章：根据深度显示不同状态 -->
      <span 
        v-if="thread.depth !== undefined" 
        class="depth-badge"
        :class="getDepthClass(thread.depth)"
        :title="getDepthTooltip(thread.depth)"
      >
        {{ thread.depth }}
        <span v-if="thread.depth >= 3" class="depth-limit-icon">🚫</span>
      </span>
      
      <span 
        v-if="hasChildren" 
        class="thread-toggle" 
        @click.stop="toggle"
        :title="isExpanded ? '折叠子分支' : '展开子分支'"
      >
        {{ isExpanded ? '−' : '+' }}
      </span>
    </div>
    <div v-if="isExpanded && hasChildren" class="thread-children">
      <ThreadTreeNode
        v-for="child in thread.children"
        :key="child.id"
        :thread="child"
        :current-thread-id="currentThreadId"
        @switch="$emit('switch', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// 根据项目结构，应该从 types 目录导入类型定义
// 但为了代码完整性，这里保持接口定义
interface ThreadTree {
  id: number
  title?: string
  parent_message_id?: number
  children?: ThreadTree[]
  depth?: number
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

const props = defineProps<{
  thread: ThreadTree
  currentThreadId?: number
}>()

// 修正：移除未使用的 emit 变量定义，只保留事件声明
defineEmits<{
  switch: [threadId: number]
}>()

const isExpanded = ref(true)

const toggle = () => {
  isExpanded.value = !isExpanded.value
}

// 计算属性：是否有子节点
const hasChildren = computed(() => {
  return props.thread.children && props.thread.children.length > 0
})

// 方法：获取线程图标
const getThreadIcon = (depth?: number) => {
  if (depth === undefined) return '🌿'
  const icons = ['🌳', '🌿', '🍃', '🍂'] // 主分支到最深分支的不同图标
  return icons[Math.min(depth, icons.length - 1)] || '🌿'
}

// 方法：获取线程标题
const getThreadTitle = (thread: ThreadTree) => {
  if (thread.title) return thread.title
  
  // 根据深度生成默认标题
  if (thread.depth === 0) return '主分支'
  if (thread.depth !== undefined) {
    return `分支 ${thread.depth}.${thread.id}`
  }
  return `分支-${thread.id}`
}

// 方法：获取深度CSS类
const getDepthClass = (depth?: number) => {
  if (depth === undefined) return 'depth-unknown'
  
  if (depth >= 3) return 'depth-max-limit' // 达到限制的样式
  
  // 不同深度的颜色区分
  const depthClasses = ['depth-0', 'depth-1', 'depth-2', 'depth-3']
  return depthClasses[Math.min(depth, depthClasses.length - 1)] || 'depth-unknown'
}

// 方法：获取深度提示文本
const getDepthTooltip = (depth?: number) => {
  if (depth === undefined) return '深度未知'
  
  const depthNames = ['主分支', '第1层分支', '第2层分支', '第3层分支']
  const name = depthNames[Math.min(depth, depthNames.length - 1)] || `第${depth}层分支`
  
  if (depth >= 3) {
    return `${name}（已达到深度限制）`
  }
  
  return `${name}（还可创建${3 - depth}层分支）`
}

// 方法：获取线程完整提示
const getThreadTooltip = (thread: ThreadTree) => {
  const parts: string[] = []
  
  if (thread.title) {
    parts.push(`标题：${thread.title}`)
  }
  
  if (thread.depth !== undefined) {
    parts.push(getDepthTooltip(thread.depth))
  }
  
  if (thread.created_at) {
    const date = new Date(thread.created_at).toLocaleDateString()
    parts.push(`创建：${date}`)
  }
  
  return parts.join(' | ')
}
</script>

<style scoped>
/* 样式保持不变，同之前的版本 */
.thread-node {
  margin-left: 16px;
  border-left: 1px dashed rgba(0, 0, 0, 0.15);
  padding-left: 8px;
}

.thread-item {
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  transition: all 0.2s ease;
  font-size: 13px;
  position: relative;
}

.thread-item:hover {
  background: rgba(0, 0, 0, 0.05);
  transform: translateX(2px);
}

.thread-item.active {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.12) 0%, rgba(59, 130, 246, 0.08) 100%);
  color: #3b82f6;
  font-weight: 500;
  border-left: 2px solid #3b82f6;
  margin-left: -2px;
}

.thread-item.max-depth {
  opacity: 0.7;
  filter: grayscale(0.3);
}

.thread-icon {
  font-size: 14px;
  flex-shrink: 0;
  width: 20px;
  text-align: center;
}

.thread-title {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

/* 深度徽章样式 */
.depth-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 18px;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 600;
  margin-left: 4px;
  padding: 0 6px;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  position: relative;
  overflow: hidden;
}

.depth-badge::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: currentColor;
  opacity: 0.1;
  z-index: 0;
}

.depth-badge > * {
  position: relative;
  z-index: 1;
}

/* 不同深度的颜色方案 */
.depth-0 { /* 主分支 */
  color: #2563eb;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-color: #93c5fd;
}

.depth-1 { /* 第1层分支 */
  color: #059669;
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  border-color: #6ee7b7;
}

.depth-2 { /* 第2层分支 */
  color: #d97706;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-color: #fcd34d;
}

.depth-3, .depth-max-limit { /* 第3层分支 - 达到上限 */
  color: #dc2626;
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  border-color: #fca5a5;
  animation: pulse 2s infinite;
}

.depth-unknown { /* 未知深度 */
  color: #6b7280;
  background: #f3f4f6;
  border-color: #d1d5db;
}

.depth-limit-icon {
  font-size: 8px;
  margin-left: 2px;
  opacity: 0.8;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

/* 展开/折叠按钮 */
.thread-toggle {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.08) 0%, rgba(0, 0, 0, 0.04) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  flex-shrink: 0;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #6b7280;
}

.thread-toggle:hover {
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.12) 0%, rgba(0, 0, 0, 0.08) 100%);
  transform: scale(1.1);
  color: #374151;
}

.thread-children {
  margin-left: 8px;
  animation: slideDown 0.3s ease;
}

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