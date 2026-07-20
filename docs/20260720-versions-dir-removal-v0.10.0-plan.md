# `versions/` ディレクトリ廃止と v0.10.0 開発準備 計画書

作成日: 2026-07-20

## 1. 背景・目的

これまで本リポジトリは、`versions/` ディレクトリに全バージョン（v0.5.0〜v0.9.9）のスナップショットを実体として保持し、nginx（Cookie + map）でバージョンごとのポート振り分け、UI 左上のバルーンでランタイムのバージョン切替を提供してきた。

この構成には以下の問題がある。

- Dependabot アラートが旧バージョンの lockfile ごとに重複通知される（#103）
- subtree として取り込んだ `markitdown/`（#96）、`excel2md/`（#100）、`add-line-numbers/` / `code2map/` / `md2map/`（#103）が実質未使用のまま残っている
- 新バージョン追加のたびに `useVersions.ts` / nginx map / PM2 設定 / docker-compose など多数のファイルの定型更新が必要（#118）
- #113 以降の新機能を実装する際、`versions/v0.10.0/` を新設してファイル一式をコピーする運用コストが大きい

本計画では `versions/` ディレクトリを廃止し、**最新コードのみをルート直下で保持する構成**へ移行する。移行後は次の運用とする。

- main ブランチには次バージョンの変更を **Unreleased** として蓄積する（CHANGELOG の `[Unreleased]` セクション運用）
- リリース時に `pyproject.toml` のバージョンを確定し、git tag（`vX.Y.Z`）を打つ
- 旧構成（`versions/` ディレクトリ時代）のバージョンを利用したい場合は、既存の **`v0.9.9` タグ**を checkout する。このタグには `versions/` の全スナップショット（v0.5.0〜v0.9.9）と subtree 一式が含まれるため、旧バージョンごとの tag を新規作成する必要はない
- 移行完了後の最初の開発バージョンを **v0.10.0** とし、#113 等の新機能はルート直下のコードに対して実装する

### 関連 Issue

| Issue | 内容 | 本計画での扱い |
| --- | --- | --- |
| #96 | `markitdown/` が未使用（PyPI からインストール） | subtree 削除・README に git clone での取得方法を記載 |
| #100 | `excel2md` の sys.path 注入を uv 管理に揃える | PyPI 版 `excel2md>=2.2.1` へ移行（案 A）・subtree 削除 |
| #103 | `versions/` 廃止・残依存の uv 管理移行 | 本計画の中核。`versions/` 削除・subtree 削除。旧構成は v0.9.9 タグで参照 |
| #118 | ランタイムバージョン切替機能の廃止 | 本計画の前提整理。フェーズ 1 で実施 |
| #113 ほか | v0.10.0 で実装予定の新機能 | 本移行完了後、ルート直下のコードを対象に実装 |

## 2. 移行後の理想的なディレクトリ構成

`versions/v0.9.9/` の内容をルートに昇格させ、以下の構成とする。

```
spec-code-ai-reviewer/
├── .github/
│   └── workflows/
│       └── ci.yml                  # working-directory を backend/ / frontend/ に変更
├── backend/                        # ← versions/v0.9.9/backend を昇格
│   ├── app/
│   ├── tests/
│   ├── pyproject.toml              # version = "0.10.0"（開発中は Unreleased 扱い）
│   └── uv.lock
├── frontend/                       # ← versions/v0.9.9/frontend を昇格
│   ├── src/
│   ├── package.json
│   └── ...
├── docs/
│   ├── spec.md                     # ← versions/v0.9.9/spec.md を移動
│   ├── config-file-generator-spec.md  # ← versions/v0.9.9/ から移動
│   ├── ec2-deployment-spec.md      # OLD 扱い（冒頭に注記を追加するのみ。内容は更新しない）
│   └── （既存の計画書類）
├── .env.example
├── CHANGELOG.md / CHANGELOG_ja.md  # [Unreleased] セクション運用を開始
├── README.md / README_ja.md        # バージョン管理・セットアップ手順を全面書き換え
├── CONTRIBUTING.md / CONTRIBUTING_ja.md
├── SECURITY.md / SECURITY_ja.md    # versions/・subtree 前提の記述を更新
└── LICENSE
```

