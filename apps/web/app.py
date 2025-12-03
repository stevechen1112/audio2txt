import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import time
from pathlib import Path

import os

# 配置 API 地址 (假設 API 伺服器運行在本地)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# 認證憑證 (從環境變數讀取，預設為 admin/password123)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password123")
AUTH = HTTPBasicAuth(ADMIN_USERNAME, ADMIN_PASSWORD)

def fetch_artifacts(task_id: str) -> dict:
    try:
        res = requests.get(f"{API_BASE_URL}/transcription/tasks/{task_id}/artifacts", auth=AUTH, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def download_artifact(task_id: str, kind: str) -> bytes | None:
    try:
        res = requests.get(
            f"{API_BASE_URL}/transcription/tasks/{task_id}/download/{kind}",
            auth=AUTH,
            timeout=15,
        )
        if res.status_code == 200:
            return res.content
    except Exception:
        return None
    return None

st.set_page_config(
    page_title="Audio2txt Enterprise",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定義 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .success { background-color: #D4EDDA; color: #155724; }
    .info { background-color: #D1ECF1; color: #0C5460; }
    .warning { background-color: #FFF3CD; color: #856404; }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<div class="main-header">🎙️ Audio2txt Enterprise</div>', unsafe_allow_html=True)

    # 側邊欄：設定與狀態
    with st.sidebar:
        st.header("⚙️ 設定")
        
        # 檢查 API 連線
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=2, auth=AUTH)
            if response.status_code == 200:
                st.success("🟢 伺服器連線正常")
            else:
                st.error("🔴 伺服器異常")
        except:
            st.error("🔴 無法連線至伺服器")
            st.info("請確認 run_server.py 是否已啟動")
            return

        st.markdown("---")
        st.subheader("📝 報告模板")
        template_options = {
            "universal_summary": "通用型摘要",
            "legal_consultation": "⚖️ 法律諮詢記錄",
            "client_interview": "💼 客戶需求訪談",
            "executive_meeting": "👔 高層決策會議",
            "concise_minutes": "⚡ 精簡逐字稿",
        }
        selected_template = st.selectbox(
            "選擇場景模板",
            options=list(template_options.keys()),
            format_func=lambda x: template_options[x]
        )
        
        st.markdown("---")
        st.markdown("### 關於系統")
        st.info(
            "Audio2txt v4.0 Enterprise\n\n"
            "專為專業服務業打造的私有化 AI 會議系統。\n"
            "資料全程在內網處理，確保絕對隱私。"
        )

    tab1, tab2, tab3 = st.tabs(["🎙️ 錄音與上傳", "📂 歷史記錄", "📖 詞彙表"])

    with tab1:
        # ... (Existing Tab 1 content) ...
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("1. 錄製或上傳音訊")
            
            # 錄音功能 (使用 st.audio_input，Streamlit 1.40+ 原生支援)
            # 若版本較舊可 fallback 到上傳
            audio_value = st.audio_input("點擊麥克風開始錄音")
            
            uploaded_file = st.file_uploader("或上傳現有錄音檔 (WAV, M4A, MP3)", type=["wav", "m4a", "mp3"])

        with col2:
            st.subheader("2. 處理狀態")
            
            file_to_process = audio_value if audio_value else uploaded_file
            
            if file_to_process:
                st.audio(file_to_process, format="audio/wav")
                
                if st.button("🚀 開始處理", type="primary", use_container_width=True):
                    with st.spinner("正在上傳檔案..."):
                        # 1. 上傳檔案
                        files = {"file": (file_to_process.name, file_to_process, file_to_process.type)}
                        try:
                            upload_res = requests.post(f"{API_BASE_URL}/transcription/upload", files=files, auth=AUTH)
                            upload_data = upload_res.json()
                            
                            if upload_res.status_code != 200:
                                st.error(f"上傳失敗: {upload_data}")
                                return
                                
                            file_path = upload_data["file_path"]
                            st.success("✅ 上傳成功！")
                            
                            # 2. 啟動處理任務
                            process_payload = {
                                "file_path": file_path,
                                "template_id": selected_template
                            }
                            process_res = requests.post(f"{API_BASE_URL}/transcription/process", json=process_payload, auth=AUTH)
                            process_data = process_res.json()
                            
                            task_id = process_data["task_id"]
                            st.info(f"📋 任務已建立 (ID: {task_id})")
                            
                            # 3. 輪詢進度
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            result_area = st.empty()
                            
                            while True:
                                task_res = requests.get(f"{API_BASE_URL}/transcription/tasks/{task_id}", auth=AUTH)
                                task_data = task_res.json()
                                
                                status = task_data["status"]
                                progress = task_data.get("progress", 0)
                                
                                progress_bar.progress(progress)
                                status_text.text(f"狀態: {status} ({progress}%)")
                                
                                if status == "completed":
                                    st.success("🎉 處理完成！")
                                    
                                    result = task_data.get("result", {}) or {}
                                    highlights = result.get("highlights") or []
                                    artifacts = fetch_artifacts(task_id)
                                    
                                    if highlights:
                                        st.markdown("### 🔍 精華重點")
                                        for item in highlights:
                                            st.write(f"- {item['start']} ~ {item['end']} **{item['speaker']}**：{item['text']}")
                                    
                                    st.markdown("### 📄 摘要報告內容")
                                    if artifacts.get("report_markdown"):
                                        st.markdown(artifacts["report_markdown"])
                                        st.download_button(
                                            "下載 Markdown 報告",
                                            data=artifacts["report_markdown"].encode("utf-8"),
                                            file_name=f"{task_id}.md",
                                            mime="text/markdown",
                                            use_container_width=True,
                                        )
                                    else:
                                        st.warning("暫無報告內容")
                                    
                                    st.markdown("### 📝 逐字稿預覽")
                                    transcript_text = artifacts.get("transcript_text", result.get("summary", ""))
                                    st.text_area("Transcript", value=transcript_text, height=240)
                                    st.download_button(
                                        "下載逐字稿 (.txt)",
                                        data=transcript_text.encode("utf-8"),
                                        file_name=f"{task_id}.txt",
                                        mime="text/plain",
                                        use_container_width=True,
                                    )
                                    
                                    pdf_bytes = download_artifact(task_id, "report-pdf")
                                    if pdf_bytes:
                                        st.download_button(
                                            "下載 PDF 報告",
                                            data=pdf_bytes,
                                            file_name=f"{task_id}.pdf",
                                            mime="application/pdf",
                                            use_container_width=True,
                                        )
                                    
                                    break
                                    
                                elif status == "failed":
                                    st.error(f"❌ 處理失敗: {task_data.get('error')}")
                                    break
                                
                                time.sleep(2)
                                
                        except Exception as e:
                            st.error(f"發生錯誤: {e}")

    with tab2:
        # ... (Existing Tab 2 content) ...
        st.subheader("📂 歷史記錄")
        
        if st.button("🔄 重新整理"):
            st.rerun()
            
        try:
            history_res = requests.get(f"{API_BASE_URL}/transcription/history", auth=AUTH)
            if history_res.status_code == 200:
                tasks = history_res.json()
                
                if not tasks:
                    st.info("尚無歷史記錄")
                else:
                    for task in tasks:
                        with st.expander(f"{task['created_at']} - {task['template_id']} ({task['status']})"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**ID:** `{task['id']}`")
                                st.write(f"**檔案:** `{task['file_path']}`")
                            with col2:
                                st.write(f"**狀態:** {task['status']}")
                                st.write(f"**進度:** {task['progress']}%")
                            
                            if task.get("result"):
                                st.markdown("---")
                                st.markdown("### 📄 摘要報告")
                                st.markdown(task["result"].get("summary", "無摘要"))
                                
                                highlights = task["result"].get("highlights") or []
                                if highlights:
                                    st.markdown("#### 🔍 精華重點")
                                    for item in highlights:
                                        st.write(f"- {item['start']} ~ {item['end']} **{item['speaker']}**：{item['text']}")
                                
                                st.markdown("### 📝 逐字稿路徑")
                                st.code(task["result"].get("transcript_path", ""))
                                
                            if task.get("error_message"):
                                st.error(f"錯誤: {task['error_message']}")
            else:
                st.error("無法取得歷史記錄")
        except Exception as e:
            st.error(f"連線錯誤: {e}")

    with tab3:
        st.subheader("📖 專有名詞管理")
        st.info("在此新增專有名詞（如人名、公司名、術語），可提高辨識準確率。")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            new_word = st.text_input("新增詞彙", placeholder="例如：台積電、無罪推定")
        with col2:
            st.write("") # Spacer
            st.write("") # Spacer
            if st.button("➕ 新增", use_container_width=True):
                if new_word:
                    try:
                        res = requests.post(f"{API_BASE_URL}/vocabulary/", json={"word": new_word}, auth=AUTH)
                        if res.status_code == 200:
                            st.success(f"已新增：{new_word}")
                            st.rerun()
                        else:
                            st.error("新增失敗（可能已存在）")
                    except Exception as e:
                        st.error(f"錯誤: {e}")

        st.markdown("---")
        st.markdown("### 目前詞彙表")
        
        try:
            vocab_res = requests.get(f"{API_BASE_URL}/vocabulary/", auth=AUTH)
            if vocab_res.status_code == 200:
                words = vocab_res.json()
                if not words:
                    st.write("目前沒有自訂詞彙。")
                else:
                    # Display as tags
                    for i in range(0, len(words), 4):
                        cols = st.columns(4)
                        for j in range(4):
                            if i + j < len(words):
                                word = words[i+j]
                                with cols[j]:
                                    if st.button(f"🗑️ {word}", key=f"del_{word}"):
                                        requests.delete(f"{API_BASE_URL}/vocabulary/{word}", auth=AUTH)
                                        st.rerun()
            else:
                st.error("無法讀取詞彙表")
        except Exception as e:
            st.error(f"連線錯誤: {e}")

if __name__ == "__main__":
    main()
