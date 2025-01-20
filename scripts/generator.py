import streamlit as st
import pandas as pd
import json
import numpy as np
from managers.data_manager import DataManager
from managers.prompt_manager import PromptManager
from managers.llm_manager import LlmManager


class Generator:

    '''此類別定義四個函數，為產生趨勢報告的四個流程
        1. news_gen():
            根據新聞內容產生趨勢報告：需要傳入 i 以紀錄這是第幾個 iteration。結果會被存入 "trends_in_parts" 這個 session state 中
        2. news_aggregate():
            讀取 "trend_in_parts" 這個 session state，將前面數次趨勢報告的結果統整成一份。結果會被存入 "trends_merged" 這個 session state
        3. pdf_gen():
            讀取 "trends_merged"這個 session state 的資料，從 pdf 檔案中找出可以佐證 trends_merged 的關鍵數據。每個 pdf 的關鍵數據會被存入 "pdf_results" 這個 session state 中
        4. merge():
            統整 "trends_merged" 和所有 pdf results 的結果，產出最終趨勢報告'''

    @staticmethod
    def news_gen(theme, in_message, i):

        chain = LlmManager.create_prompt_chain(PromptManager.News.basic_gen(theme),
                                               st.session_state['model'])
        
        # ** Generating by part
        if "trends_in_parts" not in st.session_state.keys():
            st.session_state["trends_in_parts"] = {}
            

        response = LlmManager.llm_api_call(chain, in_message)

        with open(f"./output/news_trend_{theme}_iter{i}.json", "w", encoding = "utf8") as f:
            json.dump(response, f, indent = 4, ensure_ascii = False)

        st.session_state["trends_in_parts"].update({f"iter{i}": response})
    
    @staticmethod
    def news_aggregate(theme):
        if "trends_merged" not in st.session_state.keys():
            st.session_state["merged"] = {}

        # ** Aggregatin three parts
        
        in_message = json.dumps(st.session_state["trends_in_parts"])
        chain = LlmManager.create_prompt_chain(PromptManager.News.aggregate(),
                                               st.session_state['model'])
        response = LlmManager.llm_api_call(chain, in_message)

        st.session_state["trends_merged"] = response
        
        # st.write(st.session_state["trends_merged"])

        with open(f"./output/news_trend_{theme}_merged.json", "w", encoding = "utf8") as f:
            json.dump(response, f, indent = 4, ensure_ascii = False)


    
    @staticmethod
    def pdf_gen(theme, filename, inputs):
        if "pdf_results" not in st.session_state:
            st.session_state['pdf_results'] = {}

        if filename in st.session_state['pdf_results'].keys():
            pass
        else:
            trends = "\n\n".join([f'{name}: {report}'.replace("{", "(").replace("}", ")") for name, report in st.session_state["trends_confirmed"].items()])
            # st.write(trends)
            chain = LlmManager.create_prompt_chain(PromptManager.Pdf.basic_gen(theme, trends),
                                                   st.session_state['model'])

            if len(inputs) > 50:
                in_message_lists = np.array_split(inputs, 5)
                result = ""
                for _ in in_message_lists:
                    in_message = "\n".join(_)
                    result += json.dumps(LlmManager.llm_api_call(chain, in_message), ensure_ascii = False) + "\n"
                pdf_merge_chain = LlmManager.create_prompt_chain(PromptManager.Pdf.aggregate(theme, trends),
                                                                 st.session_state['model'])
                response = LlmManager.llm_api_call(pdf_merge_chain, result)

            else:
                in_message_lists = [inputs]
                in_message = "\n".join(in_message_lists[0])
                response = LlmManager.llm_api_call(chain, in_message)

            with open(f"./output/[{theme}]_{filename}.json", "w", encoding = "utf8") as f:
                json.dump(response, f, indent = 4, ensure_ascii = False)

            st.session_state['pdf_results'].update({filename: response})

    @staticmethod
    def merge(theme, trend, trend_idx):
        if "merged_report" not in st.session_state:
            st.session_state["merged_report"] = {}

        chain = LlmManager.create_prompt_chain(PromptManager.Merge.merge(trend_idx), 
                                               st.session_state['model'])
        pdfs = ""
        try:
            for filename, content in st.session_state["pdf_results"].items():
                pdfs = pdfs + filename + "\n\n" + json.dumps(content) + "\n\n" + "-"*100 + "\n"
        except:
            pass

        in_message = f'''以下是（1）基於新聞趨勢分析而產出的趨勢報告:
{trend}
=================================================================================================================================
以下是（2）學術報告的摘要:
{pdfs}'''
        
        response = LlmManager.llm_api_call(chain, in_message)
        with open(f"./output/{theme}_trend_{trend_idx}_final.json", "w", encoding = "utf8") as f:
            json.dump(response, f, indent = 4, ensure_ascii = False)

        # st.write(response)
        st.session_state['merged_report'].update(response)



