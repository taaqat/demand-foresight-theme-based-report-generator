import pandas as pd
import streamlit as st
import json
from managers.llm_manager import LlmManager
from managers.data_manager import DataManager
from managers.sheet_manager import SheetManager

prompt = lambda lang, length: f'''
你是一個有力的產經分析研究員，目前正在著手進行「印度經濟」相關的分析。
我接下來會輸入印度的新聞（包含新聞 id, 標題和內容），需要請你幫我進行新聞的摘要處理，詳細規則如下：
1. 每則新聞請幫我先翻譯成「**{lang}**」
2. 之後用 {length} ~ {round(length * 1.25)} 字進行重點摘要
3. 最後按照指定輸出格式回傳給我，「不需要給我其他文字」。
4. 若沒有足夠的新聞內文讓你摘要，請回傳「無」。
5. 內文中的所有引號，請幫我轉成 ' 以避免 JSON 格式無法被抓取。
<output schema>
```
("id": "我輸入的新聞id",
 "title": "我輸入的新聞標題",
 "summary": "你幫我統整的新聞摘要。若無則回傳「無」")
```
請自行將小括號轉義成大括號以符合 JSON 格式。

'''

class Summarizor:
    
    @staticmethod
    def summarize(df, BOX, client = None):
        progress_bar = st.progress(0, "Summarizing")
        
        if 'summarized_data' not in st.session_state:
            st.session_state['summarized_data'] = pd.DataFrame()

        
        try:
            for i, row in df.iterrows():
                with BOX.container(height = 250, border = False):
                    st.dataframe(st.session_state['summarized_data'], width = 1000)

                progress_bar.progress(i/len(df), f"Summarizing ({i}/{len(df)})")
    
                if str(row['id']) in [news['id'] for i, news in st.session_state['summarized_data'].iterrows()]:
                    pass
                else:
                    in_message = f"新聞id: {row['id']}\n\n新聞標題: {row['title']}\n\n內文開始\n---{row['content']}\n---\n內文結束"
                    response = LlmManager.llm_api_call(
                        LlmManager.create_prompt_chain(prompt(lang = st.session_state['lang'],
                                                              length = st.session_state['len_per_summary']),
                                                              st.session_state['model']), 
                                                              in_message)
                    
                    # * 試著將結果 Insert 進去 Google Sheeet
                    if client is not None:
                        try:
                            res_row = [value for key, value in response.items()]
                            SheetManager.SummaryGSDB.insert(
                                client, st.session_state["sheet_url"], res_row
                            )
                        except:
                            st.warning("Failed to store the new row to the objective google sheet link")
                    
                    new_row = pd.DataFrame([response])
                    st.session_state['summarized_data'] = pd.concat([st.session_state['summarized_data'], new_row], ignore_index = True)
                
                progress_bar.progress((i+1)/len(df), f"Summarizing ({i + 1}/{len(df)})")

            st.success("Completed!")
            progress_bar.empty()
            DataManager.send_notification_email(
                st.session_state['user'],
                st.session_state['email'],
                type = 'completed',
                page = 'summary'
            )
        except Exception as error:
            
            DataManager.send_notification_email(
                st.session_state['user'],
                st.session_state['email'],
                type = 'failed',
                page = 'summary',
                error = error
            )
            raise error