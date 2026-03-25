<template>
  <Teleport to="body">
    <div v-if="visible" class="toast-message" :class="type">
      {{ message }}
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue'

export interface ToastProps {
  visible: boolean
  message: string
  type?: 'success' | 'error'
  duration?: number
}

const props = withDefaults(defineProps<ToastProps>(), {
  type: 'success',
  duration: 3000
})

const emit = defineEmits<{
  'update:visible': [visible: boolean]
}>()

// 自动隐藏逻辑
let timeoutId: number | null = null

const hideToast = () => {
  emit('update:visible', false)
}

onMounted(() => {
  // 当组件挂载时，如果有visible为true，则设置定时器
  if (props.visible) {
    setupAutoHide()
  }
})

// 监听visible变化
watch(() => props.visible, (newVisible) => {
  if (newVisible) {
    setupAutoHide()
  } else {
    clearTimeoutIfExists()
  }
})

function setupAutoHide() {
  clearTimeoutIfExists()
  if (props.duration > 0) {
    timeoutId = window.setTimeout(() => {
      hideToast()
    }, props.duration)
  }
}

function clearTimeoutIfExists() {
  if (timeoutId !== null) {
    clearTimeout(timeoutId)
    timeoutId = null
  }
}
</script>

<style scoped>
.toast-message {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.9);
  color: white;
  padding: 12px 20px;
  border-radius: 8px;
  z-index: 99999;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  animation: toastFadeIn 0.3s ease;
  font-size: 13px;
  font-weight: 500;
  max-width: 400px;
  text-align: center;
  word-break: break-word;
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  pointer-events: none;
}

.toast-message.success {
  background: rgba(16, 185, 129, 0.9);
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
}

.toast-message.error {
  background: rgba(239, 68, 68, 0.9);
  box-shadow: 0 8px 24px rgba(239, 68, 68, 0.3);
}

@keyframes toastFadeIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}
</style>