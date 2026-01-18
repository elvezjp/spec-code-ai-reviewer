import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ReviewerPage } from '@/pages/ReviewerPage'
import { ConfigGeneratorPage } from '@/pages/ConfigGeneratorPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ReviewerPage />} />
        <Route path="/config-generator" element={<ConfigGeneratorPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
