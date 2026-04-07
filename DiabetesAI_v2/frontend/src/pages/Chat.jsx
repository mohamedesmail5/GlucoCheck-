import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { axios } from '../lib/auth'
import { useMessages, useCreateSession, GRADE_META } from '../lib/api'

export default function Chat() {
  const { sessionId: paramId } = useParams()
  const navigate = useNavigate()
  const [sessionId, setSessionId] = useState(paramId || null)
  const [messages, setMessages]   = useState([])
  const [input, setInput]         = useState('')
  const [loading, setLoading]     = useState(false)
  const [imagePreview, setImagePreview] = useState(null)
  const [imageUrl, setImageUrl]   = useState(null)
  const [uploadingImg, setUploadingImg] = useState(false)
  const bottomRef = useRef(null)
  const createSession = useCreateSession()

  // Load existing messages
  const { data: existingMsgs } = useMessages(sessionId)
  useEffect(() => {
    if (existingMsgs?.length) {
      setMessages(existingMsgs.map(m => ({ role: m.role, text: m.content })))
    }
  }, [existingMsgs])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Image Dropzone
  const onDrop = useCallback(async (files) => {
    const file = files[0]
    if (!file) return
    setImagePreview(URL.createObjectURL(file))
    setUploadingImg(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const { data } = await axios.post('/api/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setImageUrl(data.url)
      if (data.cnn_result) {
        const r = data.cnn_result
        toast.success(`CNN: ${r.label_ar} — ثقة ${r.confidence}%`)
      }
    } catch {
      toast.error('فشل رفع الصورة')
      setImagePreview(null)
    } finally {
      setUploadingImg(false)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'image/*': ['.jpg','.jpeg','.png','.webp'] }, maxFiles: 1
  })

  const sendMessage = async () => {
    if (!input.trim() && !imageUrl) return
    if (loading) return

    let sid = sessionId
    if (!sid) {
      const s = await createSession.mutateAsync()
      sid = s.id
      setSessionId(sid)
      navigate(`/chat/${sid}`, { replace: true })
    }

    const userMsg = { role: 'user', text: input, image: imagePreview }
    setMessages(prev => [...prev, userMsg])
    const sentInput = input
    const sentImage = imageUrl
    setInput('')
    setImagePreview(null)
    setImageUrl(null)
    setLoading(true)

    // Streaming via SSE
    try {
      const agentMsg = { role: 'agent', text: '', streaming: true }
      setMessages(prev => [...prev, agentMsg])

      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ session_id: sid, message: sentInput, image_url: sentImage })
      })

      const reader  = response.body.getReader()
      const decoder = new TextDecoder()
      let full = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n').filter(l => l.startsWith('data: '))
        for (const line of lines) {
          try {
            const payload = JSON.parse(line.slice(6))
            if (payload.token) {
              full += payload.token
              setMessages(prev => {
                const copy = [...prev]
                copy[copy.length - 1] = { role: 'agent', text: full, streaming: true }
                return copy
              })
            }
            if (payload.done) {
              setMessages(prev => {
                const copy = [...prev]
                copy[copy.length - 1] = { role: 'agent', text: full, grade: payload.grade }
                return copy
              })
            }
          } catch {}
        }
      }
    } catch {
      toast.error('حدث خطأ في الاتصال بالذكاء الاصطناعي')
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-white/5 bg-navy-50/50">
        <div className="w-2 h-2 rounded-full bg-jade animate-pulse-slow" />
        <h1 className="font-display font-semibold text-white">DiabetesAI — مساعد تشخيص السكري</h1>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
        {messages.length === 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center h-full text-center py-16">
            <div className="w-16 h-16 rounded-2xl bg-azure/10 border border-azure/20 flex items-center justify-center mb-5">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" strokeWidth="2" strokeLinecap="round">
                <path d="M2 15c6.667-6 13.333 0 20-6"/><path d="M9 22c1.798-1.998 2.518-3.995 2.807-5.993"/>
                <path d="M15 2c-1.798 1.998-2.518 3.995-2.807 5.993"/>
              </svg>
            </div>
            <h2 className="font-display font-bold text-white text-xl mb-2">مرحباً، كيف يمكنني مساعدتك؟</h2>
            <p className="text-slate-500 text-sm max-w-md font-body leading-relaxed">
              أخبرني عن نتائج فحوصاتك (سكر الدم، HbA1c، الأعراض) أو ارفع صورة شبكية العين للتشخيص.
            </p>
            <div className="grid grid-cols-2 gap-3 mt-6 w-full max-w-sm">
              {starters.map(s => (
                <button key={s} onClick={() => setInput(s)}
                  className="text-right p-3 rounded-xl bg-navy-50 border border-white/5 hover:border-azure/25
                             text-slate-400 hover:text-white text-xs font-body transition-all duration-150">
                  {s}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[78%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'msg-user text-white rounded-tr-sm'
                  : 'msg-agent text-slate-200 rounded-tl-sm'
              }`}>
                {msg.image && (
                  <img src={msg.image} alt="medical" className="w-40 h-32 object-cover rounded-lg mb-2" />
                )}
                <p className={`font-body text-sm leading-relaxed whitespace-pre-wrap ${msg.streaming ? 'streaming-cursor' : ''}`}>
                  {msg.text}
                </p>
                {msg.grade !== null && msg.grade !== undefined && !msg.streaming && (
                  <div className="mt-3 pt-3 border-t border-white/10 flex items-center gap-2">
                    <span className="text-xs text-slate-500 font-mono">التشخيص:</span>
                    <GradePill grade={msg.grade} />
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>

      {/* Image preview */}
      {imagePreview && (
        <div className="px-6 pb-2">
          <div className="inline-flex items-center gap-2 bg-navy-100 border border-white/10 rounded-xl px-3 py-2">
            <img src={imagePreview} alt="" className="w-10 h-10 rounded-lg object-cover" />
            <div>
              <p className="text-white text-xs font-body">{uploadingImg ? 'جاري الرفع...' : 'صورة جاهزة'}</p>
              {uploadingImg && <div className="w-16 h-1 bg-navy-200 rounded-full mt-1"><div className="h-full bg-azure rounded-full animate-shimmer w-1/2" /></div>}
            </div>
            <button onClick={() => { setImagePreview(null); setImageUrl(null) }}
              className="text-slate-500 hover:text-rose ml-2">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="px-6 pb-6 pt-3 border-t border-white/5 bg-navy-50/30">
        {/* Dropzone */}
        <div {...getRootProps()}
          className={`mb-3 border-2 border-dashed rounded-xl px-4 py-3 text-center cursor-pointer transition-all duration-150
            ${isDragActive ? 'border-azure bg-azure/10 text-azure' : 'border-white/10 text-slate-600 hover:border-white/20 hover:text-slate-500'}`}>
          <input {...getInputProps()} />
          <p className="text-xs font-mono">
            {isDragActive ? 'أفلت الصورة هنا' : 'اسحب صورة شبكية العين هنا أو انقر للاختيار'}
          </p>
        </div>

        <div className="flex gap-3">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="اكتب سؤالك أو أدخل نتائج فحوصاتك..."
            rows={2}
            className="input-field flex-1 resize-none"
          />
          <button onClick={sendMessage} disabled={loading || (!input.trim() && !imageUrl)}
            className="btn-primary px-5 self-end disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2">
            {loading ? <SpinIcon /> : <SendIcon />}
            <span className="hidden sm:inline">{loading ? 'جاري...' : 'إرسال'}</span>
          </button>
        </div>
        <p className="text-slate-700 text-xs mt-2 font-mono text-center">
          Enter للإرسال — Shift+Enter لسطر جديد
        </p>
      </div>
    </div>
  )
}

function GradePill({ grade }) {
  const meta = GRADE_META[grade]
  const colors = ['text-jade border-jade/40 bg-jade/10','text-amber border-amber/40 bg-amber/10','text-orange-400 border-orange-400/40 bg-orange-400/10','text-rose border-rose/40 bg-rose/10']
  return (
    <span className={`text-xs font-mono px-2 py-0.5 rounded-full border ${colors[grade]}`}>
      Grade {grade} — {meta?.label}
    </span>
  )
}

function SendIcon() { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg> }
function SpinIcon() { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="animate-spin"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> }

const starters = [
  'سكري الصائم 180 mg/dL، ما التشخيص؟',
  'HbA1c 8.5%، ماذا يعني ذلك؟',
  'ما هي أعراض السكري من النوع الثاني؟',
  'كيف أتحكم في مستوى السكر يومياً؟'
]
