<template>
  <div class="profile-page">
    <div class="page-header">
      <h1>个人中心</h1>
      <p>管理您的个人信息和权限设置</p>
    </div>
    
    <div class="content-placeholder">
      <el-result icon="warning" title="页面开发中" sub-title="个人中心功能正在开发中，敬请期待">
        <template #extra>
          <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup lang="ts">
// 个人中心页面
</script>

<style lang="scss" scoped>
.profile-page {
  .page-header {
    margin-bottom: 32px;
    
    h1 {
      font-size: 28px;
      color: $text-primary;
      margin-bottom: 8px;
    }
    
    p {
      color: $text-secondary;
      margin: 0;
    }
  }
  
  .content-placeholder {
    background: $bg-card;
    border-radius: $border-radius-large;
    padding: 48px;
  }
}
</style> 