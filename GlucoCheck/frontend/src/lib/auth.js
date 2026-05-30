import { create } from 'zustand'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

axios.defaults.baseURL = API
axios.interceptors.request.use(cfg => {
  const token = localStorage.getItem('access_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

axios.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const { data } = await axios.post('/api/refresh', { refresh_token: refreshToken })
          localStorage.setItem('access_token', data.access_token)
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`
          return axios(originalRequest)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export const useAuth = create((set) => ({
  token: localStorage.getItem('access_token'),
  user:  JSON.parse(localStorage.getItem('user') || 'null'),

  login: async (email, password) => {
    const { data } = await axios.post('/api/login', { email, password })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    set({ token: data.access_token, user: data.user })
    return data
  },

  register: async (email, password, full_name) => {
    const { data } = await axios.post('/api/register', { email, password, full_name })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    set({ token: data.access_token, user: data.user })
    return data
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    set({ token: null, user: null })
  },

  updateUser: (user) => {
    localStorage.setItem('user', JSON.stringify(user))
    set({ user })
  }
}))

export { axios }
