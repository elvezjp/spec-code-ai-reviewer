# Assets

このディレクトリでは、READMEやドキュメントに使用するメディアファイル（動画・画像など）を管理します。

## ファイル一覧

| ファイル | 説明 |
|----------|------|
| demo.mp4 | アプリケーションのデモ動画 |

## READMEへの埋め込み方法

GitHubのREADMEでは `<video>` タグがサポートされていないため、動画を埋め込む際は **GitHub Uploads** を使用してURLを生成する必要があります。

### 手順

1. GitHubでIssueまたはPull Requestを開く
2. コメント欄に動画ファイルをドラッグ&ドロップ
3. 生成されたURL（`https://github.com/user-attachments/assets/...`）をコピー
4. READMEにURLを貼り付け

### 例

```markdown
https://github.com/user-attachments/assets/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

GitHubのMarkdownレンダラーがこのURLを自動的に動画プレイヤーとして表示します。

## 動画ファイルの更新

動画を更新する場合：

1. このディレクトリの動画ファイルを差し替え
2. 上記の手順でGitHub Uploadsに再アップロード
3. READMEのURLを新しいものに更新
