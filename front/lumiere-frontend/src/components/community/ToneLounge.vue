<template>
  <div class="tone-lounge-sidebar">
    <div class="lounge-card">
      <span class="sub-title">내 톤 라운지</span>
      <h2 class="lounge-name">{{ tone }} <span class="badge">라운지</span></h2>
      <p class="lounge-desc">맑고 부드러운 쿨톤 컬러가<br>잘 어울리는 톤이에요.</p>
      <button class="action-btn" @click="$emit('change-lounge')">라운지 설정 변경</button>
    </div>

    <div class="activity-card">
      <div class="member-count">
        <strong>3,842</strong>명 활동 중
      </div>
      <div class="avatar-group">
        <img v-for="n in 5" :key="n" :src="`https://i.pravatar.cc/100?img=${n+10}`" alt="avatar" />
        <span class="more-avatar">+99</span>
      </div>
      <button class="member-btn">라운지 멤버 보기</button>
    </div>

    <ul class="menu-list">
      <li class="active">📋 전체 게시글</li>
      <li>✍️ 내가 쓴 글</li>
      <li>⭐ 스크랩한 글</li>
      <li>❤️ 내가 좋아요한 글</li>
      <li>⏱️ 최근 본 글</li>
    </ul>
  </div>
</template>

<script setup>
defineProps({
  tone: {
    type: String,
    default: '여름 쿨 라이트'
  }
});
</script>

<style scoped>
.tone-lounge-sidebar {
  width: 240px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.lounge-card {
  background-color: #8b3a4a;
  color: white;
  padding: 24px;
  border-radius: 16px;
}
.sub-title { font-size: 0.8rem; opacity: 0.8; display: block; margin-bottom: 4px; }
.lounge-name { font-size: 1.3rem; margin: 0 0 12px 0; display: flex; align-items: center; gap: 8px; }
.badge { background: rgba(255,255,255,0.2); font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; }
.lounge-desc { font-size: 0.85rem; line-height: 1.5; opacity: 0.9; margin-bottom: 20px; }
.action-btn { 
  width: 100%; background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3);
  color: white; padding: 10px; border-radius: 8px; cursor: pointer; font-size: 0.85rem;
}

.activity-card {
  background: white; border: 1px solid #f0f0f0; padding: 20px; border-radius: 16px; text-align: center;
}
.member-count { font-size: 0.95rem; margin-bottom: 12px; }
.avatar-group { display: flex; justify-content: center; align-items: center; margin-bottom: 15px; }
.avatar-group img { width: 28px; height: 28px; border-radius: 50%; border: 2px solid white; margin-horizontal: -4px; }
.more-avatar { font-size: 0.75rem; color: #888; margin-left: 6px; }
.member-btn { background: none; border: 1px solid #eee; width: 100%; padding: 8px; border-radius: 8px; color: #666; font-size: 0.85rem; cursor: pointer; }

.menu-list { list-style: none; padding: 0; margin: 0; background: white; border-radius: 16px; border: 1px solid #f0f0f0; padding: 8px; }
.menu-list li { padding: 12px 16px; font-size: 0.9rem; color: #555; cursor: pointer; border-radius: 8px; }
.menu-list li.active { background-color: #fff5f6; color: #8b3a4a; font-weight: bold; }
</style>