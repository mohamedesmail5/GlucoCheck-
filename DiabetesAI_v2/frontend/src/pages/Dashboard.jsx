import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { axios, useAuth } from '../lib/auth'
import { GRADE_META, getGradeBadgeClass } from '../lib/api'
import { formatDistanceToNow } from 'date-fns'
import { ar } from 'date-fns/locale'

const stagger = { show: { transition: { staggerChildren: 0.08 } } }
const item    = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const { data: stats, isLoading: sL } = useQuery({
    queryKey: ['stats'],
    queryFn:  () => axios.get('/api/stats').then(r => r.data)
  })
  const { data: sessions = [], isLoading: sesL } = useQuery({
    queryKey: ['sessions'],
    queryFn:  () => axios.get('/api/sessions').then(r => r.data)
  })
  const { data: diagnoses = [] } = useQuery({
    queryKey: ['diagnoses'],
    queryFn:  () => axios.get('/api/diagnoses').then(r => r.data)
  })

  const gradeDistData = [
    { name: 'Grade 0', value: stats?.grade_distribution?.[0] || 0, color: '#10b981' },
    { name: 'Grade 1', value: stats?.grade_distribution?.[1] || 0, color: '#f59e0b' },
    { name: 'Grade 2', value: stats?.grade_distribution?.[2] || 0, color: '#f97316' },
    { name: 'Grade 3', value: stats?.grade_distribution?.[3] || 0, color: '#f43f5e' },
  ]

  const trend = diagnoses.slice(0, 10).reverse().map((d, i) => ({
    session: `#${i + 1}`,
    grade: d.grade
  }))

  const lastGrade = stats?.last_grade ?? null

  return (
    <div className="p-8">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="font-display font-bold text-white text-3xl">
          مرحباً، {user?.full_name?.split(' ')[0]}
        </h1>
        <p className="text-slate-500 mt-1 font-body">لوحة متابعة حالتك الصحية</p>
      </motion.div>

      {/* Stat Cards */}
      <motion.div variants={stagger} initial="hidden" animate="show"
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">

        <StatCard icon={<SessionsIcon />} label="إجمالي الجلسات"
          value={sL ? '...' : stats?.total_sessions ?? 0}
          sub="جلسة محادثة" color="azure" variants={item} />

        <StatCard icon={<DiagIcon />} label="إجمالي التشخيصات"
          value={sL ? '...' : stats?.total_diagnoses ?? 0}
          sub="تشخيص مكتمل" color="jade" variants={item} />

        <StatCard icon={<GradeIcon />} label="آخر تشخيص"
          value={lastGrade !== null
            ? <span className={getGradeBadgeClass(lastGrade)}>{GRADE_META[lastGrade]?.label}</span>
            : '—'}
          sub={lastGrade !== null ? `Grade ${lastGrade}` : 'لا يوجد بعد'} color="amber" variants={item} />

        <StatCard icon={<AccIcon />} label="دقة النموذج"
          value="98%+" sub="CNN + XGBoost" color="azure" variants={item} />
      </motion.div>

      {/* Charts Row */}
      <motion.div variants={stagger} initial="hidden" animate="show"
        className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">

        {/* Trend chart */}
        <motion.div variants={item} className="card">
          <h2 className="font-display font-semibold text-white mb-4">تطور درجات السكري</h2>
          {trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={trend}>
                <defs>
                  <linearGradient id="gradeGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#0ea5e9" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="session" stroke="#334155" tick={{ fill: '#64748b', fontSize: 11 }} />
                <YAxis domain={[0, 3]} ticks={[0,1,2,3]} stroke="#334155" tick={{ fill: '#64748b', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: '#111e38', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10 }}
                  labelStyle={{ color: '#94a3b8' }}
                  formatter={(v) => [`Grade ${v}`, 'الدرجة']}
                />
                <Area type="monotone" dataKey="grade" stroke="#0ea5e9" fill="url(#gradeGrad)" strokeWidth={2} dot={{ fill: '#0ea5e9', r: 4 }} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState label="لا توجد تشخيصات بعد — ابدأ محادثة" />
          )}
        </motion.div>

        {/* Distribution bar chart */}
        <motion.div variants={item} className="card">
          <h2 className="font-display font-semibold text-white mb-4">توزيع درجات التشخيص</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={gradeDistData} barSize={36}>
              <XAxis dataKey="name" stroke="#334155" tick={{ fill: '#64748b', fontSize: 11 }} />
              <YAxis stroke="#334155" tick={{ fill: '#64748b', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#111e38', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10 }}
                labelStyle={{ color: '#94a3b8' }}
                formatter={(v) => [v, 'عدد التشخيصات']}
              />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {gradeDistData.map((d, i) => <Cell key={i} fill={d.color} fillOpacity={0.85} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </motion.div>

      {/* Recent Sessions */}
      <motion.div variants={item} initial="hidden" animate="show" className="card">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-display font-semibold text-white text-lg">آخر الجلسات</h2>
          <button onClick={() => navigate('/history')}
            className="text-azure text-sm hover:underline font-body">عرض الكل</button>
        </div>

        {sesL ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-14 rounded-xl bg-navy/60 animate-pulse" />
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <EmptyState label="لا توجد جلسات بعد" />
        ) : (
          <div className="space-y-2">
            {sessions.slice(0, 6).map(s => (
              <div key={s.id}
                onClick={() => navigate(`/chat/${s.id}`)}
                className="flex items-center justify-between p-3.5 rounded-xl bg-navy/50 border border-white/5
                           hover:border-azure/20 hover:bg-azure/5 cursor-pointer transition-all duration-150">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-navy-200 border border-white/5 flex items-center justify-center">
                    <ChatSmIcon />
                  </div>
                  <div>
                    <p className="text-white text-sm font-body">{s.title}</p>
                    <p className="text-slate-500 text-xs mt-0.5">
                      {formatDistanceToNow(new Date(s.updated_at), { addSuffix: true, locale: ar })}
                    </p>
                  </div>
                </div>
                {s.grade !== null && s.grade !== undefined && (
                  <span className={getGradeBadgeClass(s.grade)}>
                    Grade {s.grade}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}

        <button onClick={() => navigate('/chat')}
          className="btn-primary w-full mt-5 flex items-center justify-center gap-2">
          <PlusIcon />
          ابدأ جلسة جديدة
        </button>
      </motion.div>
    </div>
  )
}

// ─── Sub-components ─────────────────────────────────────────────────────────
function StatCard({ icon, label, value, sub, color, variants }) {
  const colorMap = {
    azure:  'bg-azure/10 border-azure/20 text-azure',
    jade:   'bg-jade/10 border-jade/20 text-jade',
    amber:  'bg-amber/10 border-amber/20 text-amber',
  }
  return (
    <motion.div variants={variants} className="card hover:border-white/10 transition-colors duration-200">
      <div className={`w-10 h-10 rounded-xl border flex items-center justify-center mb-4 ${colorMap[color]}`}>
        {icon}
      </div>
      <p className="text-slate-400 text-sm font-body">{label}</p>
      <div className="text-2xl font-display font-bold text-white mt-1">{value}</div>
      <p className="text-slate-600 text-xs mt-1 font-mono">{sub}</p>
    </motion.div>
  )
}

function EmptyState({ label }) {
  return (
    <div className="flex flex-col items-center justify-center py-10 text-slate-600">
      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className="mb-3 opacity-40">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <p className="text-sm font-body">{label}</p>
    </div>
  )
}

// Icons
function SessionsIcon() { return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg> }
function DiagIcon() { return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg> }
function GradeIcon() { return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg> }
function AccIcon() { return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg> }
function ChatSmIcon() { return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg> }
function PlusIcon() { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> }
