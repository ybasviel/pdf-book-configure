# 自炊pdf 目次作成プログラム

## 概要

自炊本のpdfに著者名、タイトル、目次を設定するプログラムです。
情報の抽出はgeminiに頼っているため、ハルシネーションが起きたときはinfo.yamlを手で修正する必要があります。
2025-06-14現在、無償で利用できるgemini-2.0-flashを利用しています。



## セットアップ

### 依存パッケージのインストール
```bash
pip install -r requirements.txt
```

uvなら
```bash
uv sync
```


### 環境変数

```bash
export GEMINI_API_KEY=xxxxxx
```

## 使い方

1. まず、info.yaml を作成する
例: 
ファイル名: 自炊本.pdf 
目次が7ページから12ページまでの範囲
奥付が216ページ
PDFのページ番号が書籍のページ番号より12進んでいる


```bash
python extract.py -i "自炊本.pdf" --toc-page-start 7 --toc-page-end 12 --author-page 216 --toc-page-diff 12
```

2. info.yamlを覗いてみて、おかしなところがないか確認、修正する。
3. その後、apply.py を実行する

```bash
python apply.py
```

## 注意

大部分をvibe codingしてる上にテストもしてないので動かないかもしれません。とくにsectionのネストが深くなったときにおかしなことになるかも。
また、本によっては本章と別にローマ数字のページと目次が設置されていたりとカオスなので、適宜yamlファイルを自分で修正するしかないと思います。






