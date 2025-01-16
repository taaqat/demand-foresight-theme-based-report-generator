import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from managers.data_manager import DataManager
from scripts.summarizor import Summarizor


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

# * --- Config
if ("set_page_config" not in st.session_state):
    st.session_state['set_page_config'] = True
    st.set_page_config(page_title='III Trend Report Generator', page_icon=":tada:", layout="wide")

st.title("新聞摘要產生器")
st.markdown("""<style>
    div.stButton > button {
        width: 100%;  /* 設置按鈕寬度為頁面寬度的 50% */
        height: 50px;
        margin-left: 0;
        margin-right: auto;
    }
    </style>
    """, unsafe_allow_html=True)

if "summarization_status" not in st.session_state:
    st.session_state["summarization_status"] = "not_started"

if "news_to_be_summarized" not in st.session_state:
    st.session_state["news_to_be_summarized"] = pd.DataFrame()
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


# * 新聞資料上傳的表單
@st.dialog("上傳新聞資料")
def FORM_news_data_upload():
    uploaded = st.file_uploader("上傳新聞資料", key = 'news')
    raw = DataManager.load_news(uploaded)                 
    with st.expander("預覽你上傳的資料"):
        st.dataframe(raw)

    # *** Data Column Rename
    try:
        rename_l, rename_m, rename_r= st.columns(3)
        with rename_l:
            id_col = st.selectbox("ID", raw.columns)
        with rename_m:
            title_col = st.selectbox("Title", raw.columns)
        with rename_r:
            content_col = st.selectbox("Content", raw.columns)
        st.caption(":blue[選擇要作為 id, title, content 的欄位後，點選**確認**]")
    except:
        st.info('請上傳"csv" 或 "xlsx" 格式，並且具有明確表頭的資料')

    if st.button("確認"):

        if pd.DataFrame(raw).empty:
            st.warning("請上傳新聞資料")
        else:
            raw_renamed = raw.rename(
                columns = {
                    id_col: "id",
                    title_col: "title",
                    content_col: "content"
                }
            )
            raw_renamed = raw_renamed[['id', 'title', 'content']]
            st.session_state["news_to_be_summarized"] = raw_renamed

        st.rerun()

# *****************************************  
# ***************** Main ******************
if "user_recorded" in st.session_state:
    COL_LEFT, COL_RIGHT = st.columns(2)
    with COL_RIGHT:
        BOX_preview = st.empty()
        BOX_output = st.empty()
    
    with COL_LEFT:
    
        BOX_stage_button = st.empty()
        
        if st.session_state['summarization_status'] == 'not_started':
            with BOX_stage_button.container():
                if st.button("點擊上傳欲生成摘要的新聞資料"):
                    FORM_news_data_upload()
                if st.button("確認送出，開始摘要", type = "primary"):
                    st.session_state['summarized_data'] = pd.DataFrame()
                    if not st.session_state["news_to_be_summarized"].empty:
                        BOX_stage_button.empty()
                        st.session_state['summarization_status'] = 'started'
                        st.rerun()
                    else:
                        st.warning("請上傳欲摘要的新聞資料")
                

        if st.session_state['summarization_status'] == 'started':
            with BOX_stage_button.container():
                
                if st.button("上一步"):
                    BOX_stage_button.empty()
                    st.session_state['summarization_status'] = 'not_started'
                    st.rerun()
                
                # TODO EXECUTOR FUNCTION
                Summarizor.summarize(st.session_state["news_to_be_summarized"], BOX_output)
                

    


    if st.session_state['summarization_status'] == 'started':
        with BOX_output.container(height = 250):
            st.markdown('<h4>新聞摘要結果</h4>', unsafe_allow_html = True)
            st.dataframe(st.session_state['summarized_data'])
            