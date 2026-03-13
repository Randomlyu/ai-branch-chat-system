<template>
  <!-- 三点菜单按钮 -->
  <div class="thread-actions" @click.stop>
    <button 
      class="thread-actions-btn"
      :class="{ 'is-active': isMenuVisible }"
      @click="toggleMenu"
      @mouseenter="onMouseEnter"
      @mouseleave="onMouseLeave"
      aria-label="更多操作"
    >
      <span class="thread-actions-dots"></span>
    </button>
    
    <!-- 下拉菜单 -->
    <div 
      v-if="isMenuVisible" 
      class="thread-actions-menu"
      :style="menuStyle"
      @mouseenter="onMouseEnter"
      @mouseleave="onMouseLeave"
    >
      <button class="thread-actions-item" @click="onRename">
        <svg class="thread-actions-icon" viewBox="0 0 24 24" width="16" height="16">
          <path fill="currentColor" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
        </svg>
        重命名
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps<{
  threadId: number
  threadTitle: string
  position?: 'top-right' | 'bottom-right'
}>()

const emit = defineEmits<{
  rename: [threadId: number, currentTitle: string]
}>()

const isMenuVisible = ref(false)
const isHovering = ref(false)

// 控制菜单位置
const menuStyle = computed(() => {
  if (props.position === 'bottom-right') {
    return { top: '100%', right: '0' }
  }
  return { bottom: '100%', right: '0' } // 默认top-right
})

// 切换菜单显示
const toggleMenu = () => {
  isMenuVisible.value = !isMenuVisible.value
}

// 鼠标事件处理
const onMouseEnter = () => {
  isHovering.value = true
}

const onMouseLeave = () => {
  isHovering.value = false
  // 延迟关闭，防止快速切换时闪烁
  setTimeout(() => {
    if (!isHovering.value) {
      isMenuVisible.value = false
    }
  }, 100)
}

// 重命名点击处理
const onRename = () => {
  isMenuVisible.value = false
  emit('rename', props.threadId, props.threadTitle)
}

// 点击外部关闭菜单
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.thread-actions')) {
    isMenuVisible.value = false
  }
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
</style>