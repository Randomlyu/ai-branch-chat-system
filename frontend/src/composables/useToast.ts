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
    toast.value = { show: true, message, type }
    setTimeout(() => {
      toast.value.show = false
    }, duration)
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