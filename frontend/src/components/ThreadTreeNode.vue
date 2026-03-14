<template>
  <div class="thread-node" :style="{ marginLeft: `${(thread.depth || 0) * 12}px` }">
    <div
      class="thread-item"
      :class="{ 
        active: thread.id === currentThreadId,
        'max-depth': thread.depth !== undefined && thread.depth >= 3 
      }"
      @click="handleItemClick"
      @mouseenter="handleMouseEnter"
      @mouseleave="handleMouseLeave"
    >
      <!-- 操作区域（左侧） -->
      <div class="thread-actions-left">
        <!-- 展开/折叠按钮 -->
        <span 
          v-if="hasChildren" 
          class="thread-toggle" 
          @click.stop="toggle"
          :title="isExpanded ? '折叠子分支' : '展开子分支'"
        >
          <svg v-if="isExpanded" class="thread-toggle-icon" viewBox="0 0 24 24" width="12" height="12">
            <path fill="currentColor" d="M7.41,15.41L12,10.83L16.59,15.41L18,14L12,8L6,14L7.41,15.41Z"/>
          </svg>
          <svg v-else class="thread-toggle-icon" viewBox="0 0 24 24" width="12" height="12">
            <path fill="currentColor" d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z"/>
          </svg>
        </span>
        
        <!-- 分支图标占位（无子分支时） -->
        <span v-else class="thread-icon-placeholder"></span>
      </div>
      
      <!-- 内容区域（中间） -->
      <div class="thread-content">
        <!-- 分支图标 -->
        <div class="thread-icon-container" :title="getThreadTooltip(thread)">
          <svg v-if="thread.depth === 0" class="thread-icon" viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M12,2A2,2 0 0,1 14,4C14,4.74 13.6,5.39 13,5.73V7H14A7,7 0 0,1 21,14H22A1,1 0 0,1 23,15V18A1,1 0 0,1 22,19H21V20A2,2 0 0,1 19,22H5A2,2 0 0,1 3,20V19H2A1,1 0 0,1 1,18V15A1,1 0 0,1 2,14H3A7,7 0 0,1 10,7H11V5.73C10.4,5.39 10,4.74 10,4A2,2 0 0,1 12,2M7.5,13A2.5,2.5 0 0,0 5,15.5A2.5,2.5 0 0,0 7.5,18A2.5,2.5 0 0,0 10,15.5A2.5,2.5 0 0,0 7.5,13M16.5,13A2.5,2.5 0 0,0 14,15.5A2.5,2.5 0 0,0 16.5,18A2.5,2.5 0 0,0 19,15.5A2.5,2.5 0 0,0 16.5,13Z"/>
          </svg>
          <svg v-else-if="thread.depth === 1" class="thread-icon" viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M3,13A9,9 0 0,0 12,22C12,17 7.97,13 3,13M12,5.5A2.5,2.5 0 0,1 14.5,8A2.5,2.5 0 0,1 12,10.5A2.5,2.5 0 0,1 9.5,8A2.5,2.5 0 0,1 12,5.5M5.6,10.25A2.5,2.5 0 0,0 8.1,12.75C8.1,14.26 6.76,15.6 5.25,15.6C3.74,15.6 2.4,14.26 2.4,12.75C2.4,11.24 3.74,9.9 5.25,9.9C6.25,9.9 7.1,10.55 7.44,11.5H10.56C10.9,10.55 11.75,9.9 12.75,9.9C14.26,9.9 15.6,11.24 15.6,12.75C15.6,14.26 14.26,15.6 12.75,15.6C11.24,15.6 9.9,14.26 9.9,12.75C9.9,12.65 9.9,12.55 9.91,12.45H7.44C7.29,12.93 6.81,13.28 6.25,13.28C5.56,13.28 5,12.72 5,12.03C5,11.34 5.56,10.78 6.25,10.78C6.85,10.78 7.37,11.21 7.5,11.78H10.5C10.63,11.21 11.15,10.78 11.75,10.78C12.44,10.78 13,11.34 13,12.03C13,12.72 12.44,13.28 11.75,13.28C11.19,13.28 10.71,12.93 10.56,12.45H8.09C8.1,12.55 8.1,12.65 8.1,12.75C8.1,13.47 7.47,14.1 6.75,14.1C6.03,14.1 5.4,13.47 5.4,12.75C5.4,12.03 6.03,11.4 6.75,11.4C7.47,11.4 8.1,12.03 8.1,12.75C8.1,13.47 7.47,14.1 6.75,14.1C6.03,14.1 5.4,13.47 5.4,12.75C5.4,12.03 6.03,11.4 6.75,11.4C7.47,11.4 8.1,12.03 8.1,12.75C8.1,13.47 7.47,14.1 6.75,14.1C6.03,14.1 5.4,13.47 5.4,12.75C5.4,12.03 6.03,11.4 6.75,11.4C7.47,11.4 8.1,12.03 8.1,12.75C8.1,13.47 7.47,14.1 6.75,14.1C6.03,14.1 5.4,13.47 5.4,12.75C5.4,12.03 6.03,11.4 6.75,11.4C7.47,11.4 8.1,12.03 8.1,12.75C8.1,13.47 7.47,14.1 6.75,14.1C6.03,14.1 5.4,13.47 5.4,12.75C5.4,12.03 6.03,11.4 6.75,11.4C7.47,11.4 8.1,12.03 8.1,12.75C8.1,13.47 7.47,14.1 6.75,14.1C6.03,14.1 5.4,13.47 5.4,12.75C5.4,12.03 6.03,11.4 6.75,11.4C7.47,11.4 8.1,12.03 8.1,12.75C8.1,13.47 7.47,14.1 6.75,14.1C6.03,14.1 5.4,13.47 5.4,12.75C5.4,12.03 6.03,11.4 6.75,11.4C7.47,11.4 8.1,12.03 8.1,12.75C8.1,13.47 7.47,14.1 6.75,14.1C6.03,14.1 5.4,13.47 5.4,12.75A2.5,2.5 0 0,0 5.6,10.25Z"/>
          </svg>
          <svg v-else-if="thread.depth === 2" class="thread-icon" viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M12,2A2,2 0 0,1 14,4C14,4.74 13.6,5.39 13,5.73V7H14A7,7 0 0,1 21,14H22A1,1 0 0,1 23,15V18A1,1 0 0,1 22,19H21V20A2,2 0 0,1 19,22H5A2,2 0 0,1 3,20V19H2A1,1 0 0,1 1,18V15A1,1 0 0,1 2,14H3A7,7 0 0,1 10,7H11V5.73C10.4,5.39 10,4.74 10,4A2,2 0 0,1 12,2M7.5,13A1.5,1.5 0 0,0 6,14.5A1.5,1.5 0 0,0 7.5,16A1.5,1.5 0 0,0 9,14.5A1.5,1.5 0 0,0 7.5,13M16.5,13A1.5,1.5 0 0,0 15,14.5A1.5,1.5 0 0,0 16.5,16A1.5,1.5 0 0,0 18,14.5A1.5,1.5 0 0,0 16.5,13M12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17A2,2 0 0,0 14,15A2,2 0 0,0 12,13Z"/>
          </svg>
          <svg v-else class="thread-icon" viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4M12,10.5A1.5,1.5 0 0,1 13.5,12A1.5,1.5 0 0,1 12,13.5A1.5,1.5 0 0,1 10.5,12A1.5,1.5 0 0,1 12,10.5M7.5,10.5A1.5,1.5 0 0,1 9,12A1.5,1.5 0 0,1 7.5,13.5A1.5,1.5 0 0,1 6,12A1.5,1.5 0 0,1 7.5,10.5M16.5,10.5A1.5,1.5 0 0,1 18,12A1.5,1.5 0 0,1 16.5,13.5A1.5,1.5 0 0,1 15,12A1.5,1.5 0 0,1 16.5,10.5Z"/>
          </svg>
        </div>
        
        <!-- 标题区域 -->
        <div class="thread-title-container" :title="thread.title">
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
        
        <!-- 深度徽章 -->
        <div 
          v-if="thread.depth !== undefined" 
          class="depth-badge-container"
          :title="getDepthTooltip(thread.depth)"
        >
          <span class="depth-badge" :class="getDepthClass(thread.depth)">
            {{ thread.depth }}
            <span v-if="thread.depth >= 3" class="depth-limit-icon">!</span>
          </span>
        </div>
      </div>
      
      <!-- 操作区域（右侧） -->
      <div class="thread-actions-right">
        <!-- 三点菜单按钮 -->
        <div 
          v-if="showMenuButton" 
          class="thread-actions-container"
        >
          <button 
            class="thread-actions-btn"
            :class="{ 'is-active': isMenuVisible }"
            @click.stop="toggleMenu"
            aria-label="更多操作"
            @mouseenter="onMenuButtonMouseEnter"
            @mouseleave="onMenuButtonMouseLeave"
          >
            <svg class="thread-actions-icon" viewBox="0 0 24 24" width="16" height="16">
              <path fill="currentColor" d="M12,16A2,2 0 0,1 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18A2,2 0 0,1 12,16M12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10M12,4A2,2 0 0,1 14,6A2,2 0 0,1 12,8A2,2 0 0,1 10,6A2,2 0 0,1 12,4Z"/>
            </svg>
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

