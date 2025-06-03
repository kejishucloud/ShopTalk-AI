import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import Cookies from 'js-cookie'
import { login, getUserInfo } from '@/api/auth'
import type { User, LoginForm } from '@/types/user'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(Cookies.get('token') || '')
  const userInfo = ref<User | null>(null)
  const permissions = ref<string[]>([])

  const isLoggedIn = computed(() => !!token.value)

  // 登录
  const loginAction = async (loginForm: LoginForm) => {
    try {
      const response = await login(loginForm)
      token.value = response.data.access_token
      Cookies.set('token', token.value, { expires: 7 })
      await fetchUserInfo()
      return { success: true }
    } catch (error: any) {
      return { success: false, message: error.response?.data?.message || '登录失败' }
    }
  }

  // 获取用户信息
  const fetchUserInfo = async () => {
    try {
      const response = await getUserInfo()
      userInfo.value = response.data.user
      permissions.value = response.data.permissions || []
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }

  // 登出
  const logout = () => {
    token.value = ''
    userInfo.value = null
    permissions.value = []
    Cookies.remove('token')
  }

  // 检查权限
  const hasPermission = (permission: string) => {
    return permissions.value.includes(permission)
  }

  return {
    token,
    userInfo,
    permissions,
    isLoggedIn,
    loginAction,
    fetchUserInfo,
    logout,
    hasPermission
  }
}) 