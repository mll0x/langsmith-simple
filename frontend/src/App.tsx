import { Routes, Route } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout.tsx'
import TraceListPage from './pages/TraceListPage.tsx'
import TraceDetailPage from './pages/TraceDetailPage.tsx'
import PlaygroundPage from './pages/PlaygroundPage.tsx'
import DeploymentsPage from './pages/DeploymentsPage.tsx'

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<TraceListPage />} />
        <Route path="/traces" element={<TraceListPage />} />
        <Route path="/traces/:id" element={<TraceDetailPage />} />
        <Route path="/playground" element={<PlaygroundPage />} />
        <Route path="/deployments" element={<DeploymentsPage />} />
      </Routes>
    </AppLayout>
  )
}
