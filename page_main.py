

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
if ("set_page_config" not in st.session_state):
    st.session_state['set_page_config'] = True
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
                content_col = st.selectbox("Summary", raw.columns)
            st.caption(":blue[選擇要作為 id, title, summary 的欄位後，點選**確認**]")
        except:
            st.info('請上傳"csv" 或 "xlsx" 格式，並且具有明確表頭的資料')

        if st.button("確認"):

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

            st.rerun()
                
    

    # * pdf 上傳的表單
    @st.dialog("上傳研究報告資料")
    def FORM_pdfs_data_upload():
        pdf_uploaded = st.file_uploader("上傳 PDF 格式研究報告（支援複數檔案）", type = "pdf", accept_multiple_files = True, key = 'pdfs')    

        if st.button("確認"):
            if pdf_uploaded is not None:
                for file in pdf_uploaded:
                    if file.name not in st.session_state["pdfs_raw"].keys():
                        pdf_in_messages = DataManager.load_pdf(file)
                        st.session_state["pdfs_raw"][file.name] = pdf_in_messages
            st.rerun()

    # * 新聞上傳的說明
    @st.dialog("關於新聞摘要資料")
    def FORM_news_explanation():
        st.write("""
- 由於大型語言模型有 input token 的限制，為了降低負荷量，我們要求新聞資料的內容要以「摘要」為主，請勿直接上傳新聞原文資料。
- 輸入的新聞摘要資料必須要有三個欄位：
                 
    - **id**:       用來唯一識別新聞文章
    - **title**:    新聞標題
    - **summary**:  新聞摘要
    
    欄位名稱不合也沒關係，此工具提供重新命名欄位功能。
- 若您手邊只有新聞原文資料，請使用**新聞摘要產生器**工具來製作（參考左側選單）。
- 若您的新聞筆數很大，請調整**批次數量**參數，讓語言模型分批處理。""")

    # * pdf 上傳的說明
    @st.dialog("研究報告資料是什麼？")
    def FORM_pdfs_explanation():
        st.write("""
- 您可以選擇是否上傳與主題相關的研究報告資料。大型語言模型將會從這些資料中歸納出能夠**支持新聞中趨勢的關鍵數據點。**
- 研究報告資料請上傳 **pdf** 格式。
- 請自行審核欲上傳的檔案品質，若內容不多（例如：都是圖片）或是太長、太短，則請先處理後再上傳，以免語言模型出錯。""")

    ll_1, lr_1 = st.columns((0.9, 0.1))
    ll_2, lr_2 = st.columns((0.9, 0.1))

    with ll_1:
        if st.button("點此上傳新聞摘要資料"):
            FORM_news_data_upload()
    with lr_1:
        if st.button("?", 'news_upload_explanation'):
            FORM_news_explanation()
    with ll_2:
        if st.button("點此上傳研究報告資料"):
            FORM_pdfs_data_upload()
    with lr_2:
        if st.button("?", 'pdfs_upload_explanation'):
            FORM_pdfs_explanation()

    ll_3, lr_3 = st.columns(2)
    with ll_3:
        # ** 主題名稱
        st.session_state["theme"] = st.text_input("請輸入**主題名稱**")
    with lr_3:
        # ** 拆分次數
        st.session_state["n_split"] = st.slider("請設定**批次數量**", 2, 10, step = 1)

        
    

def FUNC_right():
    
    TAB_news, TAB_pdfs = st.tabs(["新聞摘要資料預覽", "研究報告資料預覽"])
    with TAB_news:
        with st.container(height = 250, border = False):
            st.dataframe(st.session_state["news_raw"])
    with TAB_pdfs:
        with st.container(height = 250, border = False):
            for key, value in st.session_state["pdfs_raw"].items():
                st.caption(f"**:blue[{key}]**")
                st.json(value, expanded = False)



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
        

# *** Page main block
def UI():
    st.session_state['logged_in'] = True

    # * 第一步（第一個頁面）：資料上傳與資料處理
    if st.session_state['stage'] == "manual_data_processing":
        with BOX_data_process.container():
            st.markdown("<h4>資料上傳與參數設定</h4>", unsafe_allow_html = True)
            FUNC_left()

        with BOX_pdf_upload.container():
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
                    if key not in ["user_recorded", "user", "email", "logged_in", "authentication_status", "authenticator", "config"]:
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
            try:
                FUNC_call_executor_1()
                DataManager.send_notification_email(st.session_state['user'], 
                                                    st.session_state['email'],
                                                    type = 'halfway', page = 'trend_report')
            except Exception as error:
                DataManager.send_notification_email(st.session_state['user'], 
                                                    st.session_state['email'],
                                                    type = 'failed', page = 'trend_report', error = error)

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
        
            
        try:
            with BOX_call_executor_2.container():
                st.subheader("執行進度與操作")
                FUNC_call_executor_2()
            with BOX_show_result.container():
                st.subheader("成果連結")
                st.write("""\n\n\n\n\n""")
                
                # print(data)
                # print(type(data))
                st.success("Your trend report has been created and saved to **./output** folder. \n\nOr you can download by clicking the following link")
                result_pptx_base64 = ExportManager.Export.create_pptx(st.session_state["theme"], st.session_state["merged_report"])
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
            DataManager.send_notification_email(
                st.session_state['user'],
                st.session_state['email'],
                type = 'completed',
                page = 'trend_report'
            )
        except Exception as error:
            DataManager.send_notification_email(
                st.session_state['user'],
                st.session_state['email'],
                type = 'failed',
                page = 'trend_report',
                error = error
            )
            st.write(error)

def main():
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
            st.page_link('pages/page_demo.py', label = 'DEMO', icon = ':material/add_circle:')



    # * Entry Point: 登入後讓使用者輸入基本資料
    if 'user_recorded' in st.session_state:
        try:
            with st.sidebar:
                st.info(f"Dear **{st.session_state['user']}**, 歡迎使用資策會簡報產生器")
        except:
            pass
        with st.sidebar:
            if st.button("重設用戶資料"):
                del st.session_state['user_recorded']
                st.rerun()
        

    if "user_recorded" not in st.session_state:
    
        try:
            user_info()
        except:
            pass
        with st.sidebar:
            if st.button("設定用戶資料", type = "primary"):
                try:
                    user_info()
                except:
                    pass
        st.stop()

    

    if "user_recorded" in st.session_state:
        UI()

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
        main()
        with st.sidebar:
            authenticator.logout()
            DataManager.fetch_IP()

    
    elif st.session_state.authentication_status is False:
        st.error('使用者名稱/密碼不正確')

else:
    main()


