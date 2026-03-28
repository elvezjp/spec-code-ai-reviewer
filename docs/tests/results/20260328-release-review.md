# v0.9.6 OSS公開前リリースレビュー

- レビュー実施日: 2026-03-28
- 対象バージョン: v0.9.6
- ブランチ: tominaga/20260328-add-integrate-retry-skip
- PR: #91, #94
- レビュー担当: Claude Opus 4.6（Claude Code）

## 1. 文書棚卸し

| ドキュメント | 英語版 | 日本語版 | 状態 |
|---|---|---|---|
| LICENSE | MIT (Copyright 2025 Elvez) | - | OK |
| README | README.md | README_ja.md | OK |
| CHANGELOG | CHANGELOG.md | CHANGELOG_ja.md | OK |
| CONTRIBUTING | CONTRIBUTING.md | CONTRIBUTING_ja.md | OK |
| SECURITY | SECURITY.md | SECURITY_ja.md | OK |
| CI | .github/workflows/ci.yml | - | OK |

主要文書が日英揃っており、一式完備。

## 2. 文書間の相互リンク

| チェック項目 | 結果 | 備考 |
|---|---|---|
| README → CHANGELOG へのリンク | OK | 英語版・日本語版ともにリンクあり |
| README → CONTRIBUTING へのリンク | OK | 英語版・日本語版ともにリンクあり |
| README → SECURITY へのリンク | OK | 英語版・日本語版ともにリンクあり |
| README → LICENSE へのリンク | OK | 英語版・日本語版ともにリンクあり |
| README_ja → 日本語版各文書へのリンク | OK | 各文書の日本語版を参照 |
| 各文書の英語/日本語切替リンク | OK | 全文書にヘッダーで切替リンクあり |

## 3. PR#91 / PR#94 対応の反映確認

| 項目 | 結果 | 備考 |
|---|---|---|
| CHANGELOG.md に #90, #92, #93 記載 | OK | v0.9.6 セクション（2026-03-28）に記載 |
| CHANGELOG_ja.md に #90, #92, #93 記載 | OK | v0.9.6 セクション（2026-03-28）に記載 |
| SECURITY / SECURITY_ja サポートバージョン | OK | 0.9.6 に更新済み |
| CONTRIBUTING / CONTRIBUTING_ja バージョン | OK | v0.9.6 に更新済み |
| README / README_ja ディレクトリ構成 | OK | v0.9.6 を最新版として記載 |
| README / README_ja ポート割り当て表 | OK | v0.9.6 (8096) を記載 |
| versions/README.md | OK | v0.9.6 を最新版として記載、比較表にも反映 |
| CI (ci.yml) working-directory | OK | versions/v0.9.6/backend および frontend |
| CHANGELOG バージョン比較表 | OK | v0.9.6 行を追加済み |

## 4. ライセンス確認

| チェック項目 | 結果 | 備考 |
|---|---|---|
| LICENSE ファイル存在 | OK | ルートに配置 |
| ライセンス種別 | MIT License | READMEバッジ (MIT) と一致 |
| 著作権表示 | Copyright (c) 2025 Elvez | 初回コミット年として妥当 |
| README のライセンス表記との整合 | OK | 英語版・日本語版ともに MIT License と記載しリンクあり |

## 5. Keep a Changelog / SemVer 準拠確認

| チェック項目 | 結果 | 備考 |
|---|---|---|
| Keep a Changelog フォーマット宣言 | OK | 英語版・日本語版ともにヘッダーに記載 |
| カテゴリ使用 (Added/Changed/Fixed/Removed) | OK | 適切に分類 |
| リリース日記載 | OK | 全バージョンに日付あり |
| SemVer 準拠 | OK | `X.Y.Z` 形式 |
| バージョン比較リンク | 未設定 | `[0.9.6]: https://github.com/.../compare/...` 形式のリンク定義なし（改善推奨） |

## 6. SECURITY ポリシー確認

| チェック項目 | 結果 | 備考 |
|---|---|---|
| サポートバージョン記載 | OK | 0.9.6 のみサポート |
| 脆弱性報告方法 | OK | プライベートセキュリティアドバイザリ推奨 |
| 公開 Issue での報告回避の導線 | OK | 「公開の GitHub Issue を作成しないでください」と明記 |
| 対応スケジュール記載 | OK | 初回応答48時間以内、重大度別に期限を明示 |
| メールでの報告手段 | 未設定 | README に `info@elvez.co.jp` があるが SECURITY に記載なし（改善推奨） |

## 7. CONTRIBUTING 確認

| チェック項目 | 結果 | 備考 |
|---|---|---|
| 貢献方法の説明 | OK | バグ報告・機能提案・PR の手順を記載 |
| 開発環境セットアップ | OK | Python / Node.js / uv の前提条件とインストール手順 |
| テスト実行コマンド | OK | バックエンド・フロントエンドのテストコマンドを記載 |
| コーディングスタイル | OK | Python (PEP 8) / TypeScript (ESLint) のガイドライン |
| コミットメッセージ規約 | OK | 現在形・命令形・72文字制限を明記 |
| バージョン番号 | OK | v0.9.6 に更新済み |

## 8. 指摘事項

### 改善推奨（公開ブロッカーではない）

1. **CHANGELOG のバージョン比較リンク未設定**: Keep a Changelog 推奨のフッターリンク定義（`[0.9.6]: https://github.com/elvezjp/spec-code-ai-reviewer/compare/v0.9.5...v0.9.6`）がない。利用者がバージョン間差分を追いやすくなるため追加推奨。

2. **SECURITY にメール報告手段がない**: README に `info@elvez.co.jp` があるが、SECURITY.md の報告方法にメール連絡先が含まれていない。GitHub に不慣れな報告者向けに追加推奨。

3. **LICENSE の著作権年**: `Copyright (c) 2025 Elvez` は初回コミット年として妥当だが、2026年の現在 `2025-2026` とするかは方針次第。

4. **`.env.example` の内容確認**: README で `cp .env.example .env` を案内しており、ファイルも存在する。機密情報のプレースホルダー以外が含まれていないか念のため確認推奨。

## 9. 総合判定

**公開可能。** 主要文書（LICENSE / README / CHANGELOG / CONTRIBUTING / SECURITY）が日英揃っており、相互リンクも正しく、v0.9.6 への更新が全文書に反映されている。指摘4点は改善推奨だが、公開をブロックする問題はない。

## 10. Cursor（oss-release-docs スキル）によるレビュー追記

- レビュー実施: 2026-03-28（本ドキュメントへの追記と同一日）
- 基準: Cursor エージェントスキル `oss-release-docs`、および同スキル参照先の README / CHANGELOG / SECURITY / CONTRIBUTING / LICENSE 要件
- レビュー担当: Cursor（Auto）

### 10.1 結論

OSS として公開して大きな問題になる欠落はない。ルートに LICENSE・日英 README・SECURITY・CONTRIBUTING・CHANGELOG が揃い、README から主要ドキュメントとライセンスに辿れる。CI は `versions/v0.9.6` を対象としている。

社内 README テンプレート（readme-requirements）まで厳密に合わせる場合は、下記「10.3」の見出し・構成のギャップを埋めるとよい。

### 10.2 PR#91 / PR#94 と CHANGELOG の対応

| PR | CHANGELOG 上の参照 | 整合 |
|----|-------------------|------|
| PR #91（コードパート除外・重要・要約等） | Issue **#90** | PR 本文 `Closes #90` と一致 |
| PR #94（結果統合リトライのスキップ） | Issue **#93** | PR 本文 `Closes #93` と一致 |

CHANGELOG は Issue 番号で記載されているため、PR 番号で追跡したい場合は括弧で PR 番号を追記する運用も可（現状の Issue 参照でも実務上は多くの場合十分）。

### 10.3 社内 README テンプレ準拠で優先したい項目

| 項目 | 内容 |
|------|------|
| Use Cases / ユースケース | readme-requirements では必須。現状は Features で価値は伝わるが、**具体的利用シーン**の独立見出しがない |
| Documentation / ドキュメント | CHANGELOG・CONTRIBUTING・SECURITY 等を **1 見出しにまとめる** 想定。末尾で個別リンクはあるが一覧見出しがない |
| 見出し順 | テンプレは **セットアップ → 使い方**。現状 README は **使い方 → セットアップ**（公開可否には直結しない） |

### 10.4 軽微な不整合・任意調整

| 項目 | 内容 |
|------|------|
| CHANGELOG_ja.md | Keep a Changelog のリンクが英語版 URL（`/en/1.0.0/`）のまま。日本語ファイルなら `https://keepachangelog.com/ja/1.0.0/` に揃え可能 |
| 開発の背景（英文） | 社内テンプレの定型（例: 「small utility」「IXV (Ixiv)」）と表現が一部異なる。承認フローに合わせて統一するかは任意 |
| README の `git clone` | SSH（`git@github.com:...`）。CONTRIBUTING は HTTPS。外部コントリビュータ向けに README にも HTTPS 例を併記すると親切 |
| LICENSE 年号 | `2025` のみ。2026 年継続開発を反映するなら `2025-2026` 等への更新はよくある運用（必須ではない） |

### 10.5 セクション 8 との関係

セクション 8 の改善推奨（CHANGELOG 比較リンク、SECURITY のメール報告、LICENSE 年号、`.env.example` 確認）と整合する。本追記では **README テンプレギャップ** と **PR/Issue 番号の読み方** を追加観点として記録した。

### 10.6 本セクションの総合コメント

**公開可能（セクション 9 と同趣旨）。** 社内 README 必須項目に完全準拠させるなら、**Use Cases** と **Documentation** 見出しの追加、および任意で見出し順・リンク・年号の調整を推奨する。
