<template>
  <div class="config-input">
    <!-- 字符串输入 -->
    <el-input
      v-if="config.config_type === 'string'"
      v-model="inputValue"
      :placeholder="getPlaceholder()"
      clearable
      @input="handleInput"
    />
    
    <!-- 密码输入 -->
    <el-input
      v-else-if="config.config_type === 'password'"
      v-model="inputValue"
      type="password"
      :placeholder="getPlaceholder()"
      show-password
      clearable
      @input="handleInput"
    />
    
    <!-- 邮箱输入 -->
    <el-input
      v-else-if="config.config_type === 'email'"
      v-model="inputValue"
      type="email"
      :placeholder="getPlaceholder()"
      clearable
      @input="handleInput"
    />
    
    <!-- URL输入 -->
    <el-input
      v-else-if="config.config_type === 'url'"
      v-model="inputValue"
      type="url"
      :placeholder="getPlaceholder()"
      clearable
      @input="handleInput"
    >
      <template #prepend>
        <el-icon><Link /></el-icon>
      </template>
    </el-input>
    
    <!-- 长文本输入 -->
    <el-input
      v-else-if="config.config_type === 'text'"
      v-model="inputValue"
      type="textarea"
      :rows="4"
      :placeholder="getPlaceholder()"
      @input="handleInput"
    />
    
    <!-- 整数输入 -->
    <el-input-number
      v-else-if="config.config_type === 'integer'"
      v-model="inputValue"
      :placeholder="getPlaceholder()"
      :precision="0"
      controls-position="right"
      style="width: 100%"
      @change="handleInput"
    />
    
    <!-- 浮点数输入 -->
    <el-input-number
      v-else-if="config.config_type === 'float'"
      v-model="inputValue"
      :placeholder="getPlaceholder()"
      :precision="2"
      :step="0.1"
      controls-position="right"
      style="width: 100%"
      @change="handleInput"
    />
    
    <!-- 布尔值输入 -->
    <el-switch
      v-else-if="config.config_type === 'boolean'"
      v-model="inputValue"
      active-text="启用"
      inactive-text="禁用"
      @change="handleInput"
    />
    
    <!-- 选择输入 -->
    <el-select
      v-else-if="config.config_type === 'choice'"
      v-model="inputValue"
      :placeholder="getPlaceholder()"
      clearable
      style="width: 100%"
      @change="handleInput"
    >
      <el-option
        v-for="choice in config.choices"
        :key="choice.value"
        :label="choice.label"
        :value="choice.value"
      />
    </el-select>
    
    <!-- JSON输入 -->
    <div v-else-if="config.config_type === 'json'" class="json-input">
      <el-input
        v-model="jsonString"
        type="textarea"
        :rows="6"
        :placeholder="getPlaceholder()"
        @input="handleJsonInput"
      />
      <div v-if="jsonError" class="json-error">
        <el-text type="danger" size="small">{{ jsonError }}</el-text>
      </div>
      <div class="json-actions">
        <el-button size="small" @click="formatJson">格式化</el-button>
        <el-button size="small" @click="validateJson">验证</el-button>
      </div>
    </div>
    
    <!-- 默认字符串输入 -->
    <el-input
      v-else
      v-model="inputValue"
      :placeholder="getPlaceholder()"
      clearable
      @input="handleInput"
    />
    
    <!-- 默认值提示 -->
    <div v-if="config.default_value && !inputValue" class="default-hint">
      <el-text type="info" size="small">
        默认值: {{ config.default_value }}
      </el-text>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Link } from '@element-plus/icons-vue'
import type { SystemConfig } from '../api/config'

// Props
interface Props {
  modelValue: any
  config: SystemConfig
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  change: [value: any]
  'update:modelValue': [value: any]
}>()

// 响应式数据
const inputValue = ref<any>(props.modelValue)
const jsonString = ref<string>('')
const jsonError = ref<string>('')

// 计算属性
const isJsonType = computed(() => props.config.config_type === 'json')

// 监听器
watch(() => props.modelValue, (newValue) => {
  inputValue.value = newValue
  if (isJsonType.value) {
    updateJsonString()
  }
}, { immediate: true })

watch(inputValue, (newValue) => {
  emit('update:modelValue', newValue)
  emit('change', newValue)
})

// 生命周期钩子
onMounted(() => {
  if (isJsonType.value) {
    updateJsonString()
  }
})

// 方法

// 获取占位符文本
function getPlaceholder(): string {
  if (props.config.default_value) {
    return `默认: ${props.config.default_value}`
  }
  
  switch (props.config.config_type) {
    case 'string':
      return '请输入字符串'
    case 'password':
      return '请输入密码'
    case 'email':
      return '请输入邮箱地址'
    case 'url':
      return '请输入URL地址'
    case 'text':
      return '请输入文本内容'
    case 'integer':
      return '请输入整数'
    case 'float':
      return '请输入数字'
    case 'choice':
      return '请选择'
    case 'json':
      return '请输入JSON格式数据'
    default:
      return '请输入'
  }
}

// 处理输入变化
function handleInput(value: any) {
  inputValue.value = value
}

// 更新JSON字符串显示
function updateJsonString() {
  try {
    if (inputValue.value && typeof inputValue.value === 'object') {
      jsonString.value = JSON.stringify(inputValue.value, null, 2)
    } else if (typeof inputValue.value === 'string') {
      // 尝试解析字符串为JSON
      const parsed = JSON.parse(inputValue.value)
      jsonString.value = JSON.stringify(parsed, null, 2)
    } else {
      jsonString.value = inputValue.value || ''
    }
    jsonError.value = ''
  } catch (error) {
    jsonString.value = String(inputValue.value || '')
    jsonError.value = ''
  }
}

// 处理JSON输入
function handleJsonInput(value: string) {
  jsonString.value = value
  jsonError.value = ''
  
  try {
    if (value.trim()) {
      const parsed = JSON.parse(value)
      inputValue.value = parsed
    } else {
      inputValue.value = null
    }
  } catch (error) {
    jsonError.value = '无效的JSON格式'
    // 不更新inputValue，保持原值
  }
}

// 格式化JSON
function formatJson() {
  try {
    if (jsonString.value.trim()) {
      const parsed = JSON.parse(jsonString.value)
      jsonString.value = JSON.stringify(parsed, null, 2)
      inputValue.value = parsed
      jsonError.value = ''
      ElMessage.success('JSON格式化成功')
    }
  } catch (error) {
    jsonError.value = '无效的JSON格式，无法格式化'
    ElMessage.error('JSON格式化失败')
  }
}

// 验证JSON
function validateJson() {
  try {
    if (jsonString.value.trim()) {
      JSON.parse(jsonString.value)
      jsonError.value = ''
      ElMessage.success('JSON格式正确')
    } else {
      ElMessage.info('JSON内容为空')
    }
  } catch (error) {
    jsonError.value = `JSON格式错误: ${(error as Error).message}`
    ElMessage.error('JSON格式验证失败')
  }
}
</script>

<style scoped lang="scss">
.config-input {
  width: 100%;
  
  .json-input {
    .json-error {
      margin-top: 4px;
    }
    
    .json-actions {
      margin-top: 8px;
      display: flex;
      gap: 8px;
    }
  }
  
  .default-hint {
    margin-top: 4px;
  }
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-switch) {
  --el-switch-on-color: #409eff;
  --el-switch-off-color: #dcdfe6;
}
</style> 