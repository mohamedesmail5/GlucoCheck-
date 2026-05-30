import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { useAuth } from '../lib/auth'

export default function Register() {
  const [form, setForm]   = useState({ full_name: '', email: '', password: '', confirm: '' })
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    if (form.password !== form.confirm) return toast.error('كلمتا المرور غير متطابقتين')
    if (form.password.length < 6) return toast.error('كلمة المرور يجب أن تكون 6 أحرف على الأقل')
    setLoading(true)
    try {
      await register(form.email, form.password, form.full_name)
      toast.success('تم إنشاء الحساب بنجاح')
      navigate('/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'حدث خطأ أثناء التسجيل')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-navy bg-grid-pattern flex items-center justify-center px-4 py-10">
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <h1 className="font-display font-bold text-white text-2xl">إنشاء حساب جديد</h1>
          <p className="text-slate-500 text-sm mt-1 font-body">انضم إلى DiabetesAI وابدأ رحلتك الصحية</p>
        </div>

        <div className="card">
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="block text-slate-400 text-sm mb-1.5">الاسم الكامل</label>
              <input value={form.full_name} onChange={set('full_name')}
                className="input-field" placeholder="محمد أحمد" required />
            </div>
            <div>
              <label className="block text-slate-400 text-sm mb-1.5">البريد الإلكتروني</label>
              <input type="email" value={form.email} onChange={set('email')}
                className="input-field" placeholder="you@example.com" required dir="ltr" />
            </div>
            <div>
              <label className="block text-slate-400 text-sm mb-1.5">كلمة المرور</label>
              <input type="password" value={form.password} onChange={set('password')}
                className="input-field" placeholder="••••••••" required dir="ltr" />
            </div>
            <div>
              <label className="block text-slate-400 text-sm mb-1.5">تأكيد كلمة المرور</label>
              <input type="password" value={form.confirm} onChange={set('confirm')}
                className="input-field" placeholder="••••••••" required dir="ltr" />
            </div>
            <button type="submit" disabled={loading}
              className="btn-primary w-full mt-2 disabled:opacity-50">
              {loading ? 'جاري الإنشاء...' : 'إنشاء الحساب'}
            </button>
          </form>

          <p className="text-center text-slate-500 text-sm mt-5">
            لديك حساب بالفعل؟{' '}
            <Link to="/login" className="text-azure hover:underline">تسجيل الدخول</Link>
          </p>
        </div>
      </motion.div>
    </div>
  )
}
