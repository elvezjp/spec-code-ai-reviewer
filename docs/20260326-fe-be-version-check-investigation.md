# フロントエンド・バックエンドバージョン整合と `/health` 経路に関する調査・検討まとめ

この文書は、GitHub Issue #79 周辺の事象を契機に行った調査と、**バージョン不一致にユーザーが気づきにくい問題**への対策案・実装時の注意点を整理したものです。実装手順の確定稿ではなく、検討の記録です。

---

## 1. 背景（Issue #79 との関係）

### 1.1 事象

- 「分割」モード選択時に、事前重要指定・事前除外指定パネル（`PreImportantPanel`）が表示されない。
- 期待動作: `docs/split-review.md` に従い、`POST /api/split/headings` で H2 一覧を取得し、事前指定 UI が表示されること。

### 1.2 調査で示された原因（Issue コメント）

- 対象例: `versions/v0.9.4/frontend/.../api.ts` の `fetchHeadings` で **`response.ok` を確認していない**。
- **バックエンド停止時**: `fetch` が例外となり `catch` でエラー表示されやすい。
- **古いバックエンド（例: v0.9.1）で 405 など**: JSON をパースし、`success === false` に当たらないと見出しが空配列になり、**エラーなしで静かに壊れる**。

### 1.3 別要因としての「バージョン不一致への気づきの弱さ」

- フロントとバックエンドのバージョンが揃っていないとき、上記のように**症状だけが出て原因が分かりにくい**。
- 対策の一方として、**バックエンドのバージョンを取得し、フロントの想定と比較する**流れが検討された。

---

## 2. バージョン不一致への対策アイデア（概要）

実装の優先度・組み合わせは別途決定する。候補は例えば以下。

| 方向 | 内容 |
|------|------|
| 起動時・初回 API 前の互換チェック | バックエンドのバージョン API を呼び、フロントが期待する範囲と比較。範囲外ならバナー／モーダル。 |
| UI での明示 | フロント版・接続先 API 版を常に表示（設定・フッターなど）。 |
| レスポンス共通メタ | `X-API-Version` 等（フロントのフェッチ層で検証）。 |
| デプロイ単位の揃え | Docker Compose / リリースをセットで配布。README で「同じマイナーで揃える」と明記。 |
| 診断情報のコピー | FE/BE バージョン・接続先をまとめてコピー（サポート用）。 |

本リポジトリでは **既にバックエンドにバージョン付きのヘルス応答がある**ため（後述）、新規の「版専用 API」は必須ではない。

---

## 3. バックエンド既存 API の整理（v0.9.4 `routers` 中心）

### 3.1 `app/routers` 配下

| エンドポイント（例） | 用途 | バージョン検知との関係 |
|---------------------|------|------------------------|
| `GET /api/convert/available-tools` | 変換ツール一覧 | **軽い GET**。接続先が本アプリかのスモークに使える。版文字列は含まない。 |
| `POST /api/split/headings` | 見出し一覧 | **機能动線そのもの**。古いサーバーでは 405 等になり得る。失敗時の扱いを誤ると静かに空データになり得る。 |
| `POST /api/test-connection` | LLM 接続テスト | 認証・LLM 依存。**版確認用途には不向き**。 |

### 3.2 `main.py`（ルーター外）

- `GET /health`  
  - 応答例: `{"status": "healthy", "version": APP_VERSION}`  
  - `APP_VERSION` は `importlib.metadata.version("spec-code-ai-reviewer-backend")`（`pyproject.toml` の版に相当。多くの場合 **`v` なし、例: `0.9.5`**）。

FastAPI の `FastAPI(..., version=APP_VERSION)` により **`GET /openapi.json` の `info.version`** とも整合する。

---

## 4. フロントでヘルス／バージョンをいつ呼ぶか

### 4.1 推奨イメージ

- **バックエンドのベース URL が決まった直後**に **非同期で 1 回**（初期表示をブロックしない）。
- **Reviewer（または App）マウント時**の `useEffect` が分かりやすい。
- バージョン切替（`useVersions` の `switchVersion`）は **Cookie 設定後に `window.location.reload()`** するため、**リロード後の初回表示＝再度マウント時**に同じ経路で再取得すればよいケースが多い。

### 4.2 `available-tools` との同期

- 現状（v0.9.5）: `Reviewer` で `useEffect` により **`loadTools()` のみ**マウント時に実行。
- ヘルス取得は **`loadTools` と同じ `useEffect` で並列**、または **`loadTools` 内で `Promise.all`** などとし、**取得タイミングを揃えてよい**。

---

## 5. 「現在のフロントエンドのバージョン」の出どころ

| ソース | 内容 | 備考 |
|--------|------|------|
| `APP_INFO.version`（例: `Reviewer` 内） | 画面・設定に渡す表示用（例: `v0.9.5`） | **ハードコード**と `package.json` の二重管理に注意。 |
| `package.json` の `version` | 例: `0.9.5` | import またはビルド時 `import.meta.env` で単一ソース化しやすい。 |
| `useVersions().currentVersion.value` | Cookie 由来の**選択中バージョン**（Docker 等） | 「ビルドされたバンドルの版」と**理論上ずれる可能性**がある。 |

