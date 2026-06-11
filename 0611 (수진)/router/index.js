import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '../views/HomeView.vue'
import UploadView from '../views/UploadView.vue'
import LoadingView from '../views/LoadingView.vue'
import PersonalColorResultView from '../views/PersonalColorResultView.vue'
import MakeoverView from '../views/MakeoverView.vue'
import ProductRecommendView from '../views/ProductRecommendView.vue'
import ProductDetailView from '../views/ProductDetailView.vue'


const router = createRouter({
  history: createWebHistory(),
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
  
  ],
})

export default router