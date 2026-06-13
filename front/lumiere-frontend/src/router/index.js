import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '../views/HomeView.vue'
import ProductDetailView from '@/views/products/ProductDetailView.vue'

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
      path: '/result',
      name: 'result',
      component: PersonalColorResultView,
    },
    {
      path: '/makeover',
      name: 'makeover',
      component: MakeoverView,
    },
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
    {
      path: '/ProductDetail',
      name: 'ProductDetail',
      component: ProductDetailView
      
    },
    {
      path: '/Diagnosis',
      name: 'Diagnosis',
      component: DiagnosisView
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/analysis/result',
      name: 'AnalysisResult',
      component: () => import('@/views/analysis/ResultView.vue')
    },
    {
      path: '/mypage',
      name: 'MyPage',
      component: MyPageView
    },
  ],
})

export default router
