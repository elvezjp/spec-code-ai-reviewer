import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout, Header, Card } from '@core/index'
import { ReviewerPage } from '@/pages/ReviewerPage'

function ConfigGeneratorDemo() {
  return (
    <Layout>
      <Header title="設定ファイルジェネレーター" />
      <Card>
        <p className="text-gray-600">Phase 4で実装予定</p>
      </Card>
    </Layout>
  )
}

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
        <Route path="/config-generator" element={<ConfigGeneratorDemo />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
