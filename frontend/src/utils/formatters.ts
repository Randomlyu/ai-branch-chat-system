/**
 * 时间格式化工具函数
 * @param timestamp 时间戳或日期对象
 * @returns 格式化的时间字符串 (HH:MM)
 */
export const formatTime = (timestamp: string | Date | undefined): string => {
  if (!timestamp) return '--'
  const date = new Date(timestamp)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

/**
 * 消息内容格式化（换行符转换为<br>）
 * @param content 消息内容
 * @returns 格式化后的HTML字符串
 */
export const formatMessage = (content: string): string => {
  return content.replace(/\n/g, '<br>')
}

/**
 * 数字格式化（千分位、百万位）
 * @param num 要格式化的数字
 * @returns 格式化后的字符串
 */
export const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

/**
 * 获取模型显示名称
 * @param model 模型标识符
 * @returns 用户友好的显示名称
 */
export const getModelDisplayName = (model: string): string => {
  const modelNames: Record<string, string> = {
    'deepseek-ai/DeepSeek-V3': 'DeepSeek V3',
    'gpt-3.5-turbo': 'GPT-3.5 Turbo',
    'gpt-4': 'GPT-4',
    'mock': '模拟模式',
    '模拟模式': '模拟模式'
  }
  return modelNames[model] || model
}