**なくなるもの**: `versions/`、`latest` シンボリックリンク、subtree 5 ディレクトリ（`markitdown/`、`excel2md/`、`add-line-numbers/`、`code2map/`、`md2map/`）、`nginx/`（ディレクトリごと）、`docker-compose.yml`、`Dockerfile.dev`、`docker-entrypoint.sh`、`ecosystem.config.js`、`dev.ecosystem.config.js`、`scripts/`（`sync_version.py` ごと）

nginx はバージョン切替のルーティングのために必要だったもので、Docker 関連ファイルはその nginx をローカルで起動するための環境だった。バージョン切替の廃止によりどちらも不要になる。PM2（ecosystem.config.js）による本番プロセス管理も廃止する。移行後のローカル起動は「uvicorn 直接起動 + Vite」の単一バージョン起動のみとなる。

## 3. 削除対象の一覧

### 3.1 ディレクトリ・シンボリックリンク

| 対象 | 理由 | 前提条件 |
| --- | --- | --- |
| `versions/`（README.md 含む全体） | 旧構成は既存の `v0.9.9` タグの checkout で参照可能 | README に v0.9.9 checkout の案内を記載 |
| `latest -> versions/v0.9.9` | ルート直下が常に最新になるため不要 | — |
| `markitdown/` | PyPI の `markitdown[xlsx,docx]` を使用しており未参照（#96） | README に旧バージョン向け git clone 手順を記載 |
| `excel2md/` | PyPI 公開済み（v2.2.1）。sys.path 注入を撤去し依存宣言に移行（#100） | フェーズ 3 のコード修正とセット |
| `add-line-numbers/` | v0.9.x は git ソース（uv）で取得済み。実体は旧バージョン（v0.8.x 以前）の path 参照のみ | `versions/` 削除とセット（旧バージョンは v0.9.9 タグの checkout で subtree ごと復元される） |
| `code2map/` | 同上 | 同上 |
| `md2map/` | 同上 | 同上 |

> **補足**: v0.5.0〜v0.8.2 の `pyproject.toml` は `[tool.uv.sources]` で `path = "../../../add-line-numbers"` 等のローカル path を参照している。`v0.9.9` タグには `versions/` 全体と subtree 一式が含まれるため、タグを checkout すれば全旧バージョンが従来どおり動作する。旧バージョンごとの tag を新規作成する必要はない。

### 3.2 インフラ・設定ファイル・スクリプト

| 対象 | 理由 |
| --- | --- |
| `nginx/`（`version-map.conf` / `dev.conf` / `spec-code-ai-reviewer.conf`） | nginx はバージョン切替ルーティングのために必要だった。切替廃止により役割がなくなるため、ディレクトリごと削除（#118） |
| `docker-compose.yml` / `Dockerfile.dev` / `docker-entrypoint.sh` | Docker 環境は nginx をローカル起動するためのものだった。nginx 廃止に伴い削除 |
| `ecosystem.config.js` / `dev.ecosystem.config.js` | PM2 によるマルチバージョンのプロセス管理を廃止 |
| `scripts/`（`sync_version.py` ごと） | 複数バージョン間のバージョン表記同期が不要になるためスクリプトごと削除。バージョン表示はバックエンドの `GET /health`（`APP_VERSION`）等から取得する方式に置き換え |

### 3.3 フロントエンドのバージョン切替機能（#118）

