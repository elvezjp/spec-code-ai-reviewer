import { Layout, Header, Card } from '@core/index'

export function NotFoundPage() {
  return (
    <Layout>
      <Header title="404 - Not Found" />
      <Card>
        <p className="text-gray-600 text-center">ページが見つかりません</p>
      </Card>
    </Layout>
  )
}
