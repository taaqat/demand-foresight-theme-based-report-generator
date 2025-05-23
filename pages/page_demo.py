import streamlit as st
from managers.data_manager import DataManager

st.markdown("""<style>
    div.stButton > button {
        width: 100%;  /* 設置按鈕寬度為頁面寬度的 50% */
        height: 50px;
        margin-left: 0;
        margin-right: auto;
    }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    icon_box, text_box = st.columns((0.2, 0.8))
    with icon_box:
        st.markdown(f'''
                        <img class="image" src="data:image/jpeg;base64,{DataManager.image_to_b64(f"./iii_icon.png")}" alt="III Icon" style="width:500px;">
                    ''', unsafe_allow_html = True)
    with text_box:
        st.markdown("""
        <style>
            .powered-by {text-align:right;
                        font-size: 14px;
                        color: grey;}
        </style>
        <p class = powered-by> Powered by 資策會數轉院 <br/>跨域實證服務中心 創新孵化組</p>""", unsafe_allow_html = True)
    st.header("資策會 Demand Foresight Tools")
    st.page_link('page_main.py', label = '主題式趨勢報告產生器', icon = ':material/add_circle:')
    st.page_link('pages/page_summarize.py', label = '新聞摘要產生器', icon = ':material/add_circle:')
    st.page_link('pages/page_archive.py', label = 'ARCHIVE', icon = ':material/add_circle:')
    st.page_link('pages/page_demo.py', label = 'DEMO', icon = ':material/add_circle:')
    DataManager.fetch_IP()


    # * Entry Point: 登入後讓使用者輸入基本資料
    if 'user_recorded' in st.session_state:
        if st.button("重新選擇模型"):
            del st.session_state['user_recorded']
            st.rerun()
     

st.title("DEMO")

generator_tab, summarizor_tab = st.tabs(['主題式趨勢報告產生器', '新聞摘要產生器'])

with generator_tab:
    with st.container(border = True):
        st.video("https://www.youtube.com/watch?v=FWWyK7ia8Pw")

with summarizor_tab:
    with st.container(border = True):
        st.video("https://www.youtube.com/watch?v=UHgBXs5TZ4o")