| 対象 | 内容 |
| --- | --- |
| `frontend/src/core/hooks/useVersions.ts` | `DEFAULT_VERSIONS` / Cookie 読み書き / `switchVersion` を含むフックごと削除 |
| `frontend/src/core/components/shared/VersionSelector.tsx` | バルーン UI を削除 |
| `frontend/src/core/index.ts` | `VersionSelector` / `useVersions` / `DEFAULT_VERSIONS` の export を削除 |
| `frontend/src/features/reviewer/index.tsx` | `useVersions()` 呼び出し（46 行目付近）と `<VersionSelector>`（836 行目付近）を削除 |
| `app_version` Cookie | 読み書きコードを削除（nginx 側の参照も同時撤去） |

設定モーダルの「起動中のバージョン番号の表示」は残す。`sync_version.py` は廃止するため、バージョン値の取得元はバックエンドの `GET /health`（`APP_VERSION` を返却済み）またはビルド時定数へ置き換える（`index.html` の表記書き換えに依存しない形にする）。

## 4. 実装修正が必要な箇所

### 4.1 インフラ・起動設定（#118）

nginx / Docker / PM2 は修正ではなく**削除**する（セクション 3.2 参照）。修正としては以下のみ。

- 「バージョン番号由来のポート割り当てルール」（8099 = v0.9.9 等）は廃止し、移行後の起動方法は README の「Single-Version Launch」相当（`uv run uvicorn app.main:app` + `npm run dev` / `npm run build`）に一本化する
- README から「Docker Compose Launch (Multi-Version)」セクションを削除し、単一バージョン起動の手順のみを残す

### 4.2 バックエンド（#100: excel2md の uv 移行）

| ファイル | 修正内容 |
| --- | --- |
| `backend/pyproject.toml` | `dependencies` に `"excel2md>=2.2.1"` を追加（PyPI 公開済みのため `[tool.uv.sources]` への追記は不要）。`version` を `0.10.0` に更新 |
| `backend/app/markdown_tools/excel2md_tool.py` | `_DEFAULT_EXCEL2MD_PATH` / `EXCEL2MD_PATH` 環境変数 / `sys.path.insert` による動的注入を撤去し、通常 import（`from excel2md import ...`。上流公開 API の `ConversionConfig` / `ExcelConverter` / `convert_to_markdown` 等に合わせて書き換え）に変更 |
| `backend/app/markdown_tools/excel2md_mermaid_tool.py` | 同上（`EXCEL2MD_PATH` の import と sys.path 操作を撤去） |
| `backend/tests/` | excel2md 関連テストのモック・パス前提を新 import に追従 |
| `backend/uv.lock` | `uv sync` で再生成 |

なお `_DEFAULT_EXCEL2MD_PATH` はディレクトリ階層（`versions/vX.Y.Z/backend/...` から 6 階層上）に依存しているため、ルート昇格だけでもパスが壊れる。**フェーズ 2（昇格）と同時か先行して必ず対応する。**

### 4.3 CI

| ファイル | 修正内容 |
| --- | --- |
| `.github/workflows/ci.yml` | `working-directory` を `versions/v0.9.9/backend` → `backend`、`versions/v0.9.9/frontend` → `frontend` に変更 |

### 4.4 ドキュメント

