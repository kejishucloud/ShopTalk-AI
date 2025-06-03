import request from './request'
import type { LoginForm } from '@/types/user'

// 登录接口
export const login = (data: LoginForm) => {
  return request.post('/auth/login/', data)
}

// 获取用户信息
export const getUserInfo = () => {
  return request.get('/auth/user/')
}

// 刷新token
export const refreshToken = (refresh: string) => {
  return request.post('/auth/token/refresh/', { refresh })
}

// 修改密码
export const changePassword = (data: {
  old_password: string
  new_password: string
  confirm_password: string
}) => {
  return request.post('/auth/change-password/', data)
}

// 更新个人信息
export const updateProfile = (data: any) => {
  return request.put('/auth/profile/', data)
} 