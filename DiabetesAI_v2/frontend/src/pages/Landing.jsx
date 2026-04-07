import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'

const fade = { hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0 } }

export default function Landing() {
  return (
    <div className="min-h-screen bg-navy bg-grid-pattern flex flex-col">
      {/* Nav */}
      <header className="flex items-center justify-between px-8 py-5 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-azure/15 border border-azure/30 flex items-center justify-center">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" strokeWidth="2" strokeLinecap="round">
              <path d="M2 15c6.667-6 13.333 0 20-6"/><path d="M9 22c1.798-1.998 2.518-3.995 2.807-5.993"/>
              <path d="M15 2c-1.798 1.998-2.518 3.995-2.807 5.993"/>
            </svg>
          </div>
          <span className="font-display font-bold text-white text-lg">DiabetesAI</span>
        </div>
        <div className="flex gap-3">
          <Link to="/login"    className="btn-ghost text-sm py-2 px-4">تسجيل الدخول</Link>
          <Link to="/register" className="btn-primary text-sm py-2 px-4">ابدأ مجاناً</Link>
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 text-center py-20">
        <motion.div variants={fade} initial="hidden" animate="show" transition={{ duration: 0.6 }}>
          <div className="inline-flex items-center gap-2 bg-azure/10 border border-azure/25 rounded-full px-4 py-1.5 mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-azure animate-pulse-slow" />
            <span className="text-azure text-sm font-mono">دقة الذكاء الاصطناعي: 98%+</span>
          </div>

          <h1 className="font-display font-bold text-5xl md:text-7xl text-white leading-tight mb-6">
            تشخيص السكري
            <br />
            <span className="text-azure">بالذكاء الاصطناعي</span>
          </h1>

          <p className="text-slate-400 text-lg md:text-xl max-w-2xl mx-auto mb-10 font-body leading-relaxed">
            نظام تشخيص متكامل يحلل بياناتك الطبية وصور شبكية العين لتحديد درجة السكري وتقديم خطة رعاية شخصية.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register" className="btn-primary text-base px-8 py-3.5">
              ابدأ التشخيص الآن
            </Link>
            <Link to="/login" className="btn-ghost text-base px-8 py-3.5">
              لديّ حساب بالفعل
            </Link>
          </div>
        </motion.div>

        {/* Feature cards */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-20 max-w-4xl w-full"
          variants={{ show: { transition: { staggerChildren: 0.12 } } }}
          initial="hidden" animate="show"
        >
          {features.map((f) => (
            <motion.div key={f.title} variants={fade} transition={{ duration: 0.5 }}
              className="card text-right hover:border-azure/20 transition-colors duration-300">
              <div className="w-10 h-10 rounded-xl bg-azure/10 border border-azure/20 flex items-center justify-center mb-4 mr-auto ml-0">
                <f.Icon />
              </div>
              <h3 className="font-display font-semibold text-white text-lg mb-2">{f.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed font-body">{f.desc}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* Grades table */}
        <motion.div variants={fade} initial="hidden" animate="show" transition={{ delay: 0.5, duration: 0.6 }}
          className="mt-16 max-w-2xl w-full card">
          <h2 className="font-display font-semibold text-white text-xl mb-5 text-right">تصنيف درجات السكري</h2>
          <div className="space-y-3">
            {grades.map(g => (
              <div key={g.grade} className="flex items-center justify-between p-3 rounded-xl bg-navy/60 border border-white/5">
                <span className={`font-mono text-sm px-3 py-0.5 rounded-full border ${g.cls}`}>Grade {g.grade}</span>
                <span className="text-slate-300 text-sm font-body">{g.label}</span>
                <span className="text-slate-500 text-xs font-mono">{g.range}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </main>

      <footer className="text-center py-6 border-t border-white/5 text-slate-600 text-sm font-mono">
        DiabetesAI — Frontend & Backend Team — 2024/2025
      </footer>
    </div>
  )
}

const grades = [
  { grade: 0, label: 'طبيعي / ما قبل السكري', range: '< 125 mg/dL',    cls: 'bg-jade/10 text-jade border-jade/30' },
  { grade: 1, label: 'سكري خفيف',              range: '126-180 mg/dL', cls: 'bg-amber/10 text-amber border-amber/30' },
  { grade: 2, label: 'سكري متوسط',             range: '181-300 mg/dL', cls: 'bg-orange-500/10 text-orange-400 border-orange-500/30' },
  { grade: 3, label: 'سكري حاد',               range: '> 300 mg/dL',   cls: 'bg-rose/10 text-rose border-rose/30' },
]

const features = [
  {
    title: 'تحليل نصي ذكي',
    desc:  'أدخل نتائج فحوصاتك وأعراضك، وسيحلل الذكاء الاصطناعي حالتك ويحدد درجة السكري.',
    Icon: () => (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" strokeWidth="2" strokeLinecap="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    )
  },
  {
    title: 'تحليل صور شبكية العين',
    desc:  'ارفع صورة شبكية العين وسيشخص نموذج CNN المدرّب على 98%+ دقة حالتك فوراً.',
    Icon: () => (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" strokeWidth="2" strokeLinecap="round">
        <circle cx="12" cy="12" r="3"/><path d="M2 12s4-8 10-8 10 8 10 8-4 8-10 8-10-8-10-8z"/>
      </svg>
    )
  },
  {
    title: 'خطة رعاية شخصية',
    desc:  'بناءً على التشخيص، يقدم الذكاء الاصطناعي توصيات مفصّلة للتغذية والرياضة والدواء.',
    Icon: () => (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" strokeWidth="2" strokeLinecap="round">
        <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
      </svg>
    )
  }
]
