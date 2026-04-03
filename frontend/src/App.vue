<script setup lang="ts">
import {RouterView } from 'vue-router'
</script>

<template>
  <RouterView />
</template>

<style>
/* 全局样式，确保应用占满整个视口 */
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

/* 主容器布局 */
.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
}
</style>