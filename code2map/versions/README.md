# versions/

各バージョンのソースコードのスナップショットを保存するディレクトリ。

リファクタリングや大きな変更を行う前の状態を `v{バージョン番号}/` として保持し、過去のバージョンとの比較や参照を可能にする。

## 構成

```
versions/
├── v0.1.1/          # pyproject.toml の version = "0.1.1" 時点のスナップショット
│   ├── code2map/
│   ├── tests/
│   ├── examples/
│   ├── main.py
│   ├── pyproject.toml
│   ├── spec.md
│   └── uv.lock
└── README.md
```
