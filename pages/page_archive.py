import streamlit as st
import streamlit_authenticator as stauth
from managers.data_manager import DataManager

# * --- Config
if ("set_page_config" not in st.session_state):
    st.session_state['set_page_config'] = True
    st.set_page_config(page_title='III Trend Report Generator', page_icon=":tada:", layout="wide")
    
@st.dialog("輸入基本資料：")
def user_info():
    user = st.text_input("你的暱稱")
    email = st.text_input("電子信箱")

    if st.button("Submit"):
        if user == None:
            st.warning("暱稱請勿留空")
        if email == None:
            st.warning("電子信箱請勿留空")
        if (not user == None) & (not email == None):
            st.session_state["user"] = user
            st.session_state["email"] = email
            st.session_state["user_recorded"] = True
            st.rerun()

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
    with st.sidebar:
        st.page_link('page_main.py', label = '主題式趨勢報告產生器', icon = ':material/add_circle:')
        st.page_link('pages/page_summarize.py', label = '新聞摘要產生器', icon = ':material/add_circle:')
        st.page_link('pages/page_archive.py', label = 'ARCHIVE', icon = ':material/add_circle:')

    # * Entry Point: 登入後讓使用者輸入基本資料
    if 'user_recorded' in st.session_state:
        try:
            st.info(f"Dear **{st.session_state['user']}**, 歡迎使用資策會簡報產生器")
        except:
            pass
        if st.button("重設用戶資料"):
            del st.session_state['user_recorded']
            st.rerun()
        

    if "user_recorded" not in st.session_state:
        try:
            user_info()
        except:
            pass

        if st.button("設定用戶資料", type = "primary"):
            try:
                user_info()
            except:
                pass
        st.stop()

    

    
    