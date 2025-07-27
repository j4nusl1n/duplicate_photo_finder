# 重複照片偵測工具 (Duplicate Photo Finder)

這個工具能夠幫助攝影師和圖片收藏家識別並處理重複的圖片檔案，支援多種檔案格式包括 Sony 相機的 RAW 檔案 (.ARW)。

## 功能特點

- **多維度比較**：同時考慮檔案雜湊值、解析度、檔案大小及相機型號
- **智慧選擇**：自動識別最佳品質的重複圖片
- **高效處理**：使用多線程並行處理，大幅提升大量圖片的處理速度
- **記憶體優化**：分塊讀取大型檔案，避免記憶體耗盡
- **原始格式支援**：支援 RAW 檔案 (.ARW) 及常見圖片格式 (.jpg, .png, .tiff 等)
- **強制 ExifTool 模式**：可強制使用 ExifTool 提取所有圖片類型的詮釋資料
- **靈活檔案管理**：可將重複檔案移動到指定目錄而非直接刪除
- **詳細統計**：提供已節省空間大小及重複檔案數量的精確統計
- **使用者友善**：支援逐組確認、自動選擇，及詳細的處理資訊

## 安裝需求

### 必要依賴

- Python 3.12+
- Pillow (PIL Fork)
- ExifTool (用於提取相機型號及 RAW 檔案解析度)

### 安裝步驟

1. 安裝 Python 依賴：

```bash
pip install pillow
```

2. 安裝 ExifTool：

macOS:
```bash
brew install exiftool
```

Ubuntu/Debian:
```bash
sudo apt-get install libimage-exiftool-perl
```

Windows:
- 下載 ExifTool 安裝包：https://exiftool.org/
- 將安裝路徑添加到系統環境變數

## 使用方法

### 基本使用

```bash
python duplicated_img_detect_improved.py /path/to/photos
```

### 列出重複檔案

```bash
python duplicated_img_detect_improved.py /path/to/photos --list_duplicates
```

### 移除重複檔案 (單一確認)

```bash
python duplicated_img_detect_improved.py /path/to/photos --remove_duplicates
```

### 移除重複檔案 (逐組確認)

```bash
python duplicated_img_detect_improved.py /path/to/photos --remove_duplicates --group_by_group
```

### 自動選擇最佳品質檔案並移除其餘檔案

```bash
python duplicated_img_detect_improved.py /path/to/photos --remove_duplicates --auto_select_best
```

### 強制使用 ExifTool 提取詮釋資料

```bash
python duplicated_img_detect_improved.py /path/to/photos --force_exiftool
```

### 將重複檔案移動到指定目錄而非刪除

```bash
python duplicated_img_detect_improved.py /path/to/photos --remove_duplicates --dest_dir /path/to/duplicate_archive
```

### 啟用詳細記錄

```bash
python duplicated_img_detect_improved.py /path/to/photos --verbose
```

## 命令列選項

| 選項 | 描述 |
|------|------|
| `directory` | 要搜尋的圖片目錄路徑（必要參數） |
| `--max_workers` | 最大工作線程數（預設為 CPU 核心數 x 4，上限 32） |
| `--list_duplicates` | 列出所有重複檔案 |
| `--remove_duplicates` | 確認後移除重複檔案 |
| `--auto_select_best` | 自動選擇最佳品質的檔案保留 |
| `--group_by_group` | 逐組確認重複檔案處理方式 |
| `--force_exiftool` | 強制對所有圖片類型使用 ExifTool 提取詮釋資料（需安裝 ExifTool） |
| `--dest_dir` | 指定目錄用於移動重複檔案而非刪除 |
| `--verbose` | 啟用詳細記錄 |

## 工作原理

1. **檔案識別**：工具會搜尋指定目錄及其子目錄中的所有支援格式圖片
2. **詮釋資料提取**：從每個檔案提取相機型號、解析度等詮釋資料
3. **檔案雜湊**：計算每個檔案的 SHA-256 雜湊值以判斷內容相同性
4. **重複分組**：根據雜湊值及詮釋資料將檔案分組
5. **智慧選擇**：依據解析度及檔案大小為每組重複檔案評分
6. **使用者確認**：根據設定讓使用者確認處理操作
7. **檔案處理**：移除或移動選定的重複檔案並提供統計資訊

## 支援的檔案格式

- Sony RAW 檔案 (.ARW)
- JPEG 檔案 (.jpg, .jpeg)
- PNG 檔案 (.png)
- TIFF 檔案 (.tiff, .tif)
- BMP 檔案 (.bmp)
- GIF 檔案 (.gif)

## 安全注意事項

- 在處理大量檔案前，建議先備份重要資料
- 使用 `--list_duplicates` 選項預覽重複檔案，確認識別準確性
- 使用 `--group_by_group` 選項逐組確認以提高安全性
- 考慮使用 `--dest_dir` 選項移動重複檔案到歸檔目錄，而非直接刪除

## 日誌記錄

腳本產生的日誌檔案 `duplicate_detection.log` 包含所有處理資訊，有助於診斷潛在問題。

## 授權

MIT 授權

## 貢獻

歡迎提交問題報告、功能請求或改進建議！
