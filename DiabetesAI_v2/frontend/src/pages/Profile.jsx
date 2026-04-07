import { useState } from 'react'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { axios } from '../lib/auth'
import { useAuth } from '../lib/auth'

export default function Profile() {
  const { user, updateUser, logout } = useAuth()
  const [name, setName]         = useState(user?.full_name || '')
  const [oldPass, setOldPass]   = useState('')
  const [newPass, setNewPass]   = useState('')
  const [saving, setSaving]     = useState(false)
  const [deleting, setDeleting] = useState(false)

  const saveName = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await axios.put('/api/profile', { full_name: name })
      updateUser({ ...user, full_name: name })
      toast.success('تم تحديث الاسم')
    } catch { toast.error('حدث خطأ') }
    finally { setSaving(false) }
  }

  const changePassword = async (e) => {
    e.preventDefault()
    if (newPass.length < 6) return toast.error('كلمة المرور يجب أن تكون 6 أحرف على الأقل')
    setSaving(true)
    try {
      await axios.put('/api/profile', { password: newPass })
      setOldPass(''); setNewPass('')
      toast.success('تم تغيير كلمة المرور')
    } catch { toast.error('حدث خطأ') }
    finally { setSaving(false) }
  }

  const deleteAccount = async () => {
    if (!confirm('هل أنت متأكد من حذف حسابك؟ لا يمكن التراجع عن هذا الإجراء.')) return
    setDeleting(true)
    try {
      await axios.delete('/api/account')
      logout()
    } catch { toast.error('حدث خطأ أثناء حذف الحساب') }
    finally { setDeleting(false) }
  }

  return (
    <div className="p-8 max-w-2xl">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="font-display font-bold text-white text-3xl">الملف الشخصي</h1>
        <p className="text-slate-500 mt-1 font-body">إدارة بيانات حسابك</p>
      </motion.div>

      {/* Avatar */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
        className="card mb-6 flex items-center gap-4">
        <div className="w-16 h-16 rounded-2xl bg-azure/15 border border-azure/30 flex items-center justify-center text-azure font-display font-bold text-2xl">
          {user?.full_name?.[0] || 'U'}
        </div>
        <div>
          <p className="text-white font-display font-semibold text-lg">{user?.full_name}</p>
          <p className="text-slate-500 text-sm font-mono">{user?.email}</p>
        </div>
      </motion.div>

      {/* Update Name */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }}
        className="card mb-5">
        <h2 className="font-display font-semibold text-white mb-4">تعديل الاسم</h2>
        <form onSubmit={saveName} className="space-y-4">
          <div>
            <label className="block text-slate-400 text-sm mb-1.5">الاسم الكامل</label>
            <input value={name} onChange={e => setName(e.target.value)}
              className="input-field" placeholder="الاسم الكامل" required />
          </div>
          <button type="submit" disabled={saving} className="btn-primary text-sm px-5 py-2 disabled:opacity-50">
            {saving ? 'جاري الحفظ...' : 'حفظ التغييرات'}
          </button>
        </form>
      </motion.div>

      {/* Change Password */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
        className="card mb-5">
        <h2 className="font-display font-semibold text-white mb-4">تغيير كلمة المرور</h2>
        <form onSubmit={changePassword} className="space-y-4">
          <div>
            <label className="block text-slate-400 text-sm mb-1.5">كلمة المرور الجديدة</label>
            <input type="password" value={newPass} onChange={e => setNewPass(e.target.value)}
              className="input-field" placeholder="••••••••" required dir="ltr" />
          </div>
          <button type="submit" disabled={saving} className="btn-primary text-sm px-5 py-2 disabled:opacity-50">
            {saving ? 'جاري التغيير...' : 'تغيير كلمة المرور'}
          </button>
        </form>
      </motion.div>

      {/* Danger Zone */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.25 }}
        className="card border-rose/20">
        <h2 className="font-display font-semibold text-rose mb-2">المنطقة الحرجة</h2>
        <p className="text-slate-500 text-sm font-body mb-4">حذف حسابك سيؤدي إلى حذف جميع بياناتك ولا يمكن التراجع.</p>
        <button onClick={deleteAccount} disabled={deleting}
          className="px-5 py-2 rounded-xl border border-rose/30 text-rose hover:bg-rose/10 text-sm font-display transition-all disabled:opacity-50">
          {deleting ? 'جاري الحذف...' : 'حذف الحساب نهائياً'}
        </button>
      </motion.div>
    </div>
  )
}
