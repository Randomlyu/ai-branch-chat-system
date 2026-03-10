<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <header>
    <div class="wrapper">
      <nav>
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/about">About</RouterLink>
        <RouterLink to="/api-test">API测试</RouterLink>
      </nav>
    </div>
  </header>

  <RouterView />
</template>

<style scoped>
/* 保持原有样式 */
</style>