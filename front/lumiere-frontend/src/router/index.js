import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '@/views/Home/HomeView.vue'

import LoginView from '@/views/accounts/LoginView.vue'
import MyPageView from '@/views/accounts/MyPageView.vue'

import UploadView from '@/views/diagnosis/UploadView.vue'
import LoadingView from '@/views/diagnosis/LoadingView.vue'
import PersonalColorResultView from '@/views/diagnosis/PersonalColorResultView.vue'

import ProductRecommendView from '@/views/products/ProductRecommendView.vue'
import ProductDetailView from '@/views/products/ProductDetailView.vue'

import AnalysisView from '@/views/Analysis/AnalysisView.vue'
import CommunityView from '@/views/community/CommunityView.vue'
import CommunityCreateView from '@/views/community/CommunityCreateView.vue'
import CommunityDetailView from '@/views/community/CommunityDetailView.vue'
import { isAuthenticated } from '@/utils/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),

  routes: [
    // 홈
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },

    // 계정
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/mypage',
      name: 'mypage',
      component: MyPageView,
      meta: {
        requiresAuth: true,
        authMessage: '마이페이지는 로그인 후 이용할 수 있어요.',
      },
    },

    // AI 퍼스널컬러 진단 흐름
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

    // 진단 결과 화면
    // /result       → 방금 진단한 결과
    // /result/101   → 마이페이지에서 과거 진단 다시보기
    {
      path: '/result/:id?',
      name: 'result',
      component: PersonalColorResultView,
    },
    {
      path: '/diagnosis/result',
      name: 'diagnosis-result-mock',
      component: PersonalColorResultView,
    },
    {
      path: '/diagnosis/results/demo',
      name: 'diagnosis-result-demo',
      component: PersonalColorResultView,
    },
    {
      path: '/diagnosis/results/:diagnosisId',
      name: 'diagnosis-result-detail',
      component: PersonalColorResultView,
    },

    // 추천 제품 목록
    {
      path: '/products',
      name: 'products',
      component: ProductRecommendView,
    },

    // 제품 옵션 상세
    // /product-detail/101 → ProductOption id 기준 상세
    {
      path: '/product-detail/:id?',
      name: 'product-detail',
      component: ProductDetailView,
    },

    // URL 제품 색상 분석
    {
      path: '/product-analysis',
      name: 'product-analysis',
      component: AnalysisView,
    },

    // 마이페이지에서 URL 분석 기록 다시보기
    {
      path: '/analysis/result/:id',
      name: 'analysis-result',
      component: AnalysisView,
    },

    // 커뮤니티
    {
      path: '/community',
      name: 'community',
      component: CommunityView,
    },
    {
      path: '/community/posts/new',
      name: 'community-create',
      component: CommunityCreateView,
      meta: {
        requiresAuth: true,
        authMessage: '게시글 작성은 로그인 후 이용할 수 있어요.',
      },
    },
    {
      path: '/community/posts/:id',
      name: 'community-detail',
      component: CommunityDetailView,
    },
    {
      path: '/community/lounge/:loungeKey',
      name: 'community-lounge',
      component: CommunityView,
    },
  ],
})

router.beforeEach((to) => {
  if (!to.meta.requiresAuth || isAuthenticated()) return true

  if (to.meta.authMessage) {
    alert(to.meta.authMessage)
  }

  return {
    name: 'login',
    query: {
      redirect: to.fullPath,
    },
  }
})

export default router
