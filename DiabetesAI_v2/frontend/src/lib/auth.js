import { create } from 'zustand'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

axios.defaults.baseURL = API
axios.interceptors.request.use(cfg => {
  const token = localStorage.getItem('access_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

export const useAuth = create((set) => ({
  token: localStorage.getItem('access_token'),
  user:  JSON.parse(localStorage.getItem('user') || 'null'),

  login: async (email, password) => {
    const { data } = await axios.post('/api/login', { email, password })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    set({ token: data.access_token, user: data.user })
    return data
  },

  register: async (email, password, full_name) => {
    const { data } = await axios.post('/api/register', { email, password, full_name })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    set({ token: data.access_token, user: data.user })
    return data
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    set({ token: null, user: null })
  },

  updateUser: (user) => {
    localStorage.setItem('user', JSON.stringify(user))
    set({ user })
  }
}))

export { axios }