const emit = defineEmits<{
  switch: [threadId: number]
}>()

// 状态
const isExpanded = ref(true)
const isHovering = ref(false)
const isMenuVisible = ref(false)
const isMenuHovering = ref(false)
const isMenuButtonHovering = ref(false)
const isRenaming = ref(false)
const renameInput = ref('')
const renameInputRef = ref<HTMLInputElement>()

// 计算属性
const hasChildren = computed(() => {
  return props.thread.children && props.thread.children.length > 0
})

// 菜单按钮显示条件
const showMenuButton = computed(() => {
  // 重命名时不显示菜单按钮
  if (isRenaming.value) return false
  
  // 始终显示菜单按钮（无论是否有子分支）
  return true
})

// 方法
const handleItemClick = (event: MouseEvent) => {
  // 如果点击的是操作按钮区域，不触发切换分支
  const target = event.target as HTMLElement
  if (target.closest('.thread-actions-left') || 
      target.closest('.thread-actions-right') ||
      target.closest('.rename-input')) {
    return
  }
  
  // 否则切换到当前分支
  if (!isRenaming.value) {
    emit('switch', props.thread.id)
  }
}

const handleMouseEnter = () => {
  isHovering.value = true
}

const handleMouseLeave = () => {
  isHovering.value = false
}

