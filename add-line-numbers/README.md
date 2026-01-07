# add-line-numbers

テキストファイルに「4桁右揃えの行番号」を自動で付けるPythonスクリプトです。コードレビューやAI解析で「〇行目を見て」と指し示しやすくなります。外部ライブラリ不要で、Python 3.8+ だけあれば動きます。

## まずはクイックスタート

1. リポジトリを取得して移動する
   ```bash
   git clone https://github.com/elvezjp/add-line-numbers.git
   cd add-line-numbers
   ```
2. そのまま実行（`inputs/` → `outputs/`）
   ```bash
   python add_line_numbers.py
   ```
3. 結果を確認  
   - 変換後のファイルが `outputs/` に生成されます  
   - `outputs/README.md` が自動で作られ、構造と使い方がまとまります

## もう少し詳しく（初心者向け）

- 何をするツール？
  - テキストファイルの各行頭に行番号（例: `   1: `）を付けます
  - 入力ディレクトリの構造を保ったまま出力にコピーします
  - 出力先に説明用 README を自動生成します

- 対応するファイル
  - UTF-8のテキストファイル全般（.py, .java, .js, .json, .xml, .md, .txt など）
  - 画像などのバイナリやUTF-8で読めないファイルは自動スキップします

- 必要なもの
  - Python 3.8以上
  - 追加のpipインストールは不要です

## 使い方

### デフォルト（何も指定しない）
```bash
python add_line_numbers.py
# inputs/ を読み、outputs/ に書き出します
```

### 入出力を自分で指定する
```bash
python add_line_numbers.py <入力ディレクトリ> <出力ディレクトリ>
```
例:
```bash
python add_line_numbers.py my_project numbered_output
```

### 実行時の出力イメージ
```
処理中: 64 個のファイル
入力: inputs
出力: outputs
------------------------------------------------------------
✓ src/main.py
✓ config/settings.json
✓ docs/README.md
------------------------------------------------------------
完了: 64 個のファイルを処理しました
✓ README.md を生成しました: outputs/README.md
```

## 行番号はこう付きます

- フォーマット: `   1: `（行番号は4桁右揃え＋コロン＋スペース）

変換前:
```python
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
```

変換後:
```
   1: def hello():
   2:     print("Hello, World!")
   3:
   4: if __name__ == "__main__":
   5:     hello()
```

## つまずきポイントとヒント

- 入力ディレクトリが存在しないとエラー終了します。パスを確認してください。
- 非UTF-8やバイナリはスキップされます。必要なら事前にUTF-8へ変換してください。
- 大量ファイルでは少し時間がかかります。出力ログで進捗を確認できます。

## テストしたいとき
```bash
pip install pytest   # 未インストールなら
pytest test.py -v
```

## ファイル構成
```
add-line-numbers/
├── add_line_numbers.py   # メインスクリプト
├── test.py               # ユニットテスト
├── spec.md               # 詳細仕様書
├── LICENSE               # MITライセンス
└── README.md             # このファイル
```
### 開発の背景
本ツールは、日本語の開発文書・仕様書を対象とした開発支援AI **IXV（イクシブ）** の開発過程で生まれた小さな実用品です。

IXVでは、システム開発における日本語の文書について、理解・構造化・活用という課題に取り組んでおり、本リポジトリでは、その一部を切り出して公開しています。

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照してください。

## 問い合わせ先

- **メールアドレス**: info@elvez.co.jp
- **宛先**: 株式会社エルブズ