| ファイル | 修正内容 |
| --- | --- |
| `README.md` / `README_ja.md` | 「Version Management」「Port Assignment Rule」「Changes Required When Adding a New Version」「Production Update Steps」「Docker Compose Launch (Multi-Version)」「Directory Structure」「Version Sync」「Updating Subtrees」を全面書き換えまたは削除。git tag ベースのリリース運用、単一バージョンのセットアップ手順（`cd backend` / `cd frontend`）、**旧構成のバージョンを利用したい場合は `git checkout v0.9.9` で取得する**旨、subtree の代わりに各リポジトリを git clone で参照する方法（#96 の方針）を記載。バージョン切替バルーンの記述（174 行目付近の Note 等）を削除 |
| `docs/spec.md`（移動後） | 「3.5 バージョン切替UI」「13.3.4 バージョン切替テスト」（E2E-VS-002 等）を削除。Cookie `app_version` に関する記述を削除 |
| `CHANGELOG.md` / `CHANGELOG_ja.md` | `[Unreleased]` セクションを新設し、以後のリリース運用（リリース時に `[0.10.0] - YYYY-MM-DD` へ確定して tag）を開始。本移行自体を Unreleased に記録 |
| `CONTRIBUTING.md` / `CONTRIBUTING_ja.md` | `cd versions/v0.9.9/...` のパス（46 / 53 / 94 / 106 / 116 行目付近）と「最新バージョン（`versions/v0.9.9/`）に焦点を当てる」の記述をルートパスに更新 |
| `SECURITY.md` / `SECURITY_ja.md` | 「旧バージョン（`versions/`）は Dismiss」「subtree で取り込んでおり〜」の Dependabot 運用方針（129 / 138 行目付近）を、単一バージョン + git tag 構成に合わせて書き換え |
| `docs/ec2-deployment-spec.md` | **OLD 扱いとし、内容は更新しない**。冒頭に「本書はマルチバージョン構成（〜v0.9.9）時代の EC2 デプロイ仕様であり、現行構成には適用されない」旨の注記のみ追加（またはファイル名に OLD プレフィックスを付与） |

## 5. 移行フェーズ

### フェーズ 0: 旧構成への到達性の確認（#103）

旧バージョンごとの git tag は**新規作成しない**。既存の `v0.9.9` タグに `versions/` の全スナップショット（v0.5.0〜v0.9.9）と subtree 一式が含まれており、これを checkout すれば旧構成をそのまま利用できるため。

1. `v0.9.9` タグが `versions/` 全体を含むコミットを指していることを確認する（確認済み: 現 main と同一コミット `0e90288`）
2. README に「旧構成のバージョンを利用したい場合は `git checkout v0.9.9` で取得する」旨を記載する（フェーズ 4 のドキュメント整備に含める）
3. `versions/README.md` にあったバージョン比較表は、必要なら `docs/` へ退避するか CHANGELOG への参照で代替する

### フェーズ 1: ランタイムバージョン切替機能とインフラ一式の廃止（#118）

- セクション 3.3 のフロントエンド削除を実施
- セクション 3.2 のインフラ一式（`nginx/`、Docker 関連 3 ファイル、`ecosystem.config.js` / `dev.ecosystem.config.js`）を削除
- この時点ではまだ `versions/v0.9.9/` 構成のままでもよい（#118 単独 PR とする場合）。ただしフェーズ 2 と同一 PR での実施も可

### フェーズ 2: v0.9.9 のルート昇格と v0.10.0 開発開始

1. `git mv versions/v0.9.9/backend backend`、`git mv versions/v0.9.9/frontend frontend`（履歴追跡のため `git mv` を使用）
2. `versions/v0.9.9/spec.md` / `config-file-generator-spec.md` を `docs/` へ移動
3. `backend/pyproject.toml` の `version` を `0.10.0` に更新、CHANGELOG に `[Unreleased]` を新設
4. CI の `working-directory` を更新（4.3）
5. `latest` シンボリックリンクと `versions/`（残りの旧バージョン）を削除
6. `scripts/`（`sync_version.py`）を削除し、フロントのバージョン表示を `GET /health` またはビルド時定数からの取得に置き換え
7. ルートで `uv sync` / `uv run pytest`、`npm ci` / `npm run test:run` / `npm run build` が通ることを確認

### フェーズ 3: subtree ディレクトリの削除と依存整理（#96 / #100 / #103）

1. `excel2md` を PyPI 依存に移行し、`sys.path` 注入を撤去（4.2）
2. `markitdown/`、`excel2md/`、`add-line-numbers/`、`code2map/`、`md2map/` を削除
3. `ecosystem.config.js` / `dev.ecosystem.config.js` から `PYTHONPATH` の subtree 参照を削除（フェーズ 1 で未実施の場合）
4. README の「Related Projects」に、参照用途では各 OSS リポジトリを git clone する旨を記載（#96 コメントの方針）

