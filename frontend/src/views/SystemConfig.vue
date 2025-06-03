<template>
  <div class="system-config">
    <div class="header">
      <h1>系统配置管理</h1>
      <p class="subtitle">管理AI模型、电商平台、智能体等系统配置</p>
    </div>

    <!-- 配置分类标签 -->
    <el-tabs v-model="activeCategory" @tab-change="handleCategoryChange" type="border-card">
      <el-tab-pane
        v-for="category in categories"
        :key="category.id"
        :label="category.display_name"
        :name="String(category.id)"
      >
        <div class="category-content">
          <div class="category-description" v-if="category.description">
            <el-alert :title="category.description" type="info" :closable="false" />
          </div>

          <!-- 加载状态 -->
          <div v-if="loading" class="loading-container">
            <el-skeleton :rows="5" animated />
          </div>

          <!-- 配置内容 -->
          <div v-else-if="currentCategoryDetail">
            <!-- 配置组 -->
            <div v-for="group in currentCategoryDetail.groups" :key="group.id" class="config-group">
              <el-collapse v-model="expandedGroups" accordion>
                <el-collapse-item :name="String(group.id)">
                  <template #title>
                    <div class="group-title">
                      <el-icon><Setting /></el-icon>
                      <span>{{ group.display_name }}</span>
                      <el-tag v-if="group.configs" size="small" type="info">
                        {{ group.configs.length }} 项配置
                      </el-tag>
                    </div>
                  </template>
                  
                  <div class="group-description" v-if="group.description">
                    <p>{{ group.description }}</p>
                  </div>
                  
                  <el-form :model="configForm" label-width="160px" class="config-form">
                    <el-form-item
                      v-for="config in group.configs"
                      :key="config.id"
                      :label="config.display_name"
                      :required="config.is_required"
                    >
                      <template #label>
                        <div class="config-label">
                          <span>{{ config.display_name }}</span>
                          <el-tooltip v-if="config.description" :content="config.description" placement="top">
                            <el-icon class="help-icon"><QuestionFilled /></el-icon>
                          </el-tooltip>
                          <el-tag v-if="config.is_required" size="small" type="danger">必填</el-tag>
                        </div>
                      </template>
                      
                      <config-input
                        v-model="configForm[config.key]"
                        :config="config"
                        @change="handleConfigChange(config.key, $event)"
                      />
                    </el-form-item>
                  </el-form>
                </el-collapse-item>
              </el-collapse>
            </div>

            <!-- 未分组的配置 -->
            <div v-if="currentCategoryDetail.ungrouped_configs?.length" class="ungrouped-configs">
              <h3>其他配置</h3>
              <el-form :model="configForm" label-width="160px" class="config-form">
                <el-form-item
                  v-for="config in currentCategoryDetail.ungrouped_configs"
                  :key="config.id"
                  :label="config.display_name"
                  :required="config.is_required"
                >
                  <template #label>
                    <div class="config-label">
                      <span>{{ config.display_name }}</span>
                      <el-tooltip v-if="config.description" :content="config.description" placement="top">
                        <el-icon class="help-icon"><QuestionFilled /></el-icon>
                      </el-tooltip>
                      <el-tag v-if="config.is_required" size="small" type="danger">必填</el-tag>
                    </div>
                  </template>
                  
                  <config-input
                    v-model="configForm[config.key]"
                    :config="config"
                    @change="handleConfigChange(config.key, $event)"
                  />
                </el-form-item>
              </el-form>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 保存按钮 -->
    <div class="footer-actions">
      <el-button @click="resetForm">重置</el-button>
      <el-button type="primary" @click="saveConfigs" :loading="saving">
        保存配置
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Setting, QuestionFilled } from '@element-plus/icons-vue'
import ConfigInput from '../components/ConfigInput.vue'
import {
  getConfigCategories,
  getConfigCategoryDetail,
  batchUpdateConfigs,
  type ConfigCategory,
  type ConfigCategoryDetail
} from '../api/config'

// 响应式数据
const activeCategory = ref<string>('')
const categories = ref<ConfigCategory[]>([])
const currentCategoryDetail = ref<ConfigCategoryDetail | null>(null)
const configForm = reactive<Record<string, any>>({})
const changedConfigs = reactive<Record<string, any>>({})
const expandedGroups = ref<string[]>([])
const loading = ref(false)
const saving = ref(false)

// 计算属性
const hasChanges = computed(() => Object.keys(changedConfigs).length > 0)

// 生命周期钩子
onMounted(async () => {
  await loadCategories()
})

// 方法

