export interface User {
  id: number
  username: string
  email: string
  nickname?: string
  avatar?: string
  phone?: string
  role: string
  status: 'active' | 'inactive'
  tags: Tag[]
  created_at: string
  updated_at: string
}

export interface LoginForm {
  username: string
  password: string
  captcha?: string
  remember?: boolean
}

export interface Tag {
  id: number
  name: string
  color: string
  description?: string
}

export interface Permission {
  id: number
  name: string
  codename: string
  content_type: string
}

export interface Role {
  id: number
  name: string
  permissions: Permission[]
} 