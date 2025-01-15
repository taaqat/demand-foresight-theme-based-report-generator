
# from managers.data_manager import DataManager
# from managers.export_manager import ExportManager
# from managers.llm_manager import LlmManager
# from managers.prompt_manager import PromptManager
# from managers.session_manager import SessionManager
from scripts.generator import Generator

import datetime as dt
import pandas as pd
import streamlit as st
import time
import numpy as np
import json
from managers.data_manager import DataManager
from managers.export_manager import ExportManager

class Executor:

    '''此類別打包所有在 generator 中的函數，於 UI 只需要呼叫 Executor.execute() 並傳入指定引述即可'''

    @staticmethod
    def execute_1(theme, n_split):
        if "trends_in_parts" not in st.session_state.keys():
            st.session_state['trends_in_parts'] = {}
        if "trends_merged" not in st.session_state.keys():
            st.session_state['trends_merged'] = {}


        # ** Generating trend reports from news data by parts
        progress_bar = st.progress(0, "Generating news trend report")
        if st.session_state["trends_in_parts"] == {}:
            inputs = "【 事件編號 id: " + st.session_state["news_raw"]["id"].astype(str)+ "; 事件標題 title: " + st.session_state["news_raw"]["title"]+ "】" + "\n\n"  + st.session_state["news_raw"]["summary"]

            # Determine chunk size
            chunk_size = len(inputs) // n_split
            remainder = len(inputs) % n_split

            # Splitting into equal chunks
            splited_input = []
            start = 0
            for i in range(n_split):
                end = start + chunk_size + (1 if i < remainder else 0)  # Add 1 to the first 'remainder' chunks
                splited_input.append(inputs[start:end])
                start = end
            

            for i, df in enumerate(splited_input, start = 1):
                progress_bar.progress(0.4 * ((i - 1) / len(splited_input)), f"Generating batch {i}")
                Generator.news_gen(theme, "\n\n".join(df), i)
                progress_bar.progress(0.4 * (i / len(splited_input)), f"Generating batch {i + 1}")
        
        # ** Aggregating trend reports
        progress_bar.progress(0.4, f"Aggregating trend report...")
        if st.session_state['trends_merged'] == {}:
            Generator.news_aggregate(theme)
        progress_bar.progress(0.5, f"Searching key data from pdf reports")

            
    @staticmethod
    def execute_2(theme):
    
    
        progress_bar = st.progress(0.5, "Searching key data from pdf file uploaded")
        # ** Searching key data (關鍵數據) from pdf reports
        st.session_state["pdf_results"] = {}

        i = 0
        if st.session_state["pdfs_raw"] != {}:
            for file_name, content in st.session_state["pdfs_raw"].items():
                progress_bar.progress(0.5 + 0.3 * (i / len(st.session_state['pdfs_raw'].keys())), f"Processing **{file_name}**")
                Generator.pdf_gen(theme, file_name, content)
                i += 1
        else:
            st.session_state["pdfs_results"] = {}

        # ** Merging the result from 1. news trend report & 2. Key data from pdf reports
        j = 0
        for trend_name, trend_report in st.session_state["trends_merged"].items():
            progress_bar.progress(0.8 + 0.2 * (j / len(st.session_state['trends_merged'].keys())), f"Merging trend {j+1}")
            Generator.merge(theme, trend_report, j + 1)
            progress_bar.progress(0.8 + 0.2 * ( (j+1) / len(st.session_state['trends_merged'].keys())), f"Merging trend {j+2}")
            j += 1

        progress_bar.progress(1, "Complete!")

        final = {}
        for i, (trend_title, trend_content) in enumerate(st.session_state["trends_merged"].items(), start = 1):
            final[f"主要趨勢{i}"] = trend_content
        with open(f"output/{theme}_trend_report.json", "w", encoding = "utf8") as f:
            json.dump(st.session_state["merged_report"], f, ensure_ascii = False)
        
        # st.write(st.session_state["merged_report"])
        progress_bar.empty()

        st.success("Completed!")

        