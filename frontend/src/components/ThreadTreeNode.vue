<template>
  <div class="thread-node">
    <div
      class="thread-item"
      :class="{ active: thread.id === currentThreadId }"
      @click="$emit('switch', thread.id)"
    >
      <span class="thread-icon">🌿</span>
      <span class="thread-title">{{ thread.title || `分支-${thread.id}` }}</span>
      <!-- 仅新增：安全显示深度（后端返回depth时显示） -->
      <span v-if="thread.depth !== undefined" class="depth-badge">
        {{ thread.depth }}
      </span>
      <span 
        v-if="thread.children?.length" 
        class="thread-toggle" 
        @click.stop="toggle"
      >
        {{ isExpanded ? '−' : '+' }}
      </span>
    </div>
    <div v-if="isExpanded && thread.children?.length" class="thread-children">
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
import { ref } from 'vue'

// 严格遵循您已定义的接口（仅扩展depth字段）
interface ThreadTree {
  id: number
  title?: string
  parent_message_id?: number
  children?: ThreadTree[]
  depth?: number  // ✅ 仅新增此字段（与后端一致）
}

defineProps<{
  thread: ThreadTree
  currentThreadId?: number
}>()

defineEmits<{
  switch: [threadId: number]
}>()

const isExpanded = ref(true)
const toggle = () => {
  isExpanded.value = !isExpanded.value
}
</script>

<style scoped>
/* 仅新增深度徽章样式（与现有样式兼容） */
.depth-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #e0e7ff;
  color: #4f46e5;
  font-size: 10px;
  font-weight: 600;
  margin-left: 4px;
}

/* 保留原有样式（无改动） */
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
  transition: background 0.2s;
  font-size: 13px;
}
.thread-item:hover {
  background: rgba(0, 0, 0, 0.05);
}
.thread-item.active {
  background: rgba(59, 130, 246, 0.12);
  color: #3b82f6;
  font-weight: 500;
}
.thread-icon {
  font-size: 12px;
  flex-shrink: 0;
}
.thread-title {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.thread-toggle {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  flex-shrink: 0;
}
.thread-children {
  margin-left: 8px;
}
</style>