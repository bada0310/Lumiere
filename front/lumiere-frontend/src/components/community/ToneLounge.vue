<template>
  <div class="tone-lounge-sidebar">
    <div class="lounge-card" :style="{ '--lounge-color': lounge.color }">
      <span class="sub-title">내 톤 라운지</span>
      <h2 class="lounge-name">{{ lounge.koreanName }} <span class="badge">라운지</span></h2>
      <p class="lounge-desc">{{ lounge.description }}</p>
      <button class="action-btn" @click="$emit('change-lounge')">라운지 설정 변경</button>
    </div>

    <div class="activity-card">
      <div class="member-count">
        <strong>{{ lounge.members.toLocaleString() }}</strong>명 활동 중
      </div>
      <div class="avatar-group">
        <img v-for="n in 5" :key="n" :src="`https://i.pravatar.cc/100?img=${n + 10}`" alt="avatar" />
        <span class="more-avatar">+99</span>
      </div>
    </div>

    <ul class="menu-list" aria-label="내 커뮤니티 메뉴">
      <li class="active">📋 전체 게시글</li>
      <li>✍️ 내가 쓴 글</li>
      <li>⭐ 스크랩한 글</li>
      <li>❤️ 내가 좋아요한 글</li>
      <li>⏱️ 최근 본 글</li>
    </ul>

    <div class="guide-card">
      <h3>커뮤니티 가이드</h3>
      <ul>
        <li>서로 존중하며 따뜻한 대화를 나눠요.</li>
        <li>광고 및 홍보 게시물은 제한될 수 있어요.</li>
        <li>제품 정보는 객관적으로 공유해주세요.</li>
      </ul>
      <button type="button">자세히 보기</button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  lounge: {
    type: Object,
    required: true,
  },
})
</script>

<style scoped>
.tone-lounge-sidebar {
  width: 220px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  font-family: "Pretendard", "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", -apple-system, BlinkMacSystemFont, sans-serif;
  letter-spacing: 0;
}

.lounge-card,
.activity-card,
.menu-list,
.guide-card {
  width: 100%;
  border-radius: 14px;
}

.lounge-card {
  background-color: var(--lounge-color);
  background-image: linear-gradient(
    180deg,
    rgba(255,255,255,0.03),
    rgba(0,0,0,0.08)
  );
  color: #FFFFFF;
  padding: 22px;
}

.sub-title {
  font-size: 0.8rem;
  color: #FFFFFF;
  display: block;
  margin-bottom: 5px;
}

.lounge-name {
  font-size: 1.16rem;
  line-height: 1.35;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  color: #FFFFFF;
  font-weight: 700;
}

.badge {
  background: rgba(255,255,255,0.16);
  border: 1px solid rgba(255,255,255,0.28);
  color: #FFFFFF;
  font-size: 0.72rem;
  padding: 2px 6px;
  border-radius: 4px;
}

.lounge-desc {
  font-size: 0.84rem;
  line-height: 1.55;
  color: rgba(255,255,255,0.82);
  margin-bottom: 18px;
  font-weight: 400;
}

.action-btn {
  width: 100%;
  background: transparent;
  border: 1px solid rgba(255,255,255,0.42);
  color: #FFFFFF;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.84rem;
  font-family: inherit;
  font-weight: 500;
}

.action-btn:hover {
  background: rgba(255,255,255,0.10);
}

.activity-card {
  background: white;
  border: 1px solid #f0e5e0;
  padding: 18px;
  text-align: center;
}

.member-count {
  font-size: 0.92rem;
  margin-bottom: 12px;
}

.member-count strong {
  color: #8b3a4a;
  font-weight: 700;
}

.avatar-group {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 14px;
}

.avatar-group img {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid white;
  margin-left: -5px;
}

.avatar-group img:first-child {
  margin-left: 0;
}

.more-avatar {
  font-size: 0.75rem;
  color: #888;
  margin-left: 6px;
}

.guide-card button {
  background: none;
  border: 1px solid #eee0dc;
  width: 100%;
  padding: 8px;
  border-radius: 8px;
  color: #6d5f5b;
  font-size: 0.84rem;
  font-family: inherit;
  font-weight: 400;
  cursor: pointer;
}

.menu-list {
  list-style: none;
  padding: 8px;
  margin: 0;
  background: white;
  border: 1px solid #f0e5e0;
}

.menu-list li {
  padding: 11px 13px;
  font-size: 0.88rem;
  color: #555;
  cursor: pointer;
  border-radius: 8px;
}

.menu-list li.active {
  background-color: #fff5f6;
  color: #8b3a4a;
  font-weight: 600;
}

.guide-card {
  background: #fffafa;
  border: 1px solid #f0e5e0;
  padding: 18px;
}

.guide-card h3 {
  font-size: 0.98rem;
  margin-bottom: 12px;
  color: #3f3633;
  font-weight: 700;
}

.guide-card ul {
  display: flex;
  flex-direction: column;
  gap: 9px;
  margin-bottom: 15px;
}

.guide-card li {
  position: relative;
  padding-left: 12px;
  color: #6d5f5b;
  font-size: 0.8rem;
  line-height: 1.45;
  font-weight: 400;
}

.guide-card li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #8b3a4a;
}

@media (max-width: 1120px) {
  .tone-lounge-sidebar {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .tone-lounge-sidebar {
    display: flex;
  }
}
</style>
