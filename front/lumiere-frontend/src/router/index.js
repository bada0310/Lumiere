import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '../views/home/HomeView.vue'
import UploadView from '@/views/diagnosis/UploadView.vue'
import LoadingView from '@/views/diagnosis/LoadingView.vue'
import PersonalColorResultView from '@/views/diagnosis/PersonalColorResultView.vue'

import ProductDetailView from '@/views/products/ProductDetailView.vue'
import ProductRecommendView from '@/views/diagnosis/ProductRecommendView.vue'
import AnalysisView from '@/views/analysis/AnalysisView.vue'
import CommunityView from '@/views/community/CommunityView.vue'

import LoginView from '@/views/accounts/LoginView.vue'
import MyPageView from '@/views/accounts/MyPageView.vue'
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    // 1. AI 진단 프로세스 라인
    {
      path: '/upload',
      name: 'upload',
      component: UploadView,
    },
    {
      path: '/loading',
      name: 'loading',
      component: LoadingView,
    },
    {
      path: '/diagnosis',
      name: 'diagnosis',
      component: PersonalColorResultView,
    },
    {
      path: '/diagnosis/result/:id', // 💡 추가: 마이페이지에서 '진단 기록 다시보기' 클릭 시 이동할 경로
      name: 'past-diagnosis-result',
      component: PersonalColorResultView,
    },

    // 2. 추천 제품 라인
    {
      path: '/products',
      name: 'products',
      component: ProductRecommendView,
    },
    {
      path: '/product-detail',
      name: 'product-detail',
      component: ProductDetailView,
    },

    // 3. 제품 검색 / URL 분석 라인
    {
      path: '/product-analysis',
      name: 'product-analysis',
      component: AnalysisView,
    },
    {
      path: '/analysis/result/:id', // 💡 추가: 마이페이지에서 '최근 URL 분석 기록' 클릭 시 이동할 경로
      name: 'past-analysis-result',
      component: AnalysisView,
    },
    // 4. 공통 제품 상세 분석 (추천리스트, URL결과, 커뮤니티에서 모두 일련번호를 들고 진입 가능하도록 :id 추가)
    {
      path: '/product-detail/:id?', // 💡 뒤에 ?를 붙이면 id가 없어도(공통 페이지) 접근 가능합니다.
      name: 'product-detail',
      component: ProductDetailView,
    },
    // 5. 톤 커뮤니티 라인
    {
      path: '/community',
      name: 'community',
      component: CommunityView,
    },
    // 6. 마이페이지 라인
    {
      path: '/mypage',
      name: 'MyPage',
      component: MyPageView
    },
    {
      path: '/result/:id?',  // 👈 새로 진단했을 때는 /result, 다시보기 할 때는 /result/101 형태로 둘 다 수용 가능
      name: 'result',
      component: PersonalColorResultView,
    },
    
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    
  ],
})

export default router
