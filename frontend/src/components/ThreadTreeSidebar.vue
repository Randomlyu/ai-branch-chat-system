<template>
  <aside class="sidebar right-sidebar" :class="{ 'collapsed': isCollapsed }">
    <div class="sidebar-header">
      <h3>分支树</h3>
      <div class="sidebar-header-actions">
        <!-- 在非收起状态下显示刷新按钮 -->
        <button 
          v-if="!isCollapsed" 
          class="btn-refresh" 
          @click="handleRefresh" 
          title="刷新分支树"
          :disabled="isStreaming"
        >
          <svg class="refresh-icon" viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/>
          </svg>
        </button>
        <!-- 收起按钮 -->
        <button class="btn-toggle-sidebar" @click="handleToggleCollapse" :title="isCollapsed ? '展开侧边栏' : '收起侧边栏'">
          <svg v-if="isCollapsed" class="sidebar-icon" viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" />
          </svg>
          <svg v-else class="sidebar-icon" viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z" />
          </svg>
        </button>
      </div>
    </div>
    <div class="thread-tree">
      <div v-if="threadTree.length === 0" class="empty-tip">
        当前对话暂无分支
      </div>
      <ThreadTreeNode
        v-for="thread in threadTree"
        :key="thread.id"
        :thread="thread"
        :current-thread-id="currentThreadId"
        @switch="handleSwitchThread"
        @deleted="handleThreadDeleted"
        @request-delete="handleRequestDeleteThread"
      />
    </div>
  </aside>
</template>

<script setup lang="ts">
import ThreadTreeNode from '@/components/ThreadTreeNode.vue'
import type { ThreadTree } from '@/types/chat'

// 定义Props
defineProps<{
  threadTree: ThreadTree[]
  currentThreadId?: number
  isCollapsed: boolean
  isStreaming: boolean
}>()

// 定义Events
const emit = defineEmits<{
  refresh: []
  'toggle-collapse': []
  switch: [threadId: number]
  'thread-deleted': [threadId: number, parentThreadId?: number | null]
  'request-delete-thread': [payload: { 
    threadId: number; 
    threadTitle: string;
    canDelete?: boolean;
    reason?: string;
  }]
}>()

// 事件处理方法
const handleRefresh = () => {
  emit('refresh')
}

const handleToggleCollapse = () => {
  emit('toggle-collapse')
}

const handleSwitchThread = (threadId: number) => {
  emit('switch', threadId)
}

const handleThreadDeleted = (threadId: number, parentThreadId?: number | null) => {
  emit('thread-deleted', threadId, parentThreadId)
}

// 处理删除线程请求
const handleRequestDeleteThread = (payload: { 
  threadId: number; 
  threadTitle: string;
  canDelete?: boolean;
  reason?: string;
}) => {
  emit('request-delete-thread', payload)
}
</script>

<style scoped>
/* 右侧边栏 */
.right-sidebar {
  width: 380px;
  min-width: 380px;
  border-left: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.08);
}

/* 右侧边栏收起状态 */
.right-sidebar.collapsed {
  width: 48px;
  min-width: 48px;
  overflow: visible;
}

/* 右侧边栏收起时隐藏内容 */
.right-sidebar.collapsed .sidebar-header h3,
.right-sidebar.collapsed .thread-tree,
.right-sidebar.collapsed .btn-refresh {
  display: none;
}

.sidebar.collapsed {
  min-height: 100vh;
  position: relative;
}

/* 侧边栏头部 */
.sidebar-header {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.9);
}

.sidebar.collapsed .sidebar-header {
  padding: 16px 8px;
  justify-content: center;
  border-bottom: none;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #202123;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sidebar.collapsed .sidebar-header-actions {
  flex-direction: column;
  gap: 8px;
  align-items: center;
  justify-content: center;
  width: 100%;
}

/* 侧边栏内容区域 */
.thread-tree {
  flex: 1;
  overflow-y: auto;
  padding: 12px 20px;
  min-height: 0;
}

/* 刷新按钮 - 现代AI风格 */
.btn-refresh {
  width: 36px;
  height: 36px;
  border: none;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(34, 197, 94, 0.1));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: #10b981;
  padding: 0;
  flex-shrink: 0;
  backdrop-filter: blur(8px);
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);
}

.btn-refresh::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.btn-refresh:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.25), rgba(34, 197, 94, 0.2));
  color: #059669;
  transform: scale(1.05) translateY(-1px);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3);
}

.btn-refresh:hover:not(:disabled)::before {
  opacity: 1;
}

.btn-refresh:active:not(:disabled) {
  transform: scale(0.95) translateY(0);
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.1);
}

/* 刷新图标动画 */
.refresh-icon {
  transition: transform 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  width: 20px;
  height: 20px;
}

.btn-refresh:not(:disabled):hover .refresh-icon {
  transform: rotate(180deg);
}

.btn-refresh:disabled .refresh-icon {
  animation: spin 2s linear infinite;
  opacity: 0.7;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 收起按钮样式 - 现代AI风格 */
.btn-toggle-sidebar {
  width: 36px;
  height: 36px;
  border: none;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.15), rgba(6, 182, 212, 0.1));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: #0ea5e9;
  padding: 0;
  flex-shrink: 0;
  backdrop-filter: blur(8px);
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.2);
}

.btn-toggle-sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.btn-toggle-sidebar:hover {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.25), rgba(6, 182, 212, 0.2));
  color: #0284c7;
  transform: scale(1.05) translateY(-1px);
  box-shadow: 0 8px 20px rgba(14, 165, 233, 0.3);
}

.btn-toggle-sidebar:hover::before {
  opacity: 1;
}

.btn-toggle-sidebar:active {
  transform: scale(0.95) translateY(0);
}

/* 图标动画 */
.sidebar-icon {
  transition: transform 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  width: 20px;
  height: 20px;
}

.btn-toggle-sidebar:hover .sidebar-icon {
  transform: scale(1.2);
}

/* 空状态提示 */
.empty-tip {
  padding: 20px 12px;
  text-align: center;
  color: #999;
  font-size: 13px;
  font-style: italic;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  margin: 8px 0;
  border: 1px dashed rgba(0, 0, 0, 0.1);
}
</style>