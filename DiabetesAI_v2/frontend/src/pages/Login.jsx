import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { useAuth } from '../lib/auth'

export default function Login() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading]   = useState(false)
  const { login } = useAuth()
  const navigate  = useNavigate()

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await login(email, password)
      toast.success('أهلاً بعودتك')
      navigate('/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'بيانات الدخول غير صحيحة')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-navy bg-grid-pattern flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-azure/15 border border-azure/30 flex items-center justify-center mx-auto mb-4">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" strokeWidth="2" strokeLinecap="round">
              <path d="M2 15c6.667-6 13.333 0 20-6"/><path d="M9 22c1.798-1.998 2.518-3.995 2.807-5.993"/>
              <path d="M15 2c-1.798 1.998-2.518 3.995-2.807 5.993"/>
            </svg>
          </div>
          <h1 className="font-display font-bold text-white text-2xl">تسجيل الدخول</h1>
          <p className="text-slate-500 text-sm mt-1 font-body">أدخل بياناتك للوصول إلى حسابك</p>
        </div>

        <div className="card">
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="block text-slate-400 text-sm mb-1.5 font-body">البريد الإلكتروني</label>
              <input
                type="email" value={email} onChange={e => setEmail(e.target.value)}
                className="input-field" placeholder="you@example.com" required dir="ltr"
              />
            </div>
            <div>
              <label className="block text-slate-400 text-sm mb-1.5 font-body">كلمة المرور</label>
              <input
                type="password" value={password} onChange={e => setPassword(e.target.value)}
                className="input-field" placeholder="••••••••" required dir="ltr"
              />
            </div>
            <button type="submit" disabled={loading}
              className="btn-primary w-full mt-2 disabled:opacity-50 disabled:cursor-not-allowed">
              {loading ? 'جاري الدخول...' : 'تسجيل الدخول'}
            </button>
          </form>

          <p className="text-center text-slate-500 text-sm mt-5 font-body">
            ليس لديك حساب؟{' '}
            <Link to="/register" className="text-azure hover:underline">إنشاء حساب جديد</Link>
          </p>
        </div>

        <p className="text-center mt-4">
          <Link to="/" className="text-slate-600 text-sm hover:text-slate-400 transition-colors">
            الرجوع للصفحة الرئيسية
          </Link>
        </p>
      </motion.div>
    </div>
  )
}
