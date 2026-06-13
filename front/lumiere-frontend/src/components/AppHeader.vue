<template>
  <header class="app-header">
    <div class="logo">Lumière</div>

    <nav class="nav">
      <a>진단하기</a>
      <a>제품 분석</a>
      <a>추천 제품</a>
      <a>커뮤니티</a>
      <a>마이페이지</a>
    </nav>

    <div class="user-area">
      <span>🔔</span>
      <span>♡</span>
      <div class="profile"></div>
      <span>안녕하세요, Subina님⌄</span>
    </div>
  </header>
</template>

<script setup>
</script>

<style scoped>
.app-header {
  height: 72px;
  padding: 0 42px;
  border-bottom: 1px solid #eaded8;
  background: rgba(255, 250, 247, 0.95);

  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  font-family: Georgia, serif;
  font-size: 30px;
  font-weight: 700;
  color: #bf4f63;
}

.nav {
  display: flex;
  gap: 56px;
  font-size: 15px;
  font-weight: 600;
}

.nav a {
  cursor: pointer;
}

.user-area {
  display: flex;
  align-items: center;
  gap: 18px;
  font-size: 14px;
}

.profile {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f5d6c8, #fff1ea);
}
</style>