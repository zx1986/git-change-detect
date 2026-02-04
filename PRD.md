# Product Requirements Document (PRD): Git Change Detect

**專案名稱:** Git Change Detect
**版本:** 1.0.0
**語言:** Python
**目標用戶:** DevOps 工程師、CI/CD 流程自動化

## 1. 專案概述 (Project Overview)

**Git Change Detect** 是一個基於 Python 的自動化命令列工具 (CLI)，旨在解決 CI/CD 流程中（特別是 Pull Request 合併至 Master/Main 分支時）無法精確感知「檔案內容變動細節」的問題。

本工具將掃描 Git 提交中的差異，根據預定義的正規表達式 (Regex) 過濾特定的目錄或檔案（如 `.yaml`），解析其 YAML 結構，並輸出結構化的變動報告。此報告將用於觸發後續的自動化部署或驗證邏輯。

## 2. 使用場景 (Use Cases)

* **場景 A (CI/CD 觸發):** 當開發人員提交 PR 並合併至主分支時，CI 流水線 (GitLab CI 或 Azure DevOps) 觸發此工具。
* **場景 B (變更分析):** 工具偵測到 `k8s-manifests/` 目錄下的 YAML 檔案發生變動，解析出具體的 Image Tag 或 Configuration 變數修改。
* **場景 C (後續自動化):** 下游腳本讀取此工具輸出的 YAML 報告，根據變動的 Key-Value 執行對應的 API 呼叫或部署指令。

## 3. 功能需求 (Functional Requirements)

### 3.1 輸入參數與設定

工具必須支援透過 Command Line Arguments 接收以下輸入：

1. **Git Revision Range:** 指定要比較的 Commit Hash 範圍 (例如: `HEAD~1..HEAD` 或 `origin/main...feature-branch`)，預設直接針對 Pull Request 合併時所有發生變化的檔案進行過濾。
2. **過濾規則 (Filter Patterns):**
* 支援以 **正規表達式 (Regex)** 定義目標監控的「目錄路徑」與「檔案名稱」。
* 範例: `^deploy/.*\.yaml$` (監控 deploy 目錄下所有 yaml 檔)。


3. **工作目錄:** 指定 Git Repository 的根目錄。

### 3.2 核心偵測邏輯

1. **Git Diff 掃描:**
* 識別指定 Commit 區間內，或預設直接針對 Pull Request (Merge Request) 合併時所有發生變化的檔案。
* 變更類型包含: `ADDED` (新增), `MODIFIED` (修改), `DELETED` (刪除)。


2. **路徑過濾:**
* 針對 Diff 列表，應用使用者輸入的 Regex 進行過濾。僅處理符合 Pattern 的檔案。


3. **內容解析 (YAML):**
* 工具必須能讀取「變更前」與「變更後」的檔案內容。
* **完整解析:** 無論變更幅度大小，需解析完整的 YAML 結構以確保上下文正確。
* **結構化比對:** 比較前後版本的 YAML Object (Dict/List)，識別具體的 Key 變動。



### 3.3 變更類型定義

針對每一個檔案的變動，需歸類為以下三種操作之一，並依據規則處理：

* **ADD (新增檔案):**
* 提取檔案內所有 Key-Value。


* **DELETE (刪除檔案):**
* 僅記錄檔案路徑與刪除狀態，**不需要**詳細列出被刪除的內容值。


* **UPDATE (修改檔案):**
* 比對 YAML 節點。
* 若為 **新增 Key** (Key Added): 記錄 Key 路徑與 Value。
* 若為 **修改 Value** (Value Edited): 記錄 Key 路徑與 **新** Value。
* 若為 **刪除 Key** (Key Deleted): 僅記錄 Key 路徑，忽略 Value。



### 3.4 輸出規範 (Output Specification)

* **格式:** YAML
* **輸出流:** Standard Output (stdout)，以便被 Pipeline 中的其他工具 (如 `yq` 或 Python script) 擷取。
* **結構定義:**

```yaml
# 輸出結構範例
detected_changes:
  - file_path: "deployments/service-a/values.yaml"  # 變動檔案的完整路徑
    change_type: "UPDATE"                           # 變動類型: ADD, UPDATE, DELETE
    diffs:                                          # 內容細節 (DELETE 類型可為空或省略)
      - action: "EDIT"                              # 該欄位的變動: ADD, EDIT, DELETE
        key_path: "image.tag"                       # 變動的 YAML 欄位路徑
        value: "v1.2.0"                             # 變更後的值 (若是 DELETE 則此欄位可選)
      - action: "ADD"
        key_path: "resources.limits.memory"
        value: "512Mi"

```

## 4. 非功能性需求 (Non-Functional Requirements)

### 4.1 技術堆疊

* **語言:** Python 3.9+
* **依賴庫建議:**
* `GitPython` 或 `PyDriller`: 用於 Git 操作與 Diff 提取。
* `ruamel.yaml`: 用於 YAML 解析 (需保留數據類型)。
* `click`: 用於 CLI 介面實作。



### 4.2 效能與並發 (Performance & Concurrency)

* **並行處理:** 當單次 Commit 涉及大量檔案變動時，必須支援並行處理 (Parallel Processing)。
* **機制:** 建議使用 Python 的 `multiprocessing` 或 `concurrent.futures` 針對每個檔案的 Diff 解析進行平行化運算，以縮短 CI/CD 執行時間。

### 4.3 錯誤處理與日誌 (Error Handling & Logging)

* **日誌 (Logging):** 所有執行過程資訊、錯誤訊息均輸出至 Standard Output (stdout) 或 Standard Error (stderr)。
* **容錯:** 若單一檔案解析失敗 (例如 YAML 語法錯誤)，應記錄錯誤並繼續處理其他檔案，最後以非零 Exit Code 退出以通知 CI 失敗。

## 5. CI/CD 整合指南 (Integration Guide)

### 5.1 GitLab CI 範例

```yaml
git_detect:
  stage: build
  script:
    - pip install -r requirements.txt
    # 比較當前分支與目標分支的差異
    - python main.py --base-ref origin/main --head-ref $CI_COMMIT_SHA --pattern "^k8s/.*\.yaml$" > changes.yaml
    - cat changes.yaml
  artifacts:
    paths:
      - changes.yaml

```

### 5.2 Azure DevOps (ADO) 範例

```yaml
steps:
- script: |
    pip install -r requirements.txt
    # ADO 通常需要明確 fetch depth
    git fetch origin main
    python main.py --base-ref origin/main --head-ref HEAD --pattern ".*\.yaml$"
  displayName: 'Run Git Change Detect'

```

## 6. 實作提示 (Implementation Notes for AI Agent)

1. **YAML 遞迴比較:** 實作一個遞迴函數 `deep_diff(old_dict, new_dict)`，回傳差異列表。需處理 Nested Dictionary 和 List 的情況。
2. **路徑表示法:** `key_path` 建議使用點符號 (dot notation) 表示層級，例如 `spec.containers[0].image`。
3. **Git Show:** 使用 `git show <commit_hash>:<file_path>` 來獲取檔案在特定版本的內容字串，不要依賴本地檔案系統的當前狀態 (因為要比對的是歷史版本)。
4. 使用 uv 進行 python 運行環境的管理。
