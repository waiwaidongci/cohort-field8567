import {createRouter,createWebHashHistory} from 'vue-router';
import Login from '../pages/Login.vue';import Overview from '../pages/Overview.vue';import Data from '../pages/Data.vue';import Experiments from '../pages/Experiments.vue';import Segments from '../pages/Segments.vue';import Campaigns from '../pages/Campaigns.vue';import Audit from '../pages/Audit.vue';
export const router=createRouter({history:createWebHashHistory(),routes:[{path:'/login',component:Login},{path:'/',component:Overview},{path:'/data',component:Data},{path:'/experiments',component:Experiments},{path:'/segments',component:Segments},{path:'/campaigns',component:Campaigns},{path:'/audit',component:Audit}]});
router.beforeEach(to=>{if(to.path!='/login'&&!localStorage.getItem('cohort-token'))return '/login';});
