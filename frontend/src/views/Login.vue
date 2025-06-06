<template>
  <div class="login-container">
    <!-- 背景动画 -->
    <div class="bg-animation">
      <div class="circle" v-for="i in 6" :key="i"></div>
    </div>
    
    <!-- 登录表单 -->
    <div class="login-box">
      <div class="login-header">
        <h1 class="logo-title glow">ShopTalk AI</h1>
        <p class="login-subtitle">智能客服管理平台</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            size="large"
            class="tech-input"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            size="large"
            class="tech-input"
            show-password
          />
        </el-form-item>
        
        <el-form-item prop="captcha">
          <div class="captcha-row">
            <el-input
              v-model="loginForm.captcha"
              placeholder="验证码"
              size="large"
              class="tech-input captcha-input"
            />
            <div class="captcha-image" @click="refreshCaptcha">
              <img :src="captchaUrl" alt="验证码" />
            </div>
          </div>
        </el-form-item>
        
        <el-form-item>
          <div class="login-options">
            <el-checkbox v-model="loginForm.remember">记住密码</el-checkbox>
            <el-link type="primary" :underline="false" @click="handleForgotPassword">忘记密码？</el-link>
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-btn gradient-btn"
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <!-- 版权信息 -->
      <div class="copyright">
        <p>&copy; 2024 ShopTalk AI. All rights reserved.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, FormInstance } from 'element-plus'
import { useUserStore } from '@/stores/user'
import type { LoginForm } from '@/types/user'

const router = useRouter()
const userStore = useUserStore()
const loginFormRef = ref<FormInstance>()

const loading = ref(false)
const captchaUrl = ref('/api/auth/captcha/')

const loginForm = reactive<LoginForm>({
  username: '',
  password: '',
  captcha: '',
  remember: false
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  captcha: [
    { required: true, message: '请输入验证码', trigger: 'blur' }
  ]
}

// 刷新验证码
const refreshCaptcha = () => {
  captchaUrl.value = `/api/auth/captcha/?t=${Date.now()}`
}

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  try {
    await loginFormRef.value.validate()
    loading.value = true
    
    const result = await userStore.loginAction(loginForm)
    
    if (result.success) {
      ElMessage.success('登录成功')
      router.push('/')
    } else {
      ElMessage.error(result.message)
      refreshCaptcha()
    }
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    loading.value = false
  }
}

// 处理忘记密码
const handleForgotPassword = () => {
  ElMessage.info('请联系管理员重置密码，或使用测试账号：用户名/密码都是 kejishu')
}

// 初始化
refreshCaptcha()
</script>

<style lang="scss" scoped>
.login-container {
  position: relative;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg-primary;
  overflow: hidden;
}

.bg-animation {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  
  .circle {
    position: absolute;
    border-radius: 50%;
    background: rgba(24, 144, 255, 0.1);
    animation: float 6s ease-in-out infinite;
    
    &:nth-child(1) {
      width: 80px;
      height: 80px;
      top: 10%;
      left: 10%;
      animation-delay: 0s;
    }
    
    &:nth-child(2) {
      width: 120px;
      height: 120px;
      top: 20%;
      right: 20%;
      animation-delay: 1s;
    }
    
    &:nth-child(3) {
      width: 60px;
      height: 60px;
      bottom: 30%;
      left: 20%;
      animation-delay: 2s;
    }
    
    &:nth-child(4) {
      width: 100px;
      height: 100px;
      bottom: 20%;
      right: 10%;
      animation-delay: 3s;
    }
    
    &:nth-child(5) {
      width: 140px;
      height: 140px;
      top: 50%;
      left: 5%;
      animation-delay: 4s;
    }
    
    &:nth-child(6) {
      width: 90px;
      height: 90px;
      top: 40%;
      right: 5%;
      animation-delay: 5s;
    }
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
    opacity: 0.3;
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
    opacity: 0.6;
  }
}

.login-box {
  position: relative;
  z-index: 2;
  width: 400px;
  padding: 40px;
  background: rgba(42, 49, 66, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(24, 144, 255, 0.3);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  animation: slideInUp 0.8s ease-out;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
  
  .logo-title {
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 8px;
    background: $gradient-tech;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .login-subtitle {
    color: $text-secondary;
    font-size: 14px;
  }
}

.login-form {
  .tech-input {
    :deep(.el-input__wrapper) {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      transition: all 0.3s ease;
      
      &:hover {
        border-color: $primary-color;
        box-shadow: 0 0 0 1px rgba(24, 144, 255, 0.2);
      }
      
      &.is-focus {
        border-color: $primary-color;
        box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
      }
    }
    
    :deep(.el-input__inner) {
      color: $text-primary;
      
      &::placeholder {
        color: $text-placeholder;
      }
    }
  }
}

.captcha-row {
  display: flex;
  gap: 12px;
  align-items: center;
  
  .captcha-input {
    flex: 1;
  }
  
  .captcha-image {
    width: 120px;
    height: 40px;
    cursor: pointer;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
    
    &:hover {
      border-color: $primary-color;
    }
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  
  :deep(.el-checkbox__label) {
    color: $text-secondary;
  }
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border: none;
  border-radius: 8px;
  background: $gradient-tech;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(79, 172, 254, 0.4);
  }
  
  &:active {
    transform: translateY(0);
  }
}

.copyright {
  text-align: center;
  margin-top: 24px;
  color: $text-tertiary;
  font-size: 12px;
}

// 响应式设计
@media (max-width: 768px) {
  .login-box {
    width: 90%;
    padding: 24px;
  }
}
</style> 