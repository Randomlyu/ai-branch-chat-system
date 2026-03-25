<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="handleOverlayClick">
      <div class="modal-content" :class="sizeClass">
        <!-- 标题区域 -->
        <div v-if="title" class="modal-header">
          <h3 class="modal-title">{{ title }}</h3>
          <button v-if="showClose" class="modal-close" @click="handleCancel" title="关闭">
            <svg class="close-icon" viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>
        
        <!-- 内容区域 -->
        <div class="modal-body">
          <div v-if="icon" class="modal-icon">
            <svg v-if="icon === 'warning'" class="icon-warning" viewBox="0 0 24 24" width="48" height="48">
              <path fill="currentColor" d="M12,2L1,21H23M12,6L19.53,19H4.47M11,10V14H13V10M11,16V18H13V16"/>
            </svg>
            <svg v-else-if="icon === 'danger'" class="icon-danger" viewBox="0 0 24 24" width="48" height="48">
              <path fill="currentColor" d="M12,2C6.47,2,2,6.47,2,12C2,17.53,6.47,22,12,22C17.53,22,22,17.53,22,12C22,6.47,17.53,6,12,2ZM12,20C7.59,20,4,16.41,4,12C4,7.59,7.59,4,12,4C16.41,4,20,7.59,20,12C20,16.41,16.41,20,12,20ZM12,7C10.9,7,10,7.9,10,9C10,10.1,10.9,11,12,11C13.1,11,14,10.1,14,9C14,7.9,13.1,7,12,7Z"/>
            </svg>
            <svg v-else-if="icon === 'info'" class="icon-info" viewBox="0 0 24 24" width="48" height="48">
              <path fill="currentColor" d="M11,9H13V7H11M12,20C7.59,20,4,16.41,4,12C4,7.59,7.59,4,12,4C16.41,4,20,7.59,20,12C20,16.41,16.41,20,12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,17H13V11H11V17Z"/>
            </svg>
          </div>
          
          <div v-if="message" class="modal-message">{{ message }}</div>
          
          <!-- 插槽内容 -->
          <slot></slot>
        </div>
        
        <!-- 操作按钮区域 -->
        <div class="modal-actions">
          <button 
            v-if="showCancel" 
            class="btn-cancel" 
            @click="handleCancel"
            :disabled="loading"
          >
            {{ cancelText }}
          </button>
          <button 
            class="btn-confirm" 
            :class="{ danger, loading: loading }"
            @click="handleConfirm"
            :disabled="loading"
          >
            <span v-if="loading" class="loading-spinner"></span>
            {{ loading ? loadingText : confirmText }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export interface ConfirmDialogProps {
  visible: boolean
  title?: string
  message?: string
  confirmText?: string
  cancelText?: string
  loadingText?: string
  danger?: boolean
  loading?: boolean
  showCancel?: boolean
  showClose?: boolean
  icon?: 'warning' | 'danger' | 'info'
  size?: 'small' | 'medium' | 'large'
  closeOnOverlay?: boolean
}

const props = withDefaults(defineProps<ConfirmDialogProps>(), {
  confirmText: '确认',
  cancelText: '取消',
  loadingText: '处理中...',
  danger: false,
  loading: false,
  showCancel: true,
  showClose: true,
  size: 'medium',
  closeOnOverlay: true
})

const emit = defineEmits<{
  'update:visible': [visible: boolean]
  confirm: []
  cancel: []
}>()

// 计算大小类
const sizeClass = computed(() => {
  return `modal-${props.size}`
})

// 事件处理
const handleConfirm = () => {
  if (!props.loading) {
    emit('confirm')
  }
}

const handleCancel = () => {
  if (!props.loading) {
    emit('cancel')
    emit('update:visible', false)
  }
}

const handleOverlayClick = () => {
  if (props.closeOnOverlay && !props.loading) {
    handleCancel()
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9998;
  animation: fadeIn 0.2s ease;
}

.modal-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(0, 0, 0, 0.1);
  max-width: 95%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

/* 尺寸控制 */
.modal-small {
  width: 400px;
}

.modal-medium {
  width: 500px;
}

.modal-large {
  width: 600px;
}

/* 头部样式 */
.modal-header {
  padding: 20px 24px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #666;
  padding: 0;
}

.modal-close:hover {
  background: rgba(0, 0, 0, 0.1);
  color: #1a1a1a;
  transform: rotate(90deg);
}

.close-icon {
  width: 20px;
  height: 20px;
  display: block;
}

/* 内容区域 */
.modal-body {
  padding: 24px;
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 16px;
}

.modal-icon {
  margin-bottom: 8px;
}

.icon-warning {
  color: #f59e0b;
}

.icon-danger {
  color: #ef4444;
}

.icon-info {
  color: #3b82f6;
}

.modal-message {
  color: #4b5563;
  line-height: 1.6;
  font-size: 15px;
  white-space: pre-line;
  word-break: break-word;
}

/* 操作按钮区域 */
.modal-actions {
  padding: 20px 24px 24px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.btn-cancel,
.btn-confirm {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  outline: none;
  min-width: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-cancel {
  background: #f3f4f6;
  color: #4b5563;
  border-color: #d1d5db;
}

.btn-cancel:hover:not(:disabled) {
  background: #e5e7eb;
  color: #374151;
  border-color: #9ca3af;
}

.btn-cancel:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-confirm {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.btn-confirm:hover:not(:disabled) {
  background: #2563eb;
  border-color: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.btn-confirm:active:not(:disabled) {
  transform: translateY(0);
}

.btn-confirm.danger {
  background: #ef4444;
  border-color: #ef4444;
}

.btn-confirm.danger:hover:not(:disabled) {
  background: #dc2626;
  border-color: #dc2626;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.btn-confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 加载动画 */
.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.btn-confirm.danger .loading-spinner {
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
}

/* 动画 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 响应式调整 */
@media (max-width: 640px) {
  .modal-content {
    width: 90%;
    min-width: auto;
  }
  
  .modal-small,
  .modal-medium,
  .modal-large {
    width: 90%;
  }
  
  .modal-body {
    padding: 20px 16px;
  }
  
  .modal-actions {
    padding: 16px;
  }
}
</style>