const toggle = (event: MouseEvent) => {
  event.stopPropagation()
  isExpanded.value = !isExpanded.value
}

const getThreadTitle = (thread: ThreadTree) => {
  if (thread.title) return thread.title
  
  if (thread.depth === 0) return '主对话'
  if (thread.depth !== undefined) {
    return `分支 ${thread.depth}.${thread.id}`
  }
  return `分支-${thread.id}`
}

const getDepthClass = (depth?: number) => {
  if (depth === undefined) return 'depth-unknown'
  
  if (depth >= 3) return 'depth-max-limit'
  
  const depthClasses = ['depth-0', 'depth-1', 'depth-2', 'depth-3']
  return depthClasses[Math.min(depth, depthClasses.length - 1)] || 'depth-unknown'
}

const getDepthTooltip = (depth?: number) => {
  if (depth === undefined) return '深度未知'
  
  const depthNames = ['主分支', '第1层分支', '第2层分支', '第3层分支']
  const name = depthNames[Math.min(depth, depthNames.length - 1)] || `第${depth}层分支`
  
  if (depth >= 3) {
    return `${name}（已达到深度限制）`
  }
  
  return `${name}（还可创建${3 - depth}层分支）`
}

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
const toggleMenu = (event: MouseEvent) => {
  event.stopPropagation()
  isMenuVisible.value = !isMenuVisible.value
}

const onMenuButtonMouseEnter = () => {
  isMenuButtonHovering.value = true
}

const onMenuButtonMouseLeave = () => {
  isMenuButtonHovering.value = false
  // 如果鼠标离开按钮，但不在菜单上，延迟关闭
  setTimeout(() => {
    if (!isMenuHovering.value) {
      isMenuVisible.value = false
    }
  }, 150)
}

const onMenuMouseEnter = () => {
  isMenuHovering.value = true
}

const onMenuMouseLeave = () => {
  isMenuHovering.value = false
  // 如果鼠标离开菜单，但不在按钮上，延迟关闭
  setTimeout(() => {
    if (!isMenuButtonHovering.value) {
      isMenuVisible.value = false
    }
  }, 150)
}

// 开始重命名
const onStartRename = (event: MouseEvent) => {
  event.stopPropagation()
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
  }
}

// 取消重命名
const cancelRename = () => {
  isRenaming.value = false
  renameInput.value = ''
}

// 输入框失去焦点处理
const onInputBlur = (event: FocusEvent) => {
  setTimeout(() => {
    const relatedTarget = event.relatedTarget as HTMLElement
    if (!relatedTarget?.closest('.thread-title-container')) {
      confirmRename()
    }
  }, 100)
}

// 监听全局点击
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.thread-actions-container') && !target.closest('.thread-actions-menu')) {
    isMenuVisible.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.thread-node {
  margin-left: 4px;
  padding-left: 8px;
  position: relative;
}

.thread-node:before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 1px;
  height: 100%;
  background: rgba(0, 0, 0, 0.1);
}

.thread-node:last-child:before {
  height: 20px;
}

.thread-item {
  padding: 6px 8px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
  transition: all 0.2s ease;
  font-size: 13px;
  position: relative;
  min-height: 36px;
  background: white;
  border: 1px solid transparent;
}

