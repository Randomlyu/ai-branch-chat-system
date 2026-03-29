/**
 * 时间格式化工具函数
 * @param timestamp 时间字符串或日期对象
 * @returns 格式化的时间字符串 (MM/DD HH:MM)
 */
export const formatTime = (timestamp: string | Date | undefined): string => {
  if (!timestamp) return '--'
  
  try {
    // 创建Date对象
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp)
    
    // 检查是否为无效日期
    if (isNaN(date.getTime())) {
      return '--'
    }
    
    // 将UTC时间转换为北京时间（UTC+8）
    const beijingTime = new Date(date.getTime() + 8 * 60 * 60 * 1000)
    
    // 格式化为 YYYY-MM-DD HH:MM
    const month = String(beijingTime.getUTCMonth() + 1).padStart(2, '0')
    const day = String(beijingTime.getUTCDate()).padStart(2, '0')
    const hours = String(beijingTime.getUTCHours()).padStart(2, '0')
    const minutes = String(beijingTime.getUTCMinutes()).padStart(2, '0')  
    
    return `${month}/${day} ${hours}:${minutes}`
  } catch (error) {
    console.error('时间格式化错误:', error, timestamp)
    return '--'
  }
}

/**
 * 格式化完整日期时间
 * @param timestamp 时间字符串或日期对象
 * @returns 格式化的日期时间字符串 (YYYY/MM/DD HH:MM)
 */
export const formatDateTime = (timestamp: string | Date | undefined): string => {
  if (!timestamp) return '--'
  
  try {
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp)
    
    if (isNaN(date.getTime())) {
      return '--'
    }
    
    // 转换为北京时间
    const beijingTime = new Date(date.getTime() + 8 * 60 * 60 * 1000)
    
    // 格式化为 YYYY-MM-DD HH:MM
    const year = beijingTime.getUTCFullYear()
    const month = String(beijingTime.getUTCMonth() + 1).padStart(2, '0')
    const day = String(beijingTime.getUTCDate()).padStart(2, '0')
    const hours = String(beijingTime.getUTCHours()).padStart(2, '0')
    const minutes = String(beijingTime.getUTCMinutes()).padStart(2, '0')  
    
    return `${year}/${month}/${day} ${hours}:${minutes}`
  } catch (error) {
    console.error('日期时间格式化错误:', error, timestamp)
    return '--'
  }
}

/**
 * 格式化相对时间（例如：刚刚、5分钟前、今天 HH:MM、昨天 HH:MM、MM-DD HH:MM）
 * @param timestamp 时间字符串或日期对象
 * @returns 相对时间字符串
 */
export const formatRelativeTime = (timestamp: string | Date | undefined): string => {
  if (!timestamp) return '--'
  
  try {
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp)
    
    if (isNaN(date.getTime())) {
      return '--'
    }
    
    // 转换为北京时间
    const now = new Date()
    const beijingNow = new Date(now.getTime() + 8 * 60 * 60 * 1000)
    const beijingTime = new Date(date.getTime() + 8 * 60 * 60 * 1000)
    
    const diffMs = beijingNow.getTime() - beijingTime.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    
    // 今天
    if (beijingTime.getUTCDate() === beijingNow.getUTCDate() && 
        beijingTime.getUTCMonth() === beijingNow.getUTCMonth() && 
        beijingTime.getUTCFullYear() === beijingNow.getUTCFullYear()) {
      if (diffMins < 1) {
        return '刚刚'
      } else if (diffMins < 60) {
        return `${diffMins}分钟前`
      } else {
        return `${diffHours}小时前`
      }
    }
    
    // 昨天
    const yesterday = new Date(beijingNow)
    yesterday.setUTCDate(beijingNow.getUTCDate() - 1)
    
    if (beijingTime.getUTCDate() === yesterday.getUTCDate() && 
        beijingTime.getUTCMonth() === yesterday.getUTCMonth() && 
        beijingTime.getUTCFullYear() === yesterday.getUTCFullYear()) {
      const hours = String(beijingTime.getUTCHours()).padStart(2, '0')
      const minutes = String(beijingTime.getUTCMinutes()).padStart(2, '0')
      return `昨天 ${hours}:${minutes}`
    }
    
    // 更早的时间
    const month = String(beijingTime.getUTCMonth() + 1).padStart(2, '0')
    const day = String(beijingTime.getUTCDate()).padStart(2, '0')
    const hours = String(beijingTime.getUTCHours()).padStart(2, '0')
    const minutes = String(beijingTime.getUTCMinutes()).padStart(2, '0')
    
    // 如果是今年
    if (beijingTime.getUTCFullYear() === beijingNow.getUTCFullYear()) {
      return `${month}-${day} ${hours}:${minutes}`
    }
    
    // 其他年份
    const year = beijingTime.getUTCFullYear()
    return `${year}-${month}-${day} ${hours}:${minutes}`
  } catch (error) {
    console.error('相对时间格式化错误:', error, timestamp)
    return '--'
  }
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