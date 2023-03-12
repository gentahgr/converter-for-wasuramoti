# 『わすらもち』用音声ファイル変換

## converter_for_wasuramoti.py
文英堂 『原色　小倉百人一首』の添付CDに格納された mp3 ファイルから、『わすらもち』で利用可能な形式に変換します。

>文英堂 『原色　小倉百人一首』[朗詠CD付]
https://www.bun-eido.co.jp/store/detail/24504/
ISBN:978-4-578-24504-9 

>わすらもち http://pjmtdw.github.io/wasuramoti/

### 必要なもの
- Python 3 (3.11 Windows 版 で動作確認済)
- ffmpeg (version 6.0で動作確認済)  https://ffmpeg.org/
- 書籍に添付のCD

### 使い方
Pythonはインストールしてパスを通してください
ffmpegはサイトから実行ファイルをダウンロードし、以下のいずれかの場所に置いてください
- `converter_for_wasuramoti.py` と同じディレクトリ
- パスの通った場所
それ以外の場所に置かれている場合は、 `--ffmpeg-path` オプションで指定してください。

```commandline
python3 converter_for_wasuramoti.py
```
オプション
* `--src DIR` mp3の置かれているディレクトリ (省略した場合、`カレントディレクトリ/source`)  
* `--dst DIR` 出力先ディレクトリ (省略した場合、`カレントディレクトリ/wasuramoti_reader/serino`)
* `--ffmpeg-path PATH` ffmpegの実行ファイルの置かれている場所

出力先ディレクトリが無い場合は自動的に作成されます。

コマンドの実行が正常に終了すると、出力ディレクトリに serino_000_1.ogg, serino_000_2.ogg, serino_001_1.ogg, ..., serino_100_2.ogg
のように、202個のoggファイルが作成されます。
作成されたディレクトリを『わすらもち』のインストールされたAndroidスマートフォンの
`wasuramoti_reader/serino` に転送してください。