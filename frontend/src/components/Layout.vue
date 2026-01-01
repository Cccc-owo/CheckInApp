<template>
  <div class="layout-container">
    <Navbar />
    <div class="main-content">
      <slot />
    </div>
  </div>
</template>

<script setup>
import Navbar from './Navbar.vue'
</script>

<style scoped>
.layout-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  background-color: #f5f5f5;
  padding: 20px;
}
</style>
