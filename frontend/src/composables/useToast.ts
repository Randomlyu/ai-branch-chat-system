// frontend/src/composables/useToast.ts
import { ref } from 'vue'

export type ToastType = 'success' | 'error'

export interface ToastState {
  show: boolean
  message: string
  type: ToastType
}

export function useToast() {
  const toast = ref<ToastState>({
    show: false,
    message: '',
    type: 'success'
  })

  /**
   * 显示Toast提示
   * @param message 提示消息
   * @param type 提示类型，默认'success'
   * @param duration 显示时长(ms)，默认3000
   */
  const showToast = (message: string, type: ToastType = 'success', duration = 3000) => {
    // 先重置状态
    toast.value.show = false
    
    // 等待下一次 DOM 更新
    setTimeout(() => {
      toast.value = { show: true, message, type }
      
      // 自动隐藏（但新的组件会自己处理自动隐藏）
      if (duration > 0) {
        setTimeout(() => {
          toast.value.show = false
        }, duration)
      }
    }, 50) // 短暂延迟确保动画重置
  }

  /**
   * 隐藏Toast提示
   */
  const hideToast = () => {
    toast.value.show = false
  }

  return {
    toast,
    showToast,
    hideToast
  }
}