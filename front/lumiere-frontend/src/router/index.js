import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '@/views/Home/HomeView.vue'

import LoginView from '@/views/accounts/LoginView.vue'
import MyPageListView from '@/views/accounts/MyPageListView.vue'
import MyPageView from '@/views/accounts/MyPageView.vue'

import UploadView from '@/views/diagnosis/UploadView.vue'
import LoadingView from '@/views/diagnosis/LoadingView.vue'
import PersonalColorResultView from '@/views/diagnosis/PersonalColorResultView.vue'

import ProductRecommendView from '@/views/products/ProductRecommendView.vue'
import ProductColorMatchingPage from '@/views/products/ProductColorMatchingPage.vue'

import AnalysisView from '@/views/Analysis/AnalysisView.vue'
import CommunityView from '@/views/community/CommunityView.vue'
import CommunityCreateView from '@/views/community/CommunityCreateView.vue'
import CommunityDetailView from '@/views/community/CommunityDetailView.vue'
import { isAuthenticated } from '@/utils/auth'

const authMessage = '로그인 후 이용할 수 있어요.'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),

  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
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
        authMessage,
      },
    },
    {
      path: '/mypage/diagnoses',
      name: 'mypage-diagnoses',
      component: MyPageListView,
      meta: {
        requiresAuth: true,
        listType: 'diagnoses',
        authMessage,
      },
    },
    {
      path: '/mypage/liked-options',
      name: 'mypage-liked-options',
      component: MyPageListView,
      meta: {
        requiresAuth: true,
        listType: 'liked-options',
        authMessage,
      },
    },
    {
      path: '/mypage/url-analyses',
      name: 'mypage-url-analyses',
      component: MyPageListView,
      meta: {
        requiresAuth: true,
        listType: 'url-analyses',
        authMessage,
      },
    },
    {
      path: '/mypage/posts',
      name: 'mypage-posts',
      component: MyPageListView,
      meta: {
        requiresAuth: true,
        listType: 'posts',
        authMessage,
      },
    },
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
    {
      path: '/products',
      name: 'products',
      component: ProductRecommendView,
    },
    {
      path: '/product-detail/:id?',
      name: 'product-detail',
      component: ProductColorMatchingPage,
    },
    {
      path: '/products/:id/color-matching',
      name: 'product-color-matching',
      component: ProductColorMatchingPage,
    },
    {
      path: '/product-analysis',
      name: 'product-analysis',
      component: AnalysisView,
    },
    {
      path: '/analysis/result/:id',
      name: 'analysis-result',
      component: AnalysisView,
    },
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
