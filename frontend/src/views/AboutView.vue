<template>
  <div class="about">
    <h1>关于AI分支对话系统</h1>
    <p>这是一个支持分支对话的AI聊天系统前端项目</p>
    <RouterLink to="/">返回首页</RouterLink>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<style scoped>
.about {
  padding: 20px;
  text-align: center;
}
</style>