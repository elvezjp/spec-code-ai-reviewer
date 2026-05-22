import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ReviewerPage } from '@/pages/ReviewerPage'
import { ConfigFileGeneratorPage } from '@/pages/ConfigFileGeneratorPage'
import { PresetsPage } from '@/pages/PresetsPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ReviewerPage />} />
        <Route path="/config-file-generator" element={<ConfigFileGeneratorPage />} />
        <Route path="/presets" element={<PresetsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
