import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import re
from managers.data_manager import DataManager
from managers.sheet_manager import SheetManager

from gspread.exceptions import APIError

# * --- Config
if ("set_page_config" not in st.session_state):
    st.session_state['set_page_config'] = True
    st.set_page_config(page_title='III Trend Report Generator', page_icon=":tada:", layout="wide")
    


st.title("ARCHIVE")

st.markdown("""<style>
    div.stButton > button {
        width: 100%;  /* 設置按鈕寬度為頁面寬度的 50% */
        height: 50px;
        margin-left: 0;
        margin-right: auto;
    }
    </style>
    """, unsafe_allow_html=True)


# ------------------------------------------------------------------------------------------------------
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
        

# ********* Main *********
COL_LEFT, COL_RIGHT = st.columns(2)

with COL_LEFT:
    try:
        st.session_state['gs'] = SheetManager.gs_conn('fetch')
    except APIError:
        st.warning("無法連線至 Google Sheet 資料庫，請稍後再試")
        st.stop()

    project_id = st.selectbox("選擇專案", options = st.session_state['gs']['project']['id'],
                 format_func = lambda id: re.search("([^\d]*)[\d\.]+", id).groups()[0] + f" (Created: {pd.to_datetime(st.session_state['gs']['project'][st.session_state['gs']['project']['id'] == id]['created_time'], unit = 's').dt.strftime('%Y-%m-%d %H:%M:%S').tolist()[0]} )")

    ll, lr = st.columns((0.9, 0.1))
    with ll:
        query = st.button("查詢")
    with lr:
        reload_gs = st.button("⟳")
        if reload_gs:
            st.cache_data.clear()
            st.rerun()

with COL_RIGHT:
    st.markdown('<h4>下載連結</h4>', unsafe_allow_html = True)
    if query:
        st.markdown(
            DataManager.get_output_download_link(project_id, 'pptx', DataManager.get_pptx(project_id)),
            unsafe_allow_html = True
        )
    
    