import streamlit as st
import os
import yaml
import json
from core.processing import Processor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="輔助工具集",
    page_icon="🛠️",
    layout="wide"
)

# --- 現代感 CSS 重構 ---
st.markdown("""
    <style>
    /* 整體背景與文字顏色 */
    .stApp { background-color: #F8FAFC; color: #1E293B; }
    
    /* 隱藏預設元件 */
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 容器邊距 */
    .block-container { padding-top: 2rem !important; max-width: 1100px !important; }
    
    /* 側邊欄：確保標籤與說明文字對比足夠（避免淺灰難以辨識） */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
        color: #0F172A !important;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #0F172A !important;
    }
    [data-testid="stSidebar"] [data-baseweb="radio"] label,
    [data-testid="stSidebar"] .stRadio label {
        color: #0F172A !important;
    }
    [data-testid="stSidebar"] .stRadio > div { gap: 10px; }
    
    /* 標題置中與樣式 */
    .main-title { 
        text-align: center; 
        font-weight: 800; 
        color: #0F172A; 
        margin-bottom: 2rem;
        font-size: 2.5rem;
    }
    
    /* 按鈕樣式：強制藍色 */
    div.stButton > button:first-child {
        background-color: #2563EB;
        color: white;
        border: none;
        transition: all 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #1D4ED8;
        color: white;
        border: none;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }

    /* 內容容器：強制換行與自定義樣式 */
    .content-box {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 20px;
        white-space: pre-wrap;
        word-wrap: break-word;
        font-family: sans-serif;
        border: 1px solid #E2E8F0;
        color: #1E293B;
        line-height: 1.6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    
    /* Expander：標題列與內容區對比（避免深底配深字） */
    [data-testid="stExpander"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        margin-bottom: 1rem !important;
        background: #FFFFFF !important;
    }
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] details > summary {
        background-color: #E2E8F0 !important;
        color: #0F172A !important;
    }
    [data-testid="stExpander"] summary * ,
    [data-testid="stExpander"] details > summary * {
        color: #0F172A !important;
    }
    /* Streamlit 常用 class（與 summary 並用，涵蓋不同版本） */
    .streamlit-expanderHeader {
        background-color: #E2E8F0 !important;
        color: #0F172A !important;
    }
    .streamlit-expanderHeader p,
    .streamlit-expanderHeader span {
        color: #0F172A !important;
    }

    /* 說明小字：略深於預設 caption 灰，仍符合 WCAG 與白底對比 */
    [data-testid="stCaption"] {
        color: #475569 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def load_config():
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Initialize Logic
config = load_config()
processor = Processor(config['keywords'], config['llm'])

# 側邊欄導覽
st.sidebar.markdown("<h2 style='font-size: 1.2rem; margin-bottom: 1.5rem;'>🛠️ 輔助工具集</h2>", unsafe_allow_html=True)
app_mode = st.sidebar.radio("切換功能", ["翻譯助理", "測試助理"])

if app_mode == "翻譯助理":
    st.markdown("<h1 class='main-title'>abc 翻譯助理</h1>", unsafe_allow_html=True)
    
    col_in, col_out = st.columns([1, 1], gap="large")
    
    with col_in:
        lang_col1, lang_col2 = st.columns(2)
        with lang_col1:
            source_lang = st.selectbox("來源語言", ["自動偵測", "繁體中文", "英文", "日文", "韓文"])
        with lang_col2:
            target_lang = st.selectbox("目標語言", ["繁體中文", "英文", "日文", "韓文"], index=1)
            
        user_input = st.text_area("原文內容：", height=320, placeholder="請輸入要翻譯的文字...")
        
        if st.button("🎨 執行專業翻譯", use_container_width=True):
            if user_input.strip():
                with st.spinner("正在進行高品質翻譯..."):
                    system_prompt = """你是一位精通多國語言的專業翻譯官。請提供三種語氣翻譯。
輸出格式必須嚴格遵守 JSON 陣列：
[
  {"name": "專業 (Professional)", "content": "翻譯結果", "desc": "適用於技術報告或商務書信"},
  {"name": "口語 (Conversational)", "content": "翻譯結果", "desc": "適合日常對話或社群互動"},
  {"name": "簡潔 (Concise)", "content": "翻譯結果", "desc": "適合簡短筆記或系統提示"}
]"""
                    user_prompt = f"請將以下內容從 {source_lang} 翻譯成 {target_lang}：\n\n{user_input}"
                    result = processor.generate_response(user_prompt, system_prompt)
                    st.session_state['trans_result'] = result
            else:
                st.warning("請先輸入原文內容。")

    with col_out:
        st.subheader("📝 翻譯結果")
        if 'trans_result' in st.session_state:
            raw_res = st.session_state['trans_result']
            try:
                clean_res = raw_res.strip().replace('```json', '').replace('```', '').strip()
                results = json.loads(clean_res)
                for style in results:
                    with st.expander(f"✨ {style['name']}", expanded=True):
                        st.markdown(f'<div class="content-box" style="background-color:#F1F5F9;">{style["content"]}</div>', unsafe_allow_html=True)
                        st.caption(f"💡 {style['desc']}")
                st.success("翻譯已優化完成！")
            except:
                st.error("解析錯誤。")
                st.text(raw_res)
        else:
            st.info("翻譯結果將顯示在此處。")

elif app_mode == "測試助理":
    st.markdown("<h1 class='main-title'>🧪 測試助理</h1>", unsafe_allow_html=True)
    
    # --- 上方輸入區 ---
    with st.container():
        st.markdown("### 📥 需求輸入與文件上傳")
        user_req = st.text_area("需求描述：", height=200, placeholder="請輸入您想測試的功能描述或需求文件內容...")
        uploaded_file = st.file_uploader("上傳參考文件 (PDF, TXT, DOCX)", type=["pdf", "txt", "docx"])
        
        if uploaded_file:
            st.info(f"已選取文件：{uploaded_file.name}")
            
        if st.button("🚀 啟動測試分析", use_container_width=True):
            if user_req.strip():
                with st.spinner("正在生成測試策略與案例..."):
                    # 測試助理專用結構化 Prompt
                    system_prompt = """你是一位資深的軟體測試工程師 (QA)。請針對需求生成測試分析。
輸出格式必須嚴格遵守以下 JSON 格式：
{
  "strategy": "測試策略概述內容...",
  "test_cases": [
    {"title": "案例名稱", "steps": "測試步驟...", "expected": "預期結果..."},
    {"title": "案例名稱", "steps": "測試步驟...", "expected": "預期結果..."}
  ],
  "risks": "潛在風險分析與建議..."
}"""
                    file_info = f"\n(參考文件: {uploaded_file.name})" if uploaded_file else ""
                    user_prompt = f"需求內容：\n{user_req}{file_info}"
                    result = processor.generate_response(user_prompt, system_prompt)
                    st.session_state['test_analysis'] = result
            else:
                st.warning("請先輸入需求描述。")

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # --- 下方結果區 ---
    res_col1, res_col2 = st.columns([3, 1])
    with res_col1:
        st.markdown("### 📊 分析結果")
    with res_col2:
        if 'test_analysis' in st.session_state:
            if st.button("🌐 翻譯成英文", use_container_width=True):
                with st.spinner("正在翻譯成英文..."):
                    translate_prompt = f"""請將以下 JSON 內容中的所有「值 (values)」翻譯成英文，但必須「嚴格保留」原始的 JSON 鍵值 (keys) 與結構。
回傳格式必須僅包含翻譯後的 JSON：
{st.session_state['test_analysis']}"""
                    eng_result = processor.generate_response(translate_prompt, "你是一位專業的技術翻譯，擅長將軟體測試文件精準翻譯成英文。")
                    st.session_state['test_analysis'] = eng_result
                    st.rerun()

    if 'test_analysis' in st.session_state:
        raw_res = st.session_state['test_analysis']
        try:
            clean_res = raw_res.strip().replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_res)
            
            # 1. 策略概述
            with st.expander("🛠️ 測試策略概述", expanded=True):
                st.markdown(f'<div class="content-box">{data["strategy"]}</div>', unsafe_allow_html=True)
            
            # 2. 測試案例
            with st.expander("📝 詳細測試案例 (Test Cases)", expanded=True):
                for idx, tc in enumerate(data["test_cases"]):
                    st.markdown(f"**Case {idx+1}: {tc['title']}**")
                    st.markdown(f"""<div class="content-box" style="background-color:#F1F5F9; font-size:0.9rem;">
**步驟：**\n{tc['steps']}\n\n**預期結果：**\n{tc['expected']}
</div>""", unsafe_allow_html=True)
            
            # 3. 風險分析
            with st.expander("⚠️ 潛在風險分析", expanded=True):
                st.markdown(f'<div class="content-box" style="border-left: 5px solid #F59E0B;">{data["risks"]}</div>', unsafe_allow_html=True)
                
            st.success("測試分析生成完畢！")
        except Exception as e:
            st.error("解析結果時發生錯誤，請重試。")
            st.text_area("原始內容：", raw_res, height=200)
    else:
        st.info("點擊按鈕後，分析結果將顯示在此處。")

st.markdown("<br><hr><p style='text-align:center; color:#94A3B8; font-size:0.8rem;'>Powered by Gemini 2.5 Flash / GPT-4o</p>", unsafe_allow_html=True)
