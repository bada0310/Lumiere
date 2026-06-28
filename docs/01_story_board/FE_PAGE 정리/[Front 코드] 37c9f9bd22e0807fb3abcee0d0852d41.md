# [Front 코드]

```jsx
<template>
  <div class="page">
    <AppHeader />

    <main class="upload-page">
      <div class="back">‹ 이전으로</div>

      <section class="title-section">
        <h1>AI 퍼스널컬러 진단</h1>
        <p>정확한 진단을 위해 가이드를 따라 사진을 업로드해 주세요.</p>
      </section>

      <section class="steps">
        <div class="step active">1</div>
        <div class="line active"></div>
        <div class="step">2</div>
        <div class="line"></div>
        <div class="step">3</div>
      </section>

      <section class="step-labels">
        <span class="active-text">사진 업로드</span>
        <span>AI 분석</span>
        <span>결과 확인</span>
      </section>

      <section class="upload-card">
        <div class="top-grid">
          <div class="guide-box">
            <h2>촬영 가이드</h2>

            <div class="guide-list">
              <div class="guide-item">
                <span>☀️</span>
                <p><strong>밝은 자연광 또는 밝은 조명</strong><br />그늘이나 어두운 곳은 피해 주세요.</p>
              </div>

              <div class="guide-item">
                <span>🙂</span>
                <p><strong>정면을 바라보고 촬영</strong><br />고개를 기울이거나 돌리지 마세요.</p>
              </div>

              <div class="guide-item">
                <span>✨</span>
                <p><strong>노필터로 촬영</strong><br />보정이나 필터는 사용하지 마세요.</p>
              </div>

              <div class="guide-item">
                <span>👓</span>
                <p><strong>안경을 벗고 촬영</strong><br />렌즈는 착용해도 괜찮아요.</p>
              </div>

              <div class="guide-item">
                <span>👒</span>
                <p><strong>모자나 머리띠를 벗고 촬영</strong><br />이마와 헤어라인이 보여야 해요.</p>
              </div>
            </div>
          </div>

          <div class="upload-box">
            <h2>사진 업로드</h2>

            <div class="upload-area">
              <div class="camera-icon">📷</div>
              <p>
                사진을 업로드하거나<br />
                카메라로 촬영해 주세요
              </p>

              <button class="primary-btn">📷 카메라로 촬영</button>
              <button class="outline-btn">⇧ 갤러리에서 선택</button>

              <small>JPG, PNG 파일만 업로드 가능 (최대 10MB)</small>
            </div>
          </div>

          <div class="preview-box">
            <h2>업로드한 이미지 미리보기</h2>

            <div class="preview-image">
              <div class="face-placeholder">🙂</div>
            </div>

            <button class="outline-btn full">다른 사진으로 변경 ↻</button>
          </div>
        </div>

        <div class="example-grid">
          <div class="example-box">
            <h3>⊙ 좋은 사진 예시</h3>

            <div class="example-list">
              <div class="good-img"></div>
              <div class="good-img"></div>
              <div class="good-img"></div>
              <div class="good-img"></div>
            </div>

            <p class="good-text">✓ 가이드에 맞는 사진은 더 정확한 진단 결과를 제공합니다.</p>
          </div>

          <div class="example-box">
            <h3>⊗ 잘못된 사진 예시</h3>

            <div class="example-list">
              <div class="bad-img"></div>
              <div class="bad-img"></div>
              <div class="bad-img"></div>
              <div class="bad-img"></div>
            </div>

            <div class="bad-labels">
              <span>조명이 어두워요</span>
              <span>측면 사진이에요</span>
              <span>안경을 착용했어요</span>
              <span>필터가 적용됐어요</span>
            </div>
          </div>
        </div>

        <RouterLink to="/loading" class="analysis-btn">
          분석 시작하기 →
        </RouterLink>

        <p class="privacy">🔒 업로드된 이미지는 AI 분석 후 즉시 삭제되며 저장되지 않습니다.</p>
      </section>
    </main>
  </div>
</template>

<script setup>
import AppHeader from '../components/AppHeader.vue'
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #fffaf7;
}

.upload-page {
  padding: 32px 48px 48px;
  background: linear-gradient(180deg, #fffaf7 0%, #fbf4f1 100%);
}

.back {
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
}

.title-section {
  text-align: center;
}

.title-section h1 {
  font-family: Georgia, serif;
  font-size: 30px;
  margin-bottom: 8px;
}

.title-section p {
  color: #555;
}

.steps {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 30px;
}

.step {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: white;
  border: 1px solid #ddd;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #777;
}

.step.active {
  background: #c65367;
  color: white;
  border-color: #c65367;
}

.line {
  width: 220px;
  height: 1px;
  background: #ddd;
}

.line.active {
  background: #e5a8b1;
  border-top: 1px dashed #e5a8b1;
}

.step-labels {
  width: 520px;
  margin: 10px auto 28px;
  display: flex;
  justify-content: space-between;
  color: #777;
  font-size: 14px;
}

.active-text {
  color: #c65367;
  font-weight: 700;
}

.upload-card {
  max-width: 1280px;
  margin: 0 auto;
  padding: 36px 42px 28px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid #eaded8;
  border-radius: 16px;
}

.top-grid {
  display: grid;
  grid-template-columns: 1fr 1.25fr 1fr;
  gap: 36px;
}

.guide-box,
.upload-box,
.preview-box,
.example-box {
  background: rgba(255, 255, 255, 0.86);
  border-radius: 14px;
}

.guide-box,
.upload-box,
.preview-box {
  padding: 24px;
}

h2 {
  font-size: 18px;
  margin-bottom: 18px;
}

.guide-list {
  border: 1px solid #eaded8;
  border-radius: 12px;
  padding: 24px 22px;
}

.guide-item {
  display: flex;
  gap: 14px;
  margin-bottom: 26px;
}

.guide-item:last-child {
  margin-bottom: 0;
}

.guide-item span {
  font-size: 24px;
}

.guide-item p {
  margin: 0;
  line-height: 1.6;
  font-size: 14px;
}

.upload-area {
  height: 348px;
  border: 2px dashed #e9b9c2;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.camera-icon {
  font-size: 52px;
  margin-bottom: 20px;
}

.upload-area p {
  text-align: center;
  line-height: 1.5;
  color: #555;
}

.primary-btn,
.outline-btn {
  width: 230px;
  height: 44px;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
  margin-top: 12px;
}

.primary-btn {
  background: #c65367;
  color: white;
  border: none;
}

.outline-btn {
  background: white;
  color: #c65367;
  border: 1px solid #d98c99;
}

.upload-area small {
  margin-top: 20px;
  color: #777;
}

.preview-image {
  height: 286px;
  border-radius: 12px;
  background: linear-gradient(135deg, #f6e7df, #fff4ef);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
}

.face-placeholder {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: #f0c8bd;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 70px;
}

.full {
  width: 100%;
}

.example-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  margin-top: 24px;
}

.example-box {
  border: 1px solid #eaded8;
  padding: 22px 24px;
}

.example-box h3 {
  color: #c65367;
  font-size: 16px;
  margin-bottom: 18px;
}

.example-list {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.good-img,
.bad-img {
  height: 100px;
  border-radius: 10px;
}

.good-img {
  background: linear-gradient(135deg, #f7d8d8, #fff1ea);
}

.bad-img {
  background: linear-gradient(135deg, #d8c2ba, #ffe3dc);
}

.good-text {
  margin-top: 16px;
  color: #4d8b61;
  font-size: 14px;
}

.bad-labels {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-top: 10px;
  font-size: 12px;
  color: #555;
  text-align: center;
}

.analysis-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 420px;
  height: 52px;
  margin: 28px auto 16px;
  border-radius: 8px;
  background: #c65367;
  color: white;
  text-decoration: none;
  font-weight: 700;
}

.privacy {
  text-align: center;
  color: #777;
  font-size: 14px;
}
</style>
```