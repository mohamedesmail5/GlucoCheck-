import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { axios } from './auth'

// ─── Sessions ──────────────────────────────────────────────────────────────────
export const useSessions = () =>
  useQuery({ queryKey: ['sessions'], queryFn: () => axios.get('/api/sessions').then(r => r.data) })

export const useSession = (id) =>
  useQuery({ queryKey: ['session', id], queryFn: () => axios.get(`/api/sessions/${id}`).then(r => r.data), enabled: !!id })

export const useCreateSession = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => axios.post('/api/sessions').then(r => r.data),
    onSuccess:  () => qc.invalidateQueries(['sessions'])
  })
}

export const useDeleteSession = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id) => axios.delete(`/api/sessions/${id}`),
    onSuccess:  () => qc.invalidateQueries(['sessions'])
  })
}

// ─── Stats ─────────────────────────────────────────────────────────────────────
export const useStats = () =>
  useQuery({ queryKey: ['stats'], queryFn: () => axios.get('/api/stats').then(r => r.data) })

// ─── Diagnoses ────────────────────────────────────────────────────────────────
export const useDiagnoses = () =>
  useQuery({ queryKey: ['diagnoses'], queryFn: () => axios.get('/api/diagnoses').then(r => r.data) })

// ─── Messages ────────────────────────────────────────────────────────────────
export const useMessages = (sessionId) =>
  useQuery({
    queryKey: ['messages', sessionId],
    queryFn:  () => axios.get(`/api/messages/${sessionId}`).then(r => r.data),
    enabled:  !!sessionId
  })

// ─── Upload ──────────────────────────────────────────────────────────────────
export const useUpload = () =>
  useMutation({
    mutationFn: (file) => {
      const fd = new FormData()
      fd.append('file', file)
      return axios.post('/api/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data)
    }
  })

// ─── Profile ──────────────────────────────────────────────────────────────────
export const useUpdateProfile = () => {
  return useMutation({
    mutationFn: (data) => axios.put('/api/profile', data).then(r => r.data)
  })
}

// ─── Grade Helpers ─────────────────────────────────────────────────────────────
export const GRADE_META = {
  0: { label: 'طبيعي',        labelEn: 'Normal',   color: '#10b981', bg: 'jade' },
  1: { label: 'خفيف',         labelEn: 'Mild',     color: '#f59e0b', bg: 'amber' },
  2: { label: 'متوسط',        labelEn: 'Moderate', color: '#f97316', bg: 'orange' },
  3: { label: 'حاد',          labelEn: 'Severe',   color: '#f43f5e', bg: 'rose' },
}

export const getGradeBadgeClass = (g) =>
  ['grade-badge-0','grade-badge-1','grade-badge-2','grade-badge-3'][g ?? 0]
