import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Landing  from './pages/Landing'
import Login    from './pages/Login'
import Register from './pages/Register'
import Chat     from './pages/Chat'
import Dashboard from './pages/Dashboard'
import History  from './pages/History'
import Profile  from './pages/Profile'
import Layout   from './components/Layout'
import { useAuth } from './lib/auth'

function Protected({ children }) {
  const { token } = useAuth()
  return token ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-center"
        toastOptions={{
          style: { background: '#111e38', color: '#e2e8f0', border: '1px solid rgba(255,255,255,0.08)' }
        }}
      />
      <Routes>
        <Route path="/"         element={<Landing />} />
        <Route path="/login"    element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route element={<Protected><Layout /></Protected>}>
          <Route path="/dashboard"       element={<Dashboard />} />
          <Route path="/chat"            element={<Chat />} />
          <Route path="/chat/:sessionId" element={<Chat />} />
          <Route path="/history"         element={<History />} />
          <Route path="/profile"         element={<Profile />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
