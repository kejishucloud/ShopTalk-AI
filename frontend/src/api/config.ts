import request from './request'

// 配置分类相关接口
export interface ConfigCategory {
  id: number
  name: string
  display_name: string
  description: string
  order: number
  is_active: boolean
}

// 配置组相关接口
export interface ConfigGroup {
  id: number
  name: string
  display_name: string
  description: string
  order: number
  is_collapsible: boolean
  is_expanded: boolean
  configs?: SystemConfig[]
}

// 系统配置相关接口
export interface SystemConfig {
  id: number
  key: string
  display_name: string
  description: string
  config_type: 'string' | 'integer' | 'float' | 'boolean' | 'json' | 'password' | 'email' | 'url' | 'text' | 'choice'
  value?: string
  parsed_value: any
  default_value?: string
  choices: Array<{value: string, label: string}>
  is_required: boolean
  is_encrypted: boolean
  order: number
  is_active: boolean
  category: number
  category_name: string
  group?: number
  group_name?: string
  created_at: string
  updated_at: string
}

// 配置分类详情
export interface ConfigCategoryDetail extends ConfigCategory {
  groups: ConfigGroup[]
  ungrouped_configs: SystemConfig[]
}

// 批量更新配置
export interface ConfigUpdateRequest {
  configs: Array<{
    key: string
    value: string
  }>
}

// API函数

// 获取所有配置分类
export function getConfigCategories() {
  return request.get<ConfigCategory[]>('/api/v1/system-config/categories/')
}

// 获取配置分类详情（包含配置项）
export function getConfigCategoryDetail(id: number) {
  return request.get<ConfigCategoryDetail>(`/api/v1/system-config/categories/${id}/detail_with_configs/`)
}

// 获取系统配置列表
export function getSystemConfigs(params?: {
  category?: number
  config_type?: string
  is_required?: boolean
  search?: string
}) {
  return request.get<{
    results: SystemConfig[]
    count: number
  }>('/api/v1/system-config/configs/', { params })
}

// 根据分类获取配置项
export function getConfigsByCategory(categoryId: number) {
  return request.get<SystemConfig[]>('/api/v1/system-config/configs/by_category/', {
    params: { category_id: categoryId }
  })
}

// 根据key获取配置值
export function getConfigByKey(key: string) {
  return request.get<{
    key: string
    value: any
    display_name: string
    description: string
  }>('/api/v1/system-config/configs/get_by_key/', {
    params: { key }
  })
}

// 根据key设置配置值
export function setConfigByKey(key: string, value: any) {
  return request.post<{
    success: boolean
    message: string
    key: string
    value: any
  }>('/api/v1/system-config/configs/set_by_key/', {
    key,
    value
  })
}

// 批量更新配置
export function batchUpdateConfigs(data: ConfigUpdateRequest) {
  return request.post<{
    success: boolean
    message: string
    updated: Array<{
      key: string
      old_value: string
      new_value: string
    }>
    errors?: string[]
  }>('/api/v1/system-config/configs/batch_update/', data)
}

// 创建系统配置
export function createSystemConfig(data: Partial<SystemConfig>) {
  return request.post<SystemConfig>('/api/v1/system-config/configs/', data)
}

// 更新系统配置
export function updateSystemConfig(id: number, data: Partial<SystemConfig>) {
  return request.put<SystemConfig>(`/api/v1/system-config/configs/${id}/`, data)
}

// 删除系统配置
export function deleteSystemConfig(id: number) {
  return request.delete(`/api/v1/system-config/configs/${id}/`)
}

// 获取配置组列表
export function getConfigGroups(categoryId?: number) {
  return request.get<ConfigGroup[]>('/api/v1/system-config/groups/', {
    params: categoryId ? { category: categoryId } : undefined
  })
} 