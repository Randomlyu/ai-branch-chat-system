import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等
    // 添加固定Token（使用alice的Token）
    config.headers.Authorization = 'Bearer dev_token_alice'
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 处理标准响应格式
    if (response.data && response.data.code !== undefined) {
      // 如果返回的数据包含code字段，判断是否成功
      if (response.data.code >= 200 && response.data.code < 300) {
        return response.data.data || response.data
      } else {
        // 业务错误
        return Promise.reject({
          code: response.data.code,
          message: response.data.message || '请求失败',
          data: response.data.data
        })
      }
    }
    return response.data
  },
  (error) => {
    // HTTP错误
    if (error.response) {
      const { status, data } = error.response
      let message = '请求失败'
      
      if (data && data.detail) {
        message = data.detail
      } else if (data && data.message) {
        message = data.message
      } else if (status === 401) {
        message = '未授权，请登录'
      } else if (status === 403) {
        message = '拒绝访问'
      } else if (status === 404) {
        message = '请求的资源不存在'
      } else if (status >= 500) {
        message = '服务器内部错误'
      }
      
      return Promise.reject({
        code: status,
        message,
        data
      })
    } else if (error.request) {
      // 请求已发出但没有收到响应
      return Promise.reject({
        code: 0,
        message: '网络连接失败，请检查网络'
      })
    } else {
      // 请求配置出错
      return Promise.reject({
        code: -1,
        message: error.message
      })
    }
  }
)

export default api