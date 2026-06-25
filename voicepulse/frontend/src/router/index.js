import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Upload from '../views/Upload.vue'
import Call from '../views/Call.vue'
import Graphs from '../views/Graphs.vue'
import Critique from '../views/Critique.vue'
import Customers from '../views/Customers.vue'
import AgentPerformance from '../views/AgentPerformance.vue'

const routes = [
  { path: '/', component: Dashboard },
  { path: '/upload', component: Upload },
  { path: '/graphs', component: Graphs },
  { path: '/critique', component: Critique },
  { path: '/customers', component: Customers },
  { path: '/agents', component: AgentPerformance },
  { path: '/call/:id', component: Call, props: true }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
