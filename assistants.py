import streamlit as st
import os
import yaml
from core.processing import Processor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="AI 輔助工具集",
    page_icon="🛠️",
    layout="wide"
)

# --- 核心視覺重構 (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #1A202C; color: #E2E8F0; }
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    h1 { padding-top: 0 !important; font-weight: 800 !important; }
    [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #FFFFFF1A; }
    .stMarkdown, .stButton, .stMetric, [data-testid="stVerticalBlock"] > div { text-align: left !important; align-items: flex-start !important; }
    .assistant-box { background: #2D3748; padding: 1.5rem; border-radius: 12px; border: 1px solid #FFFFFF1A; margin-bottom: 1rem; }
    </style>
    """, unsafe_allow_html=True)

def load_config():
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Initialize Logic
config = load_config()
processor = Processor(config['keywords'], config['llm'])

st.sidebar.title("🛠️ 輔助工具集")
app_mode = st.sidebar.radio("切換功能", ["測試助理", "翻譯助理"])

if app_mode == "測試助理":
    st.title("🧪 AI 測試助理")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        user_req = st.text_area("需求描述：", height=300, placeholder="請輸入您想測試的功能描述或需求文件內容...")
        if st.button("🚀 啟動測試分析", use_container_width=True):
            if user_req.strip():
                with st.spinner("正在生成測試案例與分析..."):
                    system_prompt = "你是一位資深的軟體測試工程師 (QA)，專精於編寫高品質的測試案例 (Test Cases) 與需求分析。"
                    user_prompt = f"請針對以下需求描述，生成完整的測試案例、邊界條件測試以及潛在風險分析：\n\n{user_req}"
                    result = processor.generate_response(user_prompt, system_prompt)
                    st.session_state['test_result'] = result
            else:
                st.warning("請先輸入需求描述。")

    with col2:
        st.subheader("📊 分析結果")
        if 'test_result' in st.session_state:
            st.markdown(f"<div class='assistant-box'>{st.session_state['test_result']}</div>", unsafe_allow_html=True)
        else:
            st.info("分析結果將顯示在此處。")

elif app_mode == "翻譯助理":
    st.title("🔤 AI 翻譯官")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        source_lang = st.selectbox("來源語言", ["自動偵測", "繁體中文", "英文", "日文", "韓文"])
        target_lang = st.selectbox("目標語言", ["繁體中文", "英文", "日文", "韓文"], index=1)
        user_input = st.text_area("原文內容：", height=300, placeholder="請輸入要翻譯的文字...")
        
        if st.button("🎨 執行專業翻譯", use_container_width=True):
            if user_input.strip():
                with st.spinner("正在進行高品質翻譯..."):
                    system_prompt = "你是一位精通多國語言的專業翻譯官，擅長優雅且準確的翻譯，並能根據語境調整語氣。"
                    user_prompt = f"請將以下內容從 {source_lang} 翻譯成 {target_lang}，並提供 2-3 種不同的語氣版本（如：專業、口語、簡潔）：\n\n{user_input}"
                    result = processor.generate_response(user_prompt, system_prompt)
                    st.session_state['trans_result'] = result
            else:
                st.warning("請先輸入原文內容。")

    with col2:
        st.subheader("📝 翻譯結果")
        if 'trans_result' in st.session_state:
            st.markdown(f"<div class='assistant-box'>{st.session_state['trans_result']}</div>", unsafe_allow_html=True)
        else:
            st.info("翻譯結果將顯示在此處。")

st.markdown("<br><p style='text-align:center; color:#4A5568; font-size:0.7rem;'>Powered by Gemini 2.5 Flash / GPT-4o</p>", unsafe_allow_html=True)
