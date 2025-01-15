import datetime as dt
import pandas as pd
import base64
import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
import datetime as dt
import tqdm
import streamlit as st
import openpyxl
import json, base64, os
from io import BytesIO
import urllib3
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import requests
from time import sleep
import re
import sys
from streamlit_gsheets import GSheetsConnection
from pypdf import PdfReader

class DataManager:
    
    @staticmethod
    def find_json_object(input_string):
        '''catch the JSON format from LLM response'''

        # Match JSON-like patterns
        input_string = input_string.replace("\n", '').strip()
        input_string = input_string.encode("utf-8").decode("utf-8")
        start_index = input_string.find('{')
        end_index = input_string.rfind('}')

        if start_index != -1 and end_index != -1:
            json_string = input_string[start_index:end_index+1]
            try:
                json_object = json.loads(json_string)
                return json_object
            except json.JSONDecodeError:
                return "DecodeError"
        # st.write(json_string)

        return None  # Return None if no valid JSON is found
    
    @staticmethod
    @st.cache_data
    def load_news(uploaded):

        '''load news data from user upload with caching'''
        if uploaded is not None:
            try:
                return pd.read_csv(uploaded)
            except:
                return pd.read_excel(uploaded)
                    
        else:
            return None
        
    @staticmethod
    @st.cache_data
    def load_pdf(uploaded):

        '''load pdf data from user upload with caching'''
        reader = PdfReader(uploaded)
        number_of_pages = len(reader.pages)
        texts = []
        for i in range(number_of_pages):
            page = reader.pages[i]
            texts.append(f"【page {i}】\n" + page.extract_text())

        return texts
    
    @staticmethod
    def get_output_download_link(topic, ext, content_b64):
        
        '''Return output ppt slide download link in HTML formatt'''
        assert ext in ['pptx', 'xlsx', 'json'], "Parameter 'ext' must be one of the following: ['pptx', 'xlsx', 'json']"

        mapping = {
                "pptx": {
                    "filename": f"[主題型]{topic}_trends.pptx",
                    "type": "vnd.openxmlformats-officedocument.presentationml.presentation",
                    "text": f"Download the {topic} trend report(Pptx Slides)"
                },
                "xlsx": {
                    "filename": f"[主題型]{topic}.xlsx",
                    "type": "vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "text": f"Download trend reports (Excel)"
                },
                "json": {
                    "filename": f"[主題型]{topic}_trend_report_.json",
                    "type": "json",
                    "text": f"Download {topic} trend report (JSON)"
                }
            }


        
        comps = (mapping[ext]['type'], mapping[ext]['filename'], mapping[ext]['text'])
        return f'<a href = "data:application/{comps[0]};base64,{content_b64}" download = "{comps[1]}"> {comps[2]}</a>'
    
    # --- Transform Picture to Base64
    @staticmethod
    def image_to_b64(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")