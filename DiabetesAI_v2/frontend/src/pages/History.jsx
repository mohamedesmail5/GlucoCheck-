import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { formatDistanceToNow, format } from 'date-fns'
import { ar } from 'date-fns/locale'
import toast from 'react-hot-toast'
import { useSessions, useDeleteSession, GRADE_META, getGradeBadgeClass } from '../lib/api'

export default function History() {
  const navigate = useNavigate()
  const { data: sessions = [], isLoading } = useSessions()
  const { mutate: deleteSession } = useDeleteSession()
  const [search, setSearch] = useState('')

  const filtered = sessions.filter(s =>
    s.title?.toLowerCase().includes(search.toLowerCase())
  )

  const handleDelete = (e, id) => {
    e.stopPropagation()
    if (!confirm('هل تريد حذف هذه الجلسة؟')) return
    deleteSession(id, { onSuccess: () => toast.success('تم حذف الجلسة') })
  }

  return (
    <div className="p-8">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="font-display font-bold text-white text-3xl">سجل الجلسات</h1>
        <p className="text-slate-500 mt-1 font-body">جميع محادثاتك السابقة مع DiabetesAI</p>
      </motion.div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative max-w-md">
          <svg className="absolute right-3 top-3.5" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input value={search} onChange={e => setSearch(e.target.value)}
            className="input-field pr-10" placeholder="ابحث في الجلسات..." />
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-20 rounded-2xl bg-navy-50 animate-pulse border border-white/5" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="card flex flex-col items-center py-16 text-center">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#334155" strokeWidth="1.5" strokeLinecap="round" className="mb-4">
            <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          <p className="text-slate-500 font-body">{search ? 'لا توجد نتائج' : 'لا توجد جلسات بعد'}</p>
          {!search && (
            <button onClick={() => navigate('/chat')} className="btn-primary mt-4 text-sm px-5 py-2">
              ابدأ جلستك الأولى
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((s, i) => (
            <motion.div key={s.id}
              initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
              onClick={() => navigate(`/chat/${s.id}`)}
              className="card cursor-pointer hover:border-azure/20 hover:bg-azure/3 transition-all duration-150 group">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-navy-200 border border-white/5 flex items-center justify-center flex-shrink-0">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                  </div>
                  <div>
                    <p className="text-white font-body font-medium">{s.title}</p>
                    <p className="text-slate-500 text-xs mt-0.5 font-mono">
                      {format(new Date(s.created_at), 'dd MMM yyyy', { locale: ar })} —
                      {formatDistanceToNow(new Date(s.updated_at), { addSuffix: true, locale: ar })}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {s.grade !== null && s.grade !== undefined && (
                    <span className={getGradeBadgeClass(s.grade)}>Grade {s.grade} — {GRADE_META[s.grade]?.label}</span>
                  )}
                  <button onClick={e => handleDelete(e, s.id)}
                    className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-rose/10 text-slate-600 hover:text-rose transition-all">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
                    </svg>
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