### フェーズ 4: ドキュメント整備

1. セクション 4.4 のドキュメント更新（`ec2-deployment-spec.md` は OLD 注記のみ）
2. 本番（EC2）環境の扱いは本計画のスコープ外とする。PM2 / nginx ベースの本番運用は廃止方針のため、既存 EC2 環境の停止・移行や旧バージョン利用ユーザーへの周知（#118 の留意点）は別途判断する
3. Dependabot: `versions/` と subtree の削除により重複アラートは自動クローズされる見込み。残存アラートは SECURITY.md の新方針で運用

### フェーズ 5 以降: v0.10.0 の機能実装

- #113（プロンプトキャッシュ）、#114〜#117、#119〜#121 をルート直下のコードに対して実装
- リリース時: CHANGELOG の `[Unreleased]` を `[0.10.0]` に確定 → `pyproject.toml` 確認 → tag `v0.10.0` 作成・push → 本番デプロイ

## 6. リスク・留意点

| リスク | 対応 |
| --- | --- |
| `v0.9.9` タグの削除・付け替えにより旧構成へ到達できなくなる | `v0.9.9` タグを旧構成アーカイブの参照点として位置づけ、削除・付け替えを行わない運用を README に明記 |
| excel2md の PyPI 版 API が既存ファサード（`excel_to_md`）と異なる | 移行時に出力の回帰テスト（既存の excel2md 関連テスト + 実ファイルでの変換確認）を実施。`uv pip install excel2md` での wheel 動作確認を事前に行う |
| ルート昇格により `_DEFAULT_EXCEL2MD_PATH` の相対階層が壊れる | フェーズ 2 と 3 を同一 PR で実施するか、フェーズ 2 内で excel2md 移行を先行させる |
| `git mv` による大規模移動で PR レビューが困難になる | フェーズを分割し、昇格（移動のみ）と修正（差分あり）を別コミットにする |
| 稼働中の EC2 本番環境（PM2 / nginx 構成）が main と乖離する | 本番環境の扱いはスコープ外として別途判断。それまで本番側は現行 tag（v0.9.9 以前）の構成で運用を継続し、main の新構成を `git pull` しない |
| Windows 環境での `latest` シンボリックリンク問題 | `latest` 自体を廃止するため解消される（副次的メリット） |

## 7. 受け入れ条件

- [ ] `git checkout v0.9.9` で旧構成（`versions/` + subtree 一式）が取得でき、その手順が README に記載されている
- [ ] ルート直下の `backend/` / `frontend/` で開発・テスト・起動が完結する（`uv run pytest` / `npm run test:run` / `npm run build` がパス）
- [ ] `versions/`、`latest`、subtree 5 ディレクトリ（markitdown / excel2md / add-line-numbers / code2map / md2map）、`scripts/`（sync_version.py）がリポジトリから削除されている
- [ ] excel2md が PyPI 依存（`excel2md>=2.2.1`）で動作し、`sys.path` 注入・`EXCEL2MD_PATH` が撤去されている
- [ ] 画面からバージョン切替 UI が除去され、設定モーダルに起動中バージョンのみ表示される
- [ ] `nginx/`・Docker 関連ファイル（docker-compose.yml / Dockerfile.dev / docker-entrypoint.sh）・PM2 設定（ecosystem.config.js / dev.ecosystem.config.js）が削除され、uvicorn + Vite の単一バージョン起動で動作する
- [ ] CI がルート構成でグリーン
- [ ] README / CONTRIBUTING / SECURITY / spec.md が新構成・新運用に更新され、ec2-deployment-spec.md に OLD 注記が付与されている
- [ ] CHANGELOG に `[Unreleased]` セクションが導入され、本移行が記録されている
