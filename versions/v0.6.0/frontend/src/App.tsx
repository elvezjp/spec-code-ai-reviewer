import { BrowserRouter, Routes, Route } from 'react-router-dom'
import {
  Layout,
  Header,
  Card,
  Button,
  VersionSelector,
  SettingsModal,
  useModal,
  useVersions,
  useSettings,
  DEFAULT_VERSIONS,
} from '@core/index'

function ReviewerDemo() {
  const settingsModal = useModal()
  const { versions, currentVersion, switchVersion } = useVersions(DEFAULT_VERSIONS)
  const { settings, saveToStorage, clearStorage } = useSettings()

  const appInfo = {
    name: 'spec-code-ai-reviewer',
    version: 'v0.6.0',
    copyright: '© 株式会社エルブズ',
    url: 'https://elvez.co.jp',
  }

  return (
    <Layout>
      <Header
        title="設計書-Javaプログラム突合 AIレビュアー"
        leftContent={
          <VersionSelector
            versions={versions}
            currentVersion={currentVersion}
            onVersionSelect={switchVersion}
          />
        }
        rightContent={
          <button
            onClick={settingsModal.open}
            className="text-gray-500 hover:text-gray-700 text-2xl"
            title="設定"
          >
            ⚙️
          </button>
        }
      />

      <Card>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          Phase 2 - Core Components Demo
        </h2>
        <div className="space-y-4">
          <div className="flex gap-2 flex-wrap">
            <Button variant="primary">Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="danger">Danger</Button>
            <Button variant="success">Success</Button>
            <Button disabled>Disabled</Button>
          </div>
          <p className="text-sm text-gray-600">
            Coreコンポーネントが正常に動作しています。
          </p>
        </div>
      </Card>

      <SettingsModal
        isOpen={settingsModal.isOpen}
        onClose={settingsModal.close}
        appInfo={appInfo}
        onConfigFileLoad={(content, filename) => {
          console.log('Config loaded:', filename, content.length)
        }}
        onSaveToStorage={saveToStorage}
        onClearStorage={clearStorage}
        llmSettings={settings.llm}
        onModelChange={(model) => console.log('Model changed:', model)}
        onTestConnection={async () => {
          await new Promise((r) => setTimeout(r, 1000))
          return true
        }}
        isSystemFallback={!settings.llm.apiKey}
        systemPromptPresets={settings.systemPrompts}
      />
    </Layout>
  )
}

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
        <Route path="/" element={<ReviewerDemo />} />
        <Route path="/config-generator" element={<ConfigGeneratorDemo />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
