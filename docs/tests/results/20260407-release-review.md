# v0.9.7 OSS公開前リリースレビュー

- レビュー実施日: 2026-04-07
- 対象バージョン: v0.9.7
- ブランチ: takahashi/20260406-feat-word
- PR: #95
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

## 3. PR#95 対応の反映確認

| 項目 | 結果 | 備考 |
|---|---|---|
| CHANGELOG.md に #95, #26 記載 | OK | v0.9.7 セクション（2026-04-07）に記載 |
| CHANGELOG_ja.md に #95, #26 記載 | OK | v0.9.7 セクション（2026-04-07）に記載 |
| SECURITY / SECURITY_ja サポートバージョン | OK | 0.9.7 に更新済み |
| CONTRIBUTING / CONTRIBUTING_ja バージョン | OK | v0.9.7 に更新済み |
| README / README_ja ディレクトリ構成 | OK | v0.9.7 を最新版として記載 |
| README / README_ja ポート割り当て表 | OK | v0.9.7 (8097) を記載 |
| README / README_ja 機能説明 | OK | Word (.docx) 対応を Features に反映済み |
| README / README_ja 使い方 | OK | Excel に加え Word (.docx) の記載あり |
| README / README_ja APIエンドポイント | OK | `/api/convert/word-to-markdown` を追加済み |
| CI (ci.yml) working-directory | OK | versions/v0.9.7/backend および frontend |
| CHANGELOG バージョン比較表 | OK | v0.9.7 行を追加済み |

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
| バージョン比較リンク | 未設定 | `[0.9.7]: https://github.com/.../compare/...` 形式のリンク定義なし（改善推奨・前回から継続） |

## 6. SECURITY ポリシー確認

| チェック項目 | 結果 | 備考 |
|---|---|---|
| サポートバージョン記載 | OK | 0.9.7 のみサポート |
| 脆弱性報告方法 | OK | プライベートセキュリティアドバイザリ推奨 |
| 公開 Issue での報告回避の導線 | OK | 「公開の GitHub Issue を作成しないでください」と明記 |
| 対応スケジュール記載 | OK | 初回応答48時間以内、重大度別に期限を明示 |
| メールでの報告手段 | 未設定 | README に `info@elvez.co.jp` があるが SECURITY に記載なし（改善推奨・前回から継続） |

## 7. CONTRIBUTING 確認

| チェック項目 | 結果 | 備考 |
|---|---|---|
| 貢献方法の説明 | OK | バグ報告・機能提案・PR の手順を記載 |
| 開発環境セットアップ | OK | Python / Node.js / uv の前提条件とインストール手順 |
| テスト実行コマンド | OK | バックエンド・フロントエンドのテストコマンドを記載 |
| コーディングスタイル | OK | Python (PEP 8) / TypeScript (ESLint) のガイドライン |
| コミットメッセージ規約 | OK | 現在形・命令形・72文字制限を明記 |
| バージョン番号 | OK | v0.9.7 に更新済み |

## 8. 指摘事項

### 改善推奨（公開ブロッカーではない）

1. **CHANGELOG のバージョン比較リンク未設定**（前回から継続）: Keep a Changelog 推奨のフッターリンク定義（`[0.9.7]: https://github.com/elvezjp/spec-code-ai-reviewer/compare/v0.9.6...v0.9.7`）がない。利用者がバージョン間差分を追いやすくなるため追加推奨。

2. **SECURITY にメール報告手段がない**（前回から継続）: README に `info@elvez.co.jp` があるが、SECURITY.md の報告方法にメール連絡先が含まれていない。GitHub に不慣れな報告者向けに追加推奨。

3. **CODE_OF_CONDUCT.md が未作成**: CONTRIBUTING.md で「行動規範に従うこと」と言及しているが、対応するファイルが存在しない。リンク先を追加するか、言及を削除するか検討推奨。

## 9. 総合判定

**公開可能。** 主要文書（LICENSE / README / CHANGELOG / CONTRIBUTING / SECURITY）が日英揃っており、相互リンクも正しく、v0.9.7 への更新が全文書に反映されている。PR#95（Word対応）の変更内容がREADMEの機能説明・使い方・APIエンドポイント、CHANGELOGの両言語版に適切に反映されている。指摘3点は改善推奨だが、公開をブロックする問題はない。

---

## 10. 追記: Cursor レビュー（oss-release-docs スキル基準）

- **追記日**: 2026-04-07
- **参照スキル**: `.claude/skills/oss-release-docs/SKILL.md`（公開前の README / CHANGELOG / CONTRIBUTING / SECURITY / LICENSE 棚卸し・整合確認）
- **前提**: 上記セクション 1〜9 は別レビュー（Claude Code）の記録。本節は Cursor 側の追認と差分整理。

### 10.1 総合所見

OSS 公開を妨げる状態ではない。主要文書が揃い、README から CHANGELOG / CONTRIBUTING / SECURITY / LICENSE に辿れる。CHANGELOG 日英の v0.9.7 記述と API 文書（`POST /api/convert/word-to-markdown`）は実装（`app.include_router(convert.router, prefix="/api/convert")` と `convert.py` のルート）と一致する。

### 10.2 README 修正の反映（ユーザー対応後の確認）

| 項目 | 結果 | 備考 |
|---|---|---|
| 冒頭の一行概要（英） | 反映済 | 「Excel / Word format」と Word を明記 |
| 冒頭の一行概要（日） | 反映済 | 「Excel / Word形式」と Word を明記 |

### 10.3 残りの軽微な改善余地（公開ブロッカーではない）

| 項目 | 内容 |
|---|---|
| README の「システム構成」 | バックエンド箇条書きが Excel 向けのまま。Word（.docx / MarkItDown 固定）を一言加えると Features・Usage と対称になる。 |
| SECURITY（英・日）の「ファイル処理」 | 処理対象の列挙に Word (.docx) を足すと、利用者の期待と一致しやすい。 |
| 社内 README 必須の「ユースケース」見出し | oss-release-docs が参照する社内要件では独立セクション必須の場合がある。現状は Usage 等で間接カバー。組織ルールに応じて要否を判断。 |
| LICENSE の Copyright 年 | `(c) 2025` のまま。方針次第で 2026 追記・更新を検討（必須ではないことが多い）。 |
| フロントテストコマンド | README「Run Tests」が `npm test`、CI が `npm run test:run` と表記が分かれる。どちらかに寄せると迷いが減る。 |

### 10.4 実装・依存（公開観点）

- `markitdown[xlsx,docx]` は本番依存として妥当。
- `python-docx` は `pyproject.toml` の dev 依存（テスト用）で、公開リポジトリとして自然。

### 10.5 セクション 8（指摘事項）との関係

セクション 8 にある CHANGELOG 比較リンク・SECURITY のメール手段・CODE_OF_CONDUCT は、本 Cursor レビューでも「改善推奨」のまま有効。README 冒頭要約の不整合はユーザー修正により解消済み。