// 加载配置分类
async function loadCategories() {
  try {
    const response = await getConfigCategories()
    categories.value = response.data
    if (categories.value.length > 0) {
      activeCategory.value = String(categories.value[0].id)
      await loadCategoryDetail(categories.value[0].id)
    }
  } catch (error) {
    console.error('加载配置分类失败:', error)
    ElMessage.error('加载配置分类失败')
  }
}

// 加载分类详情
async function loadCategoryDetail(categoryId: number) {
  loading.value = true
  try {
    const response = await getConfigCategoryDetail(categoryId)
    currentCategoryDetail.value = response.data
    
    // 初始化表单数据
    initFormData()
    
    // 默认展开第一个组
    if (currentCategoryDetail.value.groups.length > 0) {
      expandedGroups.value = [String(currentCategoryDetail.value.groups[0].id)]
    }
  } catch (error) {
    console.error('加载配置详情失败:', error)
    ElMessage.error('加载配置详情失败')
  } finally {
    loading.value = false
  }
}

// 初始化表单数据
function initFormData() {
  if (!currentCategoryDetail.value) return
  
  // 清空表单和变更记录
  Object.keys(configForm).forEach(key => delete configForm[key])
  Object.keys(changedConfigs).forEach(key => delete changedConfigs[key])
  
  // 从分组中的配置项初始化
  currentCategoryDetail.value.groups.forEach(group => {
    group.configs?.forEach(config => {
      configForm[config.key] = config.parsed_value
    })
  })
  
  // 从未分组的配置项初始化
  currentCategoryDetail.value.ungrouped_configs.forEach(config => {
    configForm[config.key] = config.parsed_value
  })
}

// 处理分类切换
async function handleCategoryChange(categoryId: string) {
  if (hasChanges.value) {
    try {
      await ElMessageBox.confirm(
        '您有未保存的更改，切换分类将丢失这些更改。是否继续？',
        '确认操作',
        {
          confirmButtonText: '继续',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    } catch {
      // 用户取消，恢复之前的选择
      activeCategory.value = activeCategory.value
      return
    }
  }
  
  await loadCategoryDetail(parseInt(categoryId))
}

// 处理配置项变更
function handleConfigChange(key: string, value: any) {
  changedConfigs[key] = value
}

// 重置表单
function resetForm() {
  initFormData()
  ElMessage.success('已重置为原始值')
}

// 保存配置
async function saveConfigs() {
  if (!hasChanges.value) {
    ElMessage.info('没有需要保存的更改')
    return
  }
  
  try {
    saving.value = true
    
    const configsToUpdate = Object.entries(changedConfigs).map(([key, value]) => ({
      key,
      value: String(value)
    }))
    
    const response = await batchUpdateConfigs({ configs: configsToUpdate })
    
    if (response.data.success) {
      ElMessage.success(response.data.message || '配置保存成功')
      
      // 清空变更记录
      Object.keys(changedConfigs).forEach(key => delete changedConfigs[key])
      
      // 重新加载当前分类数据
      await loadCategoryDetail(parseInt(activeCategory.value))
    } else {
      ElMessage.error('保存配置失败：' + (response.data.errors?.join(', ') || '未知错误'))
    }
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error('保存配置失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped lang="scss">
.system-config {
  padding: 20px;
  background: #fff;
  min-height: calc(100vh - 60px);

  .header {
    margin-bottom: 20px;
    
    h1 {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
    }
    
    .subtitle {
      color: #909399;
      margin: 0;
      font-size: 14px;
    }
  }

  .category-content {
    .category-description {
      margin-bottom: 20px;
    }

    .loading-container {
      padding: 20px;
    }

    .config-group {
      margin-bottom: 20px;
      
      .group-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 500;
        
        .el-icon {
          color: #409eff;
        }
      }
      
      .group-description {
        margin-bottom: 16px;
        padding: 12px;
        background: #f5f7fa;
        border-radius: 4px;
        color: #606266;
        font-size: 14px;
      }
    }

    .ungrouped-configs {
      margin-top: 30px;
      
      h3 {
        font-size: 16px;
        font-weight: 500;
        color: #303133;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid #ebeef5;
      }
    }

    .config-form {
      .config-label {
        display: flex;
        align-items: center;
        gap: 6px;
        
        .help-icon {
          color: #909399;
          cursor: help;
          font-size: 14px;
          
          &:hover {
            color: #409eff;
          }
        }
      }
    }
  }

  .footer-actions {
    position: sticky;
    bottom: 0;
    background: #fff;
    padding: 20px 0;
    border-top: 1px solid #ebeef5;
    text-align: right;
    margin-top: 30px;
  }
}

:deep(.el-tabs__content) {
  padding: 20px 0;
}

:deep(.el-collapse-item__header) {
  font-weight: 500;
}

:deep(.el-form-item) {
  margin-bottom: 22px;
}
</style> 