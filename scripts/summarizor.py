import pandas as pd
import streamlit as st
from managers.llm_manager import LlmManager

prompt = '''
你是一個有力的產經分析研究員，目前正在著手進行「印度經濟」相關的分析。
我接下來會輸入印度的新聞（包含新聞 id, 標題和內容），需要請你幫我進行新聞的摘要處理，詳細規則如下：
1. 每則新聞請幫我先翻譯成「**繁體**中文」
2. 之後用 200 - 300 字進行重點摘要
3. 最後按照指定輸出格式回傳給我，「不需要給我其他文字」。
4. 若沒有足夠的新聞內文讓你摘要，請回傳「無」
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
    def summarize(df, BOX):
        progress_bar = st.progress(0, "Summarizing")

        if 'summarized_data' not in st.session_state:
            st.session_state['summarized_data'] = pd.DataFrame()

        results = []
        for i, row in df.iterrows():
            with BOX.container(height = 250, border = False):
                st.markdown('<h4>新聞摘要結果</h4>', unsafe_allow_html = True)
                st.dataframe(st.session_state['summarized_data'])

            progress_bar.progress(i/len(df), f"Summarizing ({i}/{len(df)})")
            if row['id'] in [news['id'] for i, news in st.session_state['summarized_data'].iterrows()]:
                pass
            else:
                in_message = f"新聞id: {row['id']}\n\n新聞標題: {row['title']}\n\n內文開始\n---{row['content']}\n---\n內文結束"
                response = LlmManager.llm_api_call(LlmManager.create_prompt_chain(prompt), in_message)
                results.append(response)
                st.session_state['summarized_data'] = pd.DataFrame(results)
            
            progress_bar.progress((i+1)/len(df), f"Summarizing ({i + 1}/{len(df)})")

        st.success("Completed!")
        progress_bar.empty()
        