**バックエンドの `health.version` と並べる場合**は、`APP_INFO` と **表記ゆれ（`v` の有無）を正規化してから比較**する。

---

## 6. リクエスト経路の問題（重要）

### 6.1 単一バージョン起動（Vite dev + uvicorn）

- README どおり、フロントは Vite（例: 5173）、API は別ポート（例: 8000）。
- `versions/v0.9.5/frontend/vite.config.ts` では **`/api` のみ** `VITE_API_URL`（既定 `http://localhost:8000`）へプロキシ。
- バックエンドのヘルスは **`GET /health`（`/api` 配下ではない）**。
- そのため、ブラウザから **`fetch('/health')` だけではプロキシされず**、Vite 側に当たる可能性がある。**`/health` をバックエンドへプロキシする設定追加**などが必要。

### 6.2 Docker Compose（`nginx/dev.conf`）

- `location /api/` で API を `backend:$backend_port` に転送する構成。
- **`location /api/health`** が upstream の **`/api/health`** を指している一方、FastAPI は **`@app.get("/health")` のみ**のため、**nginx が想定するパスとアプリの実パスが一致していない可能性**がある。
- 本番寄りの `nginx/spec-code-ai-reviewer.conf` では **`location /health` → バックエンドの `/health`** となっており、こちらは整合的。

### 6.3 結論（経路）

**「`available-tools` と同じように、確実に意図したバックエンドへ届ける」**には、次のいずれか（または併用）が現実的。

1. **Vite**: `/health` を API と同じ target へプロキシする。  
2. **Docker nginx**: 本番と同様に **`/health` → `/health`** に揃える、など。  
3. **バックエンド**: **`GET /api/health`** を追加し、フロントは常に `/api/...` だけで叩く（後述）。

---

## 7. `/api/health` を router 以下に追加する案への意見

### メリット

- フロントの **`getBackendUrl() + '/api/...'`** 規約と一致。  
- **Vite の `/api` プロキシだけ**でヘルスも届きやすい。  
- `nginx` の **`location /api/` 一括プロキシ**とも相性がよい。

### デメリット・注意

- 既存の **`GET /health`**（ALB 等）と**二重入口**になる。**実装は 1 関数に集約**し、両方から呼ぶのがよい。  
- 「health はインフラ用」と割り切るなら **`main.py` に `/api/health` だけ足す**プロジェクトも多い。**必ずしも `routers/` が必須ではない**（プロジェクト規約次第）。

### 結論

**「ブラウザからは `/api` 経由に統一したい」なら `/api/health` は妥当。**  
**ルート `/health` はインフラ・後方互換のため残し、ロジックは共通化**するのがおすすめ。

---

## 8. 修正計画

対応 Issue: [#81](https://github.com/elvezjp/spec-code-ai-reviewer/issues/81)

### 8.1 方針決定

セクション 6〜7 の検討を踏まえ、以下の方針を採用する。

**経路**: バックエンドに `GET /api/health` を追加し、フロントエンドは `/api/...` 経由に統一する。

理由:
- Vite の既存プロキシ（`/api` → `localhost:8000`）をそのまま利用でき、**Vite 設定の変更が不要**
- nginx の `location /api/` 一括プロキシとも整合する
- 既存の `GET /health` はインフラ（ALB 等）用にそのまま残す

**スコープ**: 単一バージョン起動時の乖離検知を優先する。Docker Compose 環境はバージョンが揃いやすいため、後回しでよい。

### 8.2 修正対象と手順

#### Step 1: バックエンド — `GET /api/health` の追加

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.5/backend/app/main.py` | `GET /api/health` を追加。既存の `GET /health` とロジックを共通化 |

```python
async def _health_response():
    """ヘルスチェック共通ロジック"""
    return {"status": "healthy", "version": APP_VERSION}

@app.get("/health")
async def health_check():
    """ヘルスチェック（ルートレベル）- ALB用"""
    return await _health_response()

@app.get("/api/health")
async def api_health_check():
    """ヘルスチェック（API配下）- フロントエンド用"""
    return await _health_response()
```

#### Step 2: フロントエンド — `fetchHealth()` の追加

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.5/frontend/src/features/reviewer/services/api.ts` | `fetchHealth()` 関数を追加 |

```typescript
export interface HealthResponse {
  status: string
  version: string
}

export async function fetchHealth(): Promise<HealthResponse | null> {
  try {
    const response = await fetch(`${getBackendUrl()}/api/health`)
    if (!response.ok) return null
    return await response.json()
  } catch {
    return null  // バックエンド未起動・到達不可
  }
}
```

- 失敗時は `null` を返し、呼び出し元でハンドリング
- `assertResponseOk` は使わない（ヘルスチェック失敗でアプリ全体がエラーになるのを避ける）

#### Step 3: フロントエンド — バージョン比較と警告バナー

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.5/frontend/src/features/reviewer/index.tsx` | マウント時に `fetchHealth()` を呼び、`APP_INFO.version` と比較。不一致時に `backendVersionMismatch` state をセットし、バナーを表示 |

**バージョン比較ロジック**:

```typescript
function normalizeVersion(v: string): string {
  return v.replace(/^v/, '')  // "v0.9.5" → "0.9.5"
}

// マウント時（loadTools と同じ useEffect 内で並列実行）
const health = await fetchHealth()
if (health) {
  const feVersion = normalizeVersion(APP_INFO.version)
  const beVersion = normalizeVersion(health.version)
  if (feVersion !== beVersion) {
    setBackendVersionMismatch({ frontend: APP_INFO.version, backend: health.version })
  }
}
```

**警告バナー**（画面上部に表示）:

```
⚠ バックエンド (v0.9.1) とフロントエンド (v0.9.5) のバージョンが一致しません。
  正しく動作しない可能性があります。
```

- 閉じるボタン付き（`×` で非表示にできる）
- `fetchHealth` 失敗時（バックエンド未起動、古すぎて `/api/health` がない等）は警告を出さない
  - バックエンド未起動は他の API 呼び出し時にエラーとして検知されるため

#### Step 4: ドキュメント更新

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.5/spec.md` | API一覧に `GET /api/health` を追加。API詳細に `GET /api/health` のエンドポイント説明を追加。バージョン不一致検知機能の記載を追加 |

#### Step 5: テストの追加

| ファイル | 修正内容 |
|---|---|
| `versions/v0.9.5/backend/tests/test_health.py` | `GET /api/health` のテスト（ステータス、バージョン文字列の存在） |
| `versions/v0.9.5/frontend/src/__tests__/features/reviewer/services/api_response_check.test.ts` | `fetchHealth()` のテスト（正常、エラー、ネットワーク障害） |

**バックエンドテストケース**:

| ケース | 内容 |
|---|---|
| `GET /api/health` 正常 | `status: "healthy"` と `version` 文字列が返ること |
| `GET /health` 既存互換 | 従来通り動作すること |
| 両エンドポイントの一致 | `/health` と `/api/health` が同じレスポンスを返すこと |

**フロントエンドテストケース**:

| ケース | 内容 |
|---|---|
| fetchHealth: 正常レスポンス | `HealthResponse` オブジェクトが返ること |
| fetchHealth: 非2xxレスポンス | `null` が返ること |
| fetchHealth: ネットワークエラー | `null` が返ること（例外がスローされないこと） |

### 8.3 変更不要な箇所

| 対象 | 理由 |
|---|---|
| `vite.config.ts` | `/api` プロキシが既にあるため、`/api/health` は追加設定なしで到達可能 |
| `nginx/dev.conf` | `location /api/` 一括プロキシで `/api/health` もカバーされる |
| `nginx/spec-code-ai-reviewer.conf` | 同上 |
| `nginx/version-map.conf` | バージョンルーティングに変更なし |

### 8.4 修正順序と依存関係

```
Step 1: バックエンド — GET /api/health 追加
  ↓
Step 2: フロントエンド — fetchHealth() 追加（Step 1 の API を利用）
  ↓
Step 3: フロントエンド — バージョン比較と警告バナー（Step 2 の関数を利用）
  ↓
Step 4: ドキュメント更新（spec.md）
  ↓
Step 5: テスト追加
```

### 8.5 完了チェックリスト

- [ ] バックエンド: `GET /api/health` 追加、`GET /health` とロジック共通化
- [ ] フロントエンド: `fetchHealth()` 関数追加
- [ ] フロントエンド: マウント時バージョン比較、不一致バナー表示
- [ ] ドキュメント: `versions/v0.9.5/spec.md` に `GET /api/health` と不一致検知機能を追記
- [ ] バックエンドテスト追加・全テスト通過
- [ ] フロントエンドテスト追加・全テスト通過
- [ ] 手動動作確認（v0.9.1 バックエンド + v0.9.5 フロントエンドで警告バナー表示）

---

## 9. 参考リンク

- Issue #79: https://github.com/elvezjp/spec-code-ai-reviewer/issues/79
- Issue #81: https://github.com/elvezjp/spec-code-ai-reviewer/issues/81
- PR #80: https://github.com/elvezjp/spec-code-ai-reviewer/pull/80（response.ok チェック修正）
- 分割レビュー仕様: `docs/split-review.md`
- 起動方式: `README_ja.md`（単一バージョン / Docker Compose）

---

## 改訂履歴

| 日付 | 内容 |
|------|------|
| 2026-03-26 | 初版（会話での調査・検討の集約） |
| 2026-03-26 | セクション 8 に修正計画を追加（Issue #81） |
