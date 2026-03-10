<template>
  <div class="thread-node">
    <div
      class="thread-item"
      :class="{ active: thread.id === currentThreadId }"
      @click="$emit('switch', thread.id)"
    >
      <span class="thread-icon">🌿</span>
      <span class="thread-title">{{ thread.title || `分支-${thread.id}` }}</span>
      <span class="thread-toggle" v-if="thread.children && thread.children.length > 0" @click.stop="toggle">
        {{ isExpanded ? '−' : '+' }}
      </span>
    </div>
    <div v-if="isExpanded && thread.children" class="thread-children">
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

interface ThreadTree {
  id: number
  title?: string
  parent_message_id?: number
  children?: ThreadTree[]
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