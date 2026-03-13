<template>
  <div class="thread-node" :style="{ marginLeft: `${(thread.depth || 0) * 20}px` }">
    <div
      class="thread-item"
      :class="{ 
        active: thread.id === currentThreadId,
        'max-depth': thread.depth !== undefined && thread.depth >= 3 
      }"
      @click="$emit('switch', thread.id)"
      @mouseenter="isHovering = true"
      @mouseleave="isHovering = false"
    >
      <span class="thread-icon" :title="getThreadTooltip(thread)">
        {{ getThreadIcon(thread.depth) }}
      </span>
      
      <!-- 重命名输入框或标题显示 -->
      <div class="thread-title-container">
        <input
          v-if="isRenaming"
          ref="renameInputRef"
          v-model="renameInput"
          class="rename-input"
          @keyup.enter="confirmRename"
          @keyup.esc="cancelRename"
          @blur="onInputBlur"
        />
        <span v-else class="thread-title">{{ getThreadTitle(thread) }}</span>
      </div>
      
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
      
      <!-- 三点菜单（悬停时显示） -->
      <div v-if="(isHovering || isRenaming) && !isRenaming" class="thread-actions-container">
        <div class="thread-actions" @click.stop>
          <button 
            class="thread-actions-btn"
            :class="{ 'is-active': isMenuVisible }"
            @click="toggleMenu"
            aria-label="更多操作"
          >
            <span class="thread-actions-dots"></span>
          </button>
          
          <!-- 下拉菜单 -->
          <div 
            v-if="isMenuVisible" 
            class="thread-actions-menu"
            @mouseenter="onMenuMouseEnter"
            @mouseleave="onMenuMouseLeave"
          >
            <button class="thread-actions-item" @click="onStartRename">
              <svg class="thread-actions-icon" viewBox="0 0 24 24" width="16" height="16">
                <path fill="currentColor" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
              </svg>
              重命名
            </button>
          </div>
        </div>
      </div>
      
      <span 
        v-if="hasChildren" 
        class="thread-toggle" 
        @click.stop="toggle"
        :title="isExpanded ? '折叠子分支' : '展开子分支'"
      >
        {{ isExpanded ? '−' : '+' }}
      </span>
    </div>
    
    <!-- 子线程 -->
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
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useChatStore } from '../stores/chat'

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
  conversation_id?: number
}

const props = defineProps<{
  thread: ThreadTree
  currentThreadId?: number
}>()

// 事件定义
defineEmits<{
  switch: [threadId: number]
}>()

// 状态
const isExpanded = ref(true)
const isHovering = ref(false)
const isMenuVisible = ref(false)
const isMenuHovering = ref(false)
const isRenaming = ref(false)
const renameInput = ref('')
const renameInputRef = ref<HTMLInputElement>()

// 计算属性：是否有子节点
const hasChildren = computed(() => {
  return props.thread.children && props.thread.children.length > 0
})

// 切换展开/收起
const toggle = () => {
  isExpanded.value = !isExpanded.value
}

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
  if (thread.depth === 0) return '主对话'
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

// 三点菜单控制
const toggleMenu = () => {
  isMenuVisible.value = !isMenuVisible.value
}

const onMenuMouseEnter = () => {
  isMenuHovering.value = true
}

const onMenuMouseLeave = () => {
  isMenuHovering.value = false
  // 延迟关闭，防止快速切换时闪烁
  setTimeout(() => {
    if (!isMenuHovering.value) {
      isMenuVisible.value = false
    }
  }, 100)
}

// 点击外部关闭菜单
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.thread-actions')) {
    isMenuVisible.value = false
  }
}

// 开始重命名
const onStartRename = () => {
  isMenuVisible.value = false
  isRenaming.value = true
  renameInput.value = props.thread.title || getThreadTitle(props.thread)
  
  nextTick(() => {
    if (renameInputRef.value) {
      renameInputRef.value.focus()
      renameInputRef.value.select()
    }
  })
}

