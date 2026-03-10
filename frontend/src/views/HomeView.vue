<template>
  <div class="home">
    <h1>AI分支对话系统</h1>
    <p>欢迎使用AI分支对话系统前端界面</p>
    <RouterLink to="/api-test">前往API测试页面</RouterLink>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<style scoped>
.home {
  padding: 20px;
  text-align: center;
}
</style>