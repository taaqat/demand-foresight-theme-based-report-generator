

from scripts.generator import Generator
from scripts.executor import Executor

from managers.data_manager import DataManager
from managers.export_manager import ExportManager
from managers.sheet_manager import SheetManager



import streamlit as st
import pandas as pd
import json
import os
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from streamlit_authenticator import Hasher
import yaml
import datetime


# *********** Config ***********
st.set_page_config(page_title='III Trend Report Generator', page_icon=":tada:", layout="wide")
st.title("主題式趨勢報告")

if "config" not in st.session_state:
    with open("users.yaml") as file:
        st.session_state.config = yaml.load(file, Loader=SafeLoader)

# 初始化新聞原始資料的容器
if 'news_raw' not in st.session_state:
    st.session_state['news_raw'] = pd.DataFrame()

# 初始化 pdf 原始資料的容器
if 'pdfs_raw' not in st.session_state:
    st.session_state['pdfs_raw'] = {}

# 初始化 stage
if 'stage' not in st.session_state:
    st.session_state['stage'] = "manual_data_processing"


st.markdown("""<style>
    div.stButton > button {
        width: 100%;  /* 設置按鈕寬度為頁面寬度的 50% */
        height: 50px;
        margin-left: 0;
        margin-right: auto;
    }
    </style>
    """, unsafe_allow_html=True)

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

# *** BOX 開頭的變數，為存放不同步驟的 UI 元件的 placeholders
LEFT_COL, RIGHT_COL = st.columns(2)

with LEFT_COL:
    BOX_data_process = st.empty()
    BOX_call_executor_1 = st.empty()
    BOX_call_executor_2 = st.empty()


with RIGHT_COL:
    BOX_pdf_upload = st.empty()
    BOX_show_result = st.empty()

BOX_S1_BUTTON = st.empty()

# **********************************************************************************************************************************
# ************************************** Data Upload **********************************************
# *** News data upload

# *** FUNC 開頭的變數，為執行特定功能的函數，會被包在 BOX 當中
def FUNC_left():
    uploaded = st.file_uploader("上傳新聞資料")
    raw = DataManager.load_news(uploaded)                 # *** 之後改成 user upload
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
            content_col = st.selectbox("Summary", raw.columns)
    except:
        st.info('請上傳"csv" 或 "xlsx" 格式，並且具有明確表頭的資料')

    if st.button("Rename"):
        if pd.DataFrame(raw).empty:
            st.warning("請上傳新聞資料")
        else:
            raw_processed = raw.rename(
                columns = {
                    id_col: "id",
                    title_col: "title",
                    content_col: "summary"
                }
            )
            raw_processed = raw_processed[['id', 'title', 'summary']]
            st.session_state["news_raw"] = raw_processed


    

    
    if [col in st.session_state["news_raw"].columns for col in ["id", "title", "summary"]] == [True, True, True]:
        with st.expander("預覽重新命名後的資料"):
            st.dataframe(st.session_state['news_raw'])

        
        

def FUNC_right():
    pdf_uploaded = st.file_uploader("上傳 PDF 格式研究報告（支援複數檔案）", type = "pdf", accept_multiple_files = True)    

    if pdf_uploaded is not None:
        for file in pdf_uploaded:
            pdf_in_messages = DataManager.load_pdf(file)
            st.session_state["pdfs_raw"][file.name] = pdf_in_messages

    # ** 主題名稱
    st.subheader("請輸入主題名稱（Mandatory）")
    st.session_state["theme"] = st.text_input("請輸入**主題名稱**")
    
    # ** 拆分次數
    st.subheader("請選擇拆分次數")
    st.session_state["n_split"] = st.slider("依據你輸入的新聞資料多寡，決定要將資料拆成幾批來處理。",
                                               2, 20, step = 1)
    

def FUNC_call_executor_1():
    cl, cr = st.columns(2)
    with cl:
        if st.button("Undo"):
            st.session_state["stage"] = 'manual_data_processing'
            st.rerun()
    with cr:
        if st.button("Rerun"):
            st.rerun()
    
    Executor.execute_1(st.session_state["theme"], st.session_state["n_split"])
    

def FUNC_call_executor_2():
    cl, cr = st.columns(2)
    with cl:
        if st.button("Undo"):
            st.session_state["stage"] = 'generating'
            st.rerun()
    with cr:
        if st.button("Rerun"):
            st.rerun()
    Executor.execute_2(st.session_state["theme"])
        

# *** Main Part

 
def main():
    st.session_state['logged_in'] = True

    

    # * 第一步（第一個頁面）：資料上傳與資料處理
    if st.session_state['stage'] == "manual_data_processing":
        with BOX_data_process.container():
            st.subheader("請上傳新聞摘要資料")
            FUNC_left()

        with BOX_pdf_upload.container():
            st.subheader("請上傳研究報告（Optional）")
            FUNC_right()

        with BOX_S1_BUTTON.container():
            c_proceed, c_undo = st.columns(2)

        # * 若確定繼續，則 stage 跳到 generating。結合後面的 if else statement，畫面跳轉至第二步驟的頁面
        with c_proceed:
            if st.button("Submit", type = "primary"):
                if st.session_state["news_raw"].empty:
                    st.warning("請上傳新聞資料")
                else:
                    st.session_state['stage'] = "generating"
                    if 'trends_in_parts' in st.session_state:
                        del st.session_state['trends_in_parts']
                    if 'trends_merged' in st.session_state:
                        del st.session_state['trends_merged']
                    st.rerun()

        # * 若想重新選擇欄位或上傳 pdf，點選 Undo。此舉動會清除所有 session state 變數，請注意。
        with c_undo:
            if st.button("Undo", type = "secondary"):
                st.session_state["news_raw"] = pd.DataFrame()
                for key in st.session_state.keys():
                    del st.session_state[key]
                st.rerun()

    # * 第二步（第二個頁面）：AI 推論分析（前半）
    elif (st.session_state['stage'] == "generating") :

        BOX_S1_BUTTON.empty()

        with BOX_show_result.container():
            st.subheader("成果連結")
            st.write("""\n\n\n\n\n""")

        with BOX_call_executor_1.container():
            st.subheader("執行進度與操作")
            FUNC_call_executor_1()

            # todo *** Add a block that asks users to check the output so far.
            edited_text = st.text_area("請**確認**到目前為止生成的趨勢報告，並且依照喜好進行**編輯**。", 
                         json.dumps(st.session_state["trends_merged"], indent = 4, ensure_ascii = False),
                         height = 200)
            # ** test whether user breaks the JSON formatting of the string
            try:
                st.session_state['trends_confirmed'] = json.loads(edited_text)
                 # Wait for user confirmation
                if st.button("Press to proceed", type = "primary"):
                    st.session_state['stage'] = "proceeding"
                    st.rerun()
            except json.decoder.JSONDecodeError:
                st.warning("請不要破壞 JSON 結構！")

           

    # * 第三步（第二個頁面）：AI 推論分析（後半）
    elif (st.session_state['stage'] == "proceeding"):
        with BOX_show_result.container():
            st.subheader("成果連結")
            st.write("""\n\n\n\n\n""")

        BOX_call_executor_1.empty()
        with BOX_call_executor_2.container():
            st.subheader("執行進度與操作")
            FUNC_call_executor_2()
        
        with BOX_show_result.container():
            st.subheader("成果連結")
            st.write("""\n\n\n\n\n""")
            with open(f"./output/{st.session_state["theme"]}_trend_report.json") as f:
                data = json.load(f)

            # print(data)
            # print(type(data))
            st.success("Your trend report has been created and saved to **./output** folder. \n\nOr you can download by clicking the following link")
            result_pptx_base64 = ExportManager.Export.create_pptx(st.session_state["theme"], data)
            st.markdown(
                DataManager.get_output_download_link(
                    st.session_state["theme"], 
                    "pptx", 
                    result_pptx_base64
                    ),
                unsafe_allow_html = True
                )
        created_time = datetime.datetime.timestamp(datetime.datetime.now())
        DataManager.post_pptx(
            project_id = st.session_state["theme"] + str(created_time),
            file_content = result_pptx_base64,
            expiration = str(datetime.datetime.today() + datetime.timedelta(365)),
            user_name = st.session_state['user'],
            user_email = st.session_state['email']
        )
        SheetManager.gs_conn(
            "update",
            st.session_state["theme"],
            len(st.session_state["news_raw"]),
            list(st.session_state["pdf_results"].keys()),
            st.session_state['user'],
            st.session_state['email'],
            created_time
        )
            



# ------------------------------------------------------------------------------------------------------
# *** Authentication & Call the main function ***
            
if st.secrets['permission']['authenticate'] == True:

    authenticator = stauth.Authenticate(
        st.session_state.config['credentials'],
        st.session_state.config['cookie']['name'],
        st.session_state.config['cookie']['key'],
        st.session_state.config['cookie']['expiry_days'],
    )
    try:
        l, m, r = st.columns((1/4, 1/2, 1/4))
        with m:
            placeholder = st.container()
        with placeholder:
            authenticator.login('main')
    except Exception as e:
        st.error(e)

    if st.session_state.authentication_status:
        st.session_state.authenticator = authenticator
        
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

            # * Entry Point: 登入後讓使用者輸入基本資料
            if 'user_recorded' in st.session_state:
                try:
                    st.code(f"歡迎使用資策會簡報產生器, {st.session_state['user']}")
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
                authenticator.logout()
                st.stop()

            authenticator.logout()

        main()

            
        
    elif st.session_state.authentication_status is False:
        st.error('使用者名稱/密碼不正確')

else:
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

        # * Entry Point: 使用者輸入基本資料
        if 'user_recorded' in st.session_state:
            try:
                st.code(f"歡迎使用資策會簡報產生器, {st.session_state['user']}")
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
    main()


