import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout, Header, Card } from '@core/index'
import { ReviewerPage } from '@/pages/ReviewerPage'
import { ConfigGeneratorPage } from '@/pages/ConfigGeneratorPage'

function NotFoundPage() {
  return (
    <Layout>
      <Header title="404 - Not Found" />
      <Card>
        <p className="text-gray-600">ページが見つかりません</p>
      </Card>
    </Layout>
  )
}

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