.thread-item:hover {
  background: #f8fafc;
  border-color: #e2e8f0;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.thread-item.active {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.12) 0%, rgba(59, 130, 246, 0.08) 100%);
  border-color: rgba(59, 130, 246, 0.3);
  color: #1d4ed8;
  font-weight: 500;
}

.thread-item.max-depth {
  opacity: 0.7;
  background: #f9fafb;
}

.thread-actions-left {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
}

.thread-toggle {
  width: 20px;
  height: 20px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #6b7280;
  border: 1px solid transparent;
}

.thread-toggle:hover {
  background: rgba(0, 0, 0, 0.1);
  color: #374151;
  border-color: rgba(0, 0, 0, 0.1);
  transform: scale(1.05);
}

.thread-toggle-icon {
  width: 12px;
  height: 12px;
  display: block;
  transition: transform 0.2s ease;
}

.thread-icon-placeholder {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.thread-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  overflow: hidden;
  width: 100%;
}

.thread-icon-container {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  color: #6b7280;
}

.thread-item.active .thread-icon-container {
  color: #3b82f6;
}

.thread-icon {
  width: 16px;
  height: 16px;
  display: block;
}

.thread-title-container {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  font-size: 13px;
  color: #374151;
  padding: 2px 0;
  position: relative;
  width: calc(100% - 120px); /* 确保标题区域有足够的空间 */
}

.thread-item.active .thread-title-container {
  color: #1d4ed8;
}

.thread-title {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
  font-size: 12px;
  font-weight: 500;
}

/* 悬停时显示完整标题 */
.thread-item:hover .thread-title {
  position: absolute;
  background: white;
  padding: 6px 10px;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-width: 250px;
  border: 1px solid #e5e7eb;
  white-space: normal;
  word-break: break-word;
  overflow: visible;
  left: 0;
  top: 100%;
  margin-top: 2px;
}

.rename-input {
  width: 100%;
  padding: 4px 8px;
  border: 2px solid #3b82f6;
  border-radius: 6px;
  background: white;
  font-size: 13px;
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  color: #374151;
  min-width: 0;
}

.depth-badge-container {
  flex-shrink: 0;
  margin-right: 4px;
  width: 30px; /* 固定宽度避免挤压标题 */
  display: flex;
  justify-content: center;
}

.depth-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  padding: 0 6px;
  transition: all 0.2s ease;
  border: 1px solid;
  position: relative;
  overflow: hidden;
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
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

/* 深度颜色方案 */
.depth-0 {
  color: #2563eb;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-color: rgba(37, 99, 235, 0.3);
}

.depth-1 {
  color: #059669;
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  border-color: rgba(5, 150, 105, 0.3);
}

.depth-2 {
  color: #d97706;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-color: rgba(217, 119, 6, 0.3);
}

.depth-3, .depth-max-limit {
  color: #dc2626;
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  border-color: rgba(220, 38, 38, 0.3);
  animation: pulse 2s infinite;
}

.depth-unknown {
  color: #6b7280;
  background: #f3f4f6;
  border-color: #d1d5db;
}

.depth-limit-icon {
  font-size: 10px;
  margin-left: 2px;
  font-weight: 800;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

.thread-actions-right {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.2s ease;
  width: 28px; /* 固定宽度 */
  display: flex;
  justify-content: flex-end;
}

.thread-item:hover .thread-actions-right,
.thread-item.active .thread-actions-right {
  opacity: 1;
}

.thread-actions-container {
  position: relative;
  display: inline-block;
  z-index: 1001; /* 确保菜单在最上层 */
}

.thread-actions-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 6px;
  cursor: pointer;
  padding: 0;
  transition: all 0.2s ease;
  color: #6b7280;
  position: relative;
  z-index: 1002;
}

.thread-actions-btn:hover {
  background: rgba(0, 0, 0, 0.1);
  color: #374151;
  transform: scale(1.05);
}

.thread-actions-btn.is-active {
  background: rgba(0, 0, 0, 0.15);
  color: #374151;
}

.thread-actions-icon {
  width: 16px;
  height: 16px;
  display: block;
}

.thread-actions-menu {
  position: absolute;
  z-index: 1003; /* 更高的z-index，确保在最上层 */
  top: 0; /* 修改为从顶部开始 */
  right: 28px; /* 在按钮左侧显示 */
  min-width: 100px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 4px 0;
  animation: slideIn 0.2s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
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
  gap: 8px;
  white-space: nowrap;
}

.thread-actions-item:hover {
  background-color: #f3f4f6;
}

.thread-children {
  margin-left: 4px; /* 减少子节点缩进 */
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>