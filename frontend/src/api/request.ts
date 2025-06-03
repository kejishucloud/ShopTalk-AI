import axios from 'axios'
import { ElMessage } from 'element-plus'
import Cookies from 'js-cookie'
import router from '@/router'

// 创建axios实例
const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = Cookies.get('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    const { response } = error
    
    if (response?.status === 401) {
      // 未授权，清除token并跳转到登录页
      Cookies.remove('token')
      router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    } else if (response?.status === 403) {
      ElMessage.error('权限不足')
    } else if (response?.status === 500) {
      ElMessage.error('服务器内部错误')
    } else {
      ElMessage.error(response?.data?.message || '请求失败')
    }
    
    return Promise.reject(error)
  }
)

export default request 