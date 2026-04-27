# Dependabot アラート整理計画書

## 概要

リポジトリ全体に発生している 146 件の Dependabot アラート（Vulnerable タブ）について、issue #97 で決定した運用方針に沿って整理する。

- 対応 Issue: [#97](https://github.com/elvezjp/spec-code-ai-reviewer/issues/97)
- 関連 PR: [#98](https://github.com/elvezjp/spec-code-ai-reviewer/pull/98)（運用方針を README に追記）

## 背景

`versions/v0.x.x/` にアーカイブされた旧バージョンと、git subtree で取り込んでいる外部リポジトリディレクトリ（`add-line-numbers/`、`code2map/`、`excel2md/`、`markitdown/`、`md2map/`）が原因で、Dependabot アラートが大量に発生している。本リポジトリで本来対処すべきは最新版（`versions/v0.9.7/`）のみ。

### 現状の内訳（Vulnerable タブ）

| カテゴリ | 件数 | 対応 |
|---|---|---|
| git subtree 配下 | 19 | Dismiss（subtree 元で管理） |
| 旧バージョン（`versions/v0.5.0`〜`v0.9.6`） | 117 | Dismiss（アーカイブ・本番未使用） |
| 最新版（`versions/v0.9.7/`） | 10 | 修正対応 |
| **合計** | **146** | |

### Malware タブ

別途確認し、件数があれば最優先で修正する（場所を問わない）。

---

## Step 1: git subtree 配下のアラートを Dismiss

### 対象

以下のディレクトリ配下のアラート（合計 19 件）:

- `add-line-numbers/`
- `code2map/`（`code2map/versions/` 含む）
- `excel2md/`
- `markitdown/`
- `md2map/`（`md2map/versions/` 含む）

### Dismiss 理由

`not_used`（"Vulnerable code is not actually used"）

理由: subtree 元リポジトリ側で依存管理を行っているため、本リポジトリでは管理対象外。

### 実行コマンド

```bash
# 対象アラート番号を抽出
gh api repos/elvezjp/spec-code-ai-reviewer/dependabot/alerts --paginate \
  -q '.[] | select(.state=="open") |
       select(.dependency.manifest_path | startswith("md2map/") or
              startswith("code2map/") or
              startswith("excel2md/") or
              startswith("add-line-numbers/") or
              startswith("markitdown/")) |
       .number' > /tmp/subtree_alerts.txt

# 一括 Dismiss
while read num; do
  gh api -X PATCH repos/elvezjp/spec-code-ai-reviewer/dependabot/alerts/$num \
    -f state=dismissed \
    -f dismissed_reason=not_used \
    -f dismissed_comment="Managed in upstream subtree repository. See README Dependabot Alert Policy."
done < /tmp/subtree_alerts.txt
```

### 完了条件

- subtree 配下のすべての open アラートが dismissed になっている
- ダッシュボード上の件数が 146 → 127 に減る

---

## Step 2: 旧バージョンのアラートを Dismiss

### 対象

`versions/v0.5.0/` 〜 `versions/v0.9.6/` 配下のアラート（合計 117 件）。
※ `versions/v0.9.7/`（最新版）は除外。

### Dismiss 理由

`not_used`（アーカイブ済み、本番環境では稼働していない）

### 実行コマンド

```bash
# 対象アラート番号を抽出
gh api repos/elvezjp/spec-code-ai-reviewer/dependabot/alerts --paginate \
  -q '.[] | select(.state=="open") |
       select(.dependency.manifest_path | startswith("versions/")) |
       select(.dependency.manifest_path | startswith("versions/v0.9.7/") | not) |
       .number' > /tmp/old_version_alerts.txt

# 一括 Dismiss
while read num; do
  gh api -X PATCH repos/elvezjp/spec-code-ai-reviewer/dependabot/alerts/$num \
    -f state=dismissed \
    -f dismissed_reason=not_used \
    -f dismissed_comment="Archived past version, not used in production. See README Dependabot Alert Policy."
done < /tmp/old_version_alerts.txt
```

### 完了条件

- 旧バージョン配下のすべての open アラートが dismissed になっている
- ダッシュボード上の件数が 127 → 10 に減る

---

## Step 3: 最新版（v0.9.7）のアラートを修正

### 対象（10 件）

| # | 重要度 | パッケージ | manifest | GHSA | 概要 |
|---|---|---|---|---|---|
| 264 | high | lxml | `versions/v0.9.7/backend/uv.lock` | GHSA-vfmq-68hx-4jfw | iterparse / ETCompatXMLParser の XXE |
| 252 | medium | vite | `versions/v0.9.7/frontend/package-lock.json` | GHSA-4w7w-66w2-5vf9 | Optimized Deps `.map` Path Traversal |
| 251 | high | vite | 同上 | GHSA-v2wj-q39q-566r | `server.fs.deny` バイパス |
| 250 | high | vite | 同上 | GHSA-p9ff-h696-f583 | Dev Server WebSocket の任意ファイル読取 |
| 247 | medium | picomatch | 同上 | GHSA-3v7f-55p6-f55p | POSIX Character Classes Method Injection |
| 245 | medium | yaml | 同上 | GHSA-48c2-rrv3-qjmp | 深いネストによる Stack Overflow |
| 244 | high | flatted | 同上 | GHSA-rf6f-7fwh-wjgh | parse() の Prototype Pollution |
| 242 | high | minimatch | 同上 | GHSA-7r86-cg39-jmmj | matchOne() ReDoS |
| 241 | high | minimatch | 同上 | GHSA-7r86-cg39-jmmj | 同上（別経路） |
| 238 | high | rollup | 同上 | GHSA-mw96-cpmx-2vgc | Arbitrary File Write via Path Traversal |

### 対応方針

#### バックエンド（Python / uv）

```bash
cd versions/v0.9.7/backend
uv lock --upgrade-package lxml
uv sync
uv run pytest tests/ -v
```

#### フロントエンド（npm）

```bash
cd versions/v0.9.7/frontend
npm audit fix
# または個別に
npm update vite picomatch yaml flatted minimatch rollup
npm test
```

### 判断フロー

各パッケージについて以下のフローで判断する:

1. **lockfile 更新だけで解決するか確認**（`uv lock --upgrade-package` / `npm update`）
2. **解決する場合**: lockfile 更新 → テスト実行 → 別 PR を作成して本 PR にマージ後対応
3. **メジャーバージョン更新が必要な場合**:
   - 既存テスト・動作確認に影響が及ぶため、**個別に issue を切って別途対応**
   - 例: vite v5 → v6 のように Breaking Changes を伴う更新

### 完了条件

- v0.9.7 配下のすべての Vulnerable アラートが「修正済み」または「個別 issue 化」されている
- 修正の場合: lockfile 更新 PR がマージされアラートが自動 close される
- issue 化の場合: 該当アラートは一時的に open のまま残る（issue 番号をコメントに記載）

---

## Step 4: Malware タブの確認

### 対象

Dependabot Alerts の Malware タブに表示されているアラート全件。

### 対応

- 発生場所（subtree / 旧バージョン / 最新版）を問わず、**すべて修正対応**
- 修正できないものは個別に issue を切る

### 確認コマンド

```bash
# 現状、Dependabot API には malware フィルタが直接ないため UI で確認
open https://github.com/elvezjp/spec-code-ai-reviewer/security/dependabot?q=is%3Aopen+is%3Amalware
```

---

## 完了後の検証

```bash
# 残存 open アラート数を確認
gh api repos/elvezjp/spec-code-ai-reviewer/dependabot/alerts --paginate \
  -q '.[] | select(.state=="open") | .number' | wc -l
```

期待値: **0 件**（または最新版の修正待ち issue 化分のみ）

## 作業記録

実行時に各ステップで dismissed したアラート数、修正した PR 番号、切った issue 番号を本セクションに追記する。

| Step | 実行日 | 件数 | 関連 PR / Issue | 備考 |
|---|---|---|---|---|
| Step 1（subtree dismiss） | 2026-04-27 | 19 / 19 | - | `dismissed_reason=not_used`。内訳: md2map 9件（root 7・versions 2）/ code2map 8件（root 2・versions 6）/ excel2md 2件。残存 open: 127 件 |
| Step 2（旧バージョン dismiss） | 2026-04-27 | 117 / 117 | - | `dismissed_reason=not_used`。内訳: frontend 107件（v0.7.0〜v0.9.6 各9件・v0.6.0 8件）/ backend 10件（v0.5.0〜v0.9.1 各1件、python-dotenv）。残存 open: 10 件（最新版 v0.9.7 のみ） |
| Step 3（最新版修正） | 2026-04-27 | 10 / 10 | - | 全件マイナー/パッチ更新で解決。backend: lxml 6.0.2→6.1.0（#264）。frontend (`npm audit fix`): vite 7.3.1→7.3.2（#250-252）/ rollup 4.57.1→4.60.2（#238）/ minimatch 9.0.5→9.0.9・3.1.2→3.1.5（#241,242）/ flatted 3.3.3→3.4.2（#244）/ picomatch 4.0.3→4.0.4（#247）/ yaml 1.10.2→1.10.3（#245）。postcss 8.5.12 にも副次更新（Dependabot 未通知）。テスト: backend 191件・frontend 212件すべて成功。メジャー更新不要のため個別 issue 化なし |
| Step 4（malware 修正） | 2026-04-27 | 0 / 0 | - | Malware タブの open アラートは 0 件のため対応不要 |

---

## 後追い対応: PR #98 マージ後の再スキャンによる新規アラート

### 経緯

PR #98 マージにより default branch が更新され、Dependabot がリポジトリ全体を再スキャン。直近で新規公開された CVE 群が一斉に検出され、open アラートが **0 件 → 151 件** に増加した。

### 新規検出アラートの内訳

| カテゴリ | 件数 | 対応 |
|---|---|---|
| git subtree 配下 | 36 | Dismiss（運用方針通り） |
| 旧バージョン（`versions/v0.5.0`〜`v0.9.6`） | 110 | Dismiss（運用方針通り） |
| 最新版（`versions/v0.9.7/`） | 5 | 修正対応（後述） |
| **合計** | **151** | |

### 後追い Dismiss（subtree + 旧バージョン）

| 区分 | 実行日 | 件数 | 備考 |
|---|---|---|---|
| subtree dismiss | 2026-04-27 | 36 / 36 | `dismissed_reason=not_used`。Step 1 と同じスクリプトを再実行 |
| 旧バージョン dismiss | 2026-04-27 | 110 / 110 | `dismissed_reason=not_used`。Step 2 と同じスクリプトを再実行 |

### v0.9.7 の新規 5 件（修正対応 TODO）

| # | 重要度 | パッケージ | manifest |
|---|---|---|---|
| 411 | low | Pygments | `versions/v0.9.7/backend/uv.lock` |
| 412 | medium | anthropic | 同上 |
| 413 | medium | anthropic | 同上 |
| 414 | medium | pytest | 同上 |
| 415 | medium | python-multipart | 同上 |

→ `uv lock --upgrade-package` で対応完了（2026-04-27）。

| 区分 | 件数 | 備考 |
|---|---|---|
| 最新版 backend 修正 | 5 / 5 | Pygments 2.19.2→2.20.0（#411）/ anthropic 0.86.0→0.97.0（#412,413）/ pytest 9.0.2→9.0.3（#414）/ python-multipart 0.0.22→0.0.26（#415）。テスト 191件すべて成功 |

※ anthropic は 0.86 → 0.97 と複数マイナー更新（0.x 系のため Breaking Changes の可能性ありだったがテストは全て成功）。

### 学び（運用上の知見）

- PR マージ直後の再スキャンで新規 CVE が一斉検出されることがある
- `auto_dismissed` 状態のアラート（GitHub が自動 close したもの）と、手動 `dismissed` は API 上で区別される
- 上部ナビ「Security and quality」のバッジ件数はキャッシュされており、再スキャン完了後も反映に数十分のラグがある
