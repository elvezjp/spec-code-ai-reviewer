# 変更履歴

このプロジェクトに対するすべての重要な変更はこのファイルに記録されます。

フォーマットは [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) に基づいており、
このプロジェクトは [セマンティックバージョニング](https://semver.org/spec/v2.0.0.html) に準拠しています。

## [0.7.0] - 2026-01-25

### 追加
- **AIでMarkdownを整理する機能**: ExcelからAI生成したMarkdownをAIで構造化・正規化する機能を追加
  - 「AIでMarkdownを整理する」ボタンと方針入力欄
  - テンプレート付きの整理方針入力UI
  - react-diff-viewerを使用した整理前後のDiff表示
- **エラー/警告表示**: トークン超過、タイムアウト、改変検出などのアラート表示
- **ツール別前処理**: markdown_toolsに前処理メソッドを追加し、ツール固有の説明文混同問題に対応
- **推定トークン数表示**: 整理実行前にトークン数の目安を表示
- **organize-markdown API**: ファイル単位でMarkdown整理を実行するエンドポイントを追加
- **プリセットライブラリを追加**: プロンプトと設計書種別のプリセットライブラリを追加

### 変更
- **設定ファイル更新**: v0.7.0をlatest版として設定
  - `nginx/version-map.conf`: v0.7.0のルーティング追加、defaultポートを8070に変更
  - `docker-compose.yml`: v0.7.0フロントエンド・ポート8070を追加
  - `ecosystem.config.js`, `dev.ecosystem.config.js`: v0.7.0エントリ追加

### 注意
- **後方互換性**: v0.6.0以前のバージョンは引き続き利用可能（マルチバージョン構成維持）

## [0.6.0] - 2026-01-18

### 追加
- **React + Vite + TypeScript移行**: フロントエンドを単一HTMLファイルからモダンなSPA構成に全面刷新
  - React 19.2.0 + TypeScript 5.9によるコンポーネントベース開発
  - Vite 7.2.4による高速ビルド環境
  - React Router v7によるルーティング（`/` と `/config-file-generator`）
- **Tailwind CSS v4対応**: `@tailwindcss/vite`統合による最適化されたCSS生成
- **テスト環境構築**: Vitest + React Testing Libraryによる単体テスト（8ファイル、20+テストケース）
  - Core Hooks: useSettings, useModal, useScreenManager, useTokenEstimation
  - Feature Hooks: useFileConversion, useZipExport, useConfigState, useValidation
- **コンポーネント設計**: 再利用可能なUIコンポーネントライブラリ
  - core/components/ui: Button, Modal, Table, Card等の基本UI部品
  - core/components/shared: SettingsModal, VersionSelector等の共通機能
- **React Hooks による状態管理**: localStorage統合、モーダル制御、画面状態管理を含む包括的なHooks実装
- **lucide-react導入**: 絵文字をlucide-reactアイコンに統一し、UIの一貫性を向上

### 変更
- **フロントエンド起動方法**: バックエンドと分離して起動（開発時: Vite devサーバー ポート5173、本番: ビルド済みファイル配信）
- **プロジェクト構造**: features/配下に機能別モジュール（reviewer, config-file-generator）を配置
- **型安全性の向上**: すべてのコンポーネントとHooksにTypeScript型定義を適用
- **設定ファイル更新**: v0.6.0をlatest版として設定
  - `nginx/version-map.conf`: v0.6.0のルーティング追加、defaultポートを8060に変更
  - `docker-compose.yml`: v0.6.0フロントエンド・ポート8060を追加
  - `ecosystem.config.js`, `dev.ecosystem.config.js`: v0.6.0エントリ追加

### 注意
- **後方互換性**: v0.5.2以前のバージョンは引き続き利用可能（マルチバージョン構成維持）
- **起動方法変更**: v0.6.0以降はフロントエンドとバックエンドを別々に起動する必要があります（詳細はREADME参照）

## [0.5.2] - 2026-01-13

### 追加
- **Bedrock Converse API対応**: `invoke_model`から`converse`に移行し、Anthropic Claude系とAmazon Novaモデルの両方に対応
- **Amazon Novaモデル対応**: Nova Pro、Nova Microなどのモデルが利用可能に
- **プロバイダー設計の統一**: `get_system_llm_config()`関数を追加し、システムLLM設定の生成を`llm_service.py`に集約
- **設定ファイルジェネレーター改善**: Bedrock選択時にリージョンプレフィックスとトークン上限の注意事項を表示

### 変更
- **設定ファイル更新**: v0.5.2をlatest版として設定
  - `nginx/version-map.conf`: v0.5.2のルーティング追加、defaultポートを8052に変更
  - `docker-compose.yml`: v0.5.2フロントエンド・ポート8052を追加
  - `ecosystem.config.js`, `dev.ecosystem.config.js`: v0.5.2エントリ追加

## [0.5.1] - 2026-01-09

### 追加
- **OpenAI GPT-5.2対応**: GPT-5.2系モデルで必要な`max_completion_tokens`パラメータに対応
- **設定ファイルジェネレーター更新**: OpenAIモデル選択肢にGPT-5.2系を追加

### 変更
- **OpenAI SDK更新**: `openai>=2.14.0` に依存バージョンを引き上げ
- **設定ファイル更新**: v0.5.1をlatest版として設定
  - `nginx/version-map.conf`: v0.5.1のルーティング追加、defaultポートを8051に変更
  - `docker-compose.yml`: v0.5.1フロントエンド・ポート8051を追加
  - `ecosystem.config.js`, `dev.ecosystem.config.js`: v0.5.1エントリ追加
  - `docs/ec2-deployment-spec.md`: ポート表・VERSIONS配列を更新

### 修正
- OpenAI GPT-5.2で`max_tokens`パラメータが使用できない問題を修正（Issue #5）

## [0.5.0] - 2025-12-28

### 追加
- **レビュー複数回実行**: 1回のボタン押下で2回のレビューを直列実行し、結果をタブ切り替えで表示
- **レビュー実行データ一式ダウンロード**: ZIP形式で入出力データ（システムプロンプト、設計書MD、コード、結果）を一括保存
- **ダウンロードファイル名の統一**: `spec-markdown.md`、`code-numbered.txt` に固定

### 変更
- v0.4.0との後方互換性を維持

## [0.4.0] - 2025-12-23

### 追加
- **マルチLLMプロバイダー対応**: Bedrock / Anthropic / OpenAI を切り替えてレビュー実行が可能に（未指定時はBedrockにフォールバック）
- **設定ファイル導入**: `reviewer-config.md` でLLM設定（プロバイダー・認証・モデル一覧）と種別をMarkdownで管理
- **設定モーダル刷新**: 設定ファイルアップロード方式へ移行、モデル選択の記憶・保存/クリア、接続テスト（`/api/health`）機能追加
- **バックエンド拡張**: `llm_service`（抽象化）と `anthropic_service` / `openai_service` を追加
- **excel2md拡張**: CSV+Mermaid形式に対応（フローチャートをMermaid記法で追記）

### 変更
- v0.3.0との後方互換性を維持

## [0.3.0] - 2025-12-21

### 追加
- **マルチ変換ツール対応**: MarkItDown（標準Markdown変換）/ excel2md（シート全体をCSVブロック変換）をファイルごとに選択可能
- **バージョン・スイッチャー追加**: UI左上のピル型ボタンで過去バージョンへ切替可能に
- **レポート機能強化**: 簡易判定セクション（赤/黄/緑）表示、トークン情報表示
- **バックエンド構造改善**: `markdown_tools` パッケージ導入、変換ツールをプラグイン的に拡張可能な構造へリファクタリング
- **一括設定機能**: ツールの全ファイル一括変更が可能に

### 変更
- v0.2.5との後方互換性を維持

## [0.2.5] - 2025-12-19

### 追加
- **優先度・種別設定**: メイン設計書/参照資料の優先度設定が可能に
- **UI改善**: ファイルごとのドロップダウンメニュー追加
- **トークン数表示**: 推測値でトークン数を表示

### 変更
- 変換ツールはMarkItDown固定

## [0.1.1] - 2025-12-15

### 追加
- **初期リリース（MVP）**: 基本的なファイル変換・レビュー機能を実装
- ファイル選択→変換のシンプルなUI
- Excel → Markdown 変換（MarkItDown使用）
- ソースコード → 行番号付与（add-line-numbers準拠）
- AWS Bedrock（Claude）によるレビュー実行
- レビューレポートのコピー・ダウンロード機能

---

## リンク

- [リポジトリ](https://github.com/elvezjp/spec-code-ai-reviewer)
- [Issue](https://github.com/elvezjp/spec-code-ai-reviewer/issues)

---

## バージョン比較

| バージョン | 主な機能 |
|------------|----------|
| 0.7.0      | AIでMarkdownを整理する機能、Diff表示、ツール別前処理、プリセットライブラリ |
| 0.6.0      | React + Vite + TypeScript移行、Tailwind v4、テスト環境構築 |
| 0.5.2      | Bedrock Converse API対応、Amazon Novaモデル対応 |
| 0.5.1      | OpenAI GPT-5.2対応 |
| 0.5.0      | 複数回レビュー実行、一式ダウンロード |
| 0.4.0      | マルチLLMプロバイダー、設定ファイル |
| 0.3.0      | マルチ変換ツール、バージョン切替 |
| 0.2.5      | 優先度・種別設定、トークン数表示 |
| 0.1.1      | 初期リリース（MVP） |