// 确认重命名
const confirmRename = async () => {
  if (!renameInput.value.trim()) {
    cancelRename()
    return
  }
  
  try {
    const chatStore = useChatStore()
    await chatStore.updateThread(props.thread.id, renameInput.value.trim())
    isRenaming.value = false
  } catch (error) {
    console.error('重命名失败:', error)
    // 可以在这里添加错误提示
  }
}

// 取消重命名
const cancelRename = () => {
  isRenaming.value = false
  renameInput.value = ''
}

// 输入框失去焦点处理
const onInputBlur = (event: FocusEvent) => {
  // 延迟处理，避免立即触发blur导致无法点击确认按钮
  setTimeout(() => {
    const relatedTarget = event.relatedTarget as HTMLElement
    if (!relatedTarget?.closest('.thread-title-container')) {
      confirmRename()
    }
  }, 100)
}

// 监听全局点击
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>

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

/* 新增样式 */
.thread-title-container {
  flex: 1;
  min-width: 0; /* 防止flex元素溢出 */
}

.rename-input {
  width: 100%;
  padding: 2px 6px;
  border: 2px solid #3B82F6;
  border-radius: 4px;
  background: white;
  font-size: 13px;
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.thread-actions-container {
  margin-left: 8px;
  flex-shrink: 0;
}

.thread-actions {
  position: relative;
  display: inline-block;
}

.thread-actions-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  border-radius: 4px;
  cursor: pointer;
  padding: 0;
  transition: background-color 0.2s;
}

.thread-actions-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.thread-actions-btn.is-active {
  background-color: rgba(0, 0, 0, 0.1);
}

.thread-actions-dots {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 16px;
  height: 16px;
}

.thread-actions-dots::before,
.thread-actions-dots::after {
  content: '';
  display: block;
  width: 4px;
  height: 4px;
  background-color: #6B7280;
  border-radius: 50%;
  margin: 0 auto;
}

.thread-actions-dots::before {
  margin-bottom: 2px;
}

.thread-actions-dots::after {
  margin-top: 2px;
}

.thread-actions-btn:hover .thread-actions-dots::before,
.thread-actions-btn:hover .thread-actions-dots::after {
  background-color: #374151;
}

.thread-actions-menu {
  position: absolute;
  z-index: 1000;
  top: 100%;
  right: 0;
  min-width: 120px;
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  padding: 4px 0;
}

.thread-actions-item {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 8px 12px;
  border: none;
  background: none;
  text-align: left;
  font-size: 12px;
  color: #374151;
  cursor: pointer;
  transition: background-color 0.2s;
}

.thread-actions-item:hover {
  background-color: #F3F4F6;
}

.thread-actions-icon {
  margin-right: 8px;
  color: #6B7280;
}

/* 保留原有样式 */
.thread-node {
  position: relative;
  margin-bottom: 2px;
}

.thread-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
  position: relative;
  min-height: 36px;
}

.thread-item:hover {
  background-color: #F3F4F6;
}

.thread-item.active {
  background-color: #E0E7FF;
  font-weight: 500;
}

.thread-icon {
  margin-right: 8px;
  flex-shrink: 0;
}

.thread-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  color: #374151;
}

.depth-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 10px;
  margin-right: 8px;
  font-weight: 500;
  flex-shrink: 0;
  color: white;
}

.depth-0 { background-color: #3B82F6; }
.depth-1 { background-color: #10B981; }
.depth-2 { background-color: #F59E0B; }
.depth-3, .depth-max-limit { background-color: #EF4444; }
.depth-unknown { background-color: #9CA3AF; }

.thread-toggle {
  width: 20px;
  height: 20px;
  border: 1px solid #D1D5DB;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  margin-left: 8px;
  flex-shrink: 0;
  transition: all 0.2s;
}

.thread-toggle:hover {
  border-color: #6B7280;
  background-color: #F9FAFB;
}

.thread-children {
  margin-top: 2px;
}

</style>