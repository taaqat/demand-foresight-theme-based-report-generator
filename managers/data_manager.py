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
    def get_output_download_link(id, ext, content_b64):
        
        '''Return output ppt slide download link in HTML formatt'''
        assert ext in ['pptx', 'xlsx', 'json'], "Parameter 'ext' must be one of the following: ['pptx', 'xlsx', 'json']"

        mapping = {
                "pptx": {
                    "filename": f"[主題型]{id}_trends.pptx",
                    "type": "vnd.openxmlformats-officedocument.presentationml.presentation",
                    "text": f"Download the {id} trend report(Pptx Slides)"
                },
                "xlsx": {
                    "filename": f"[主題型]{id}.xlsx",
                    "type": "vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "text": f"Download trend reports (Excel)"
                },
                "json": {
                    "filename": f"[主題型]{id}_trend_report_.json",
                    "type": "json",
                    "text": f"Download {id} trend report (JSON)"
                }
            }


        
        comps = (mapping[ext]['type'], mapping[ext]['filename'], mapping[ext]['text'])
        return f'<a href = "data:application/{comps[0]};base64,{content_b64}" download = "{comps[1]}"> {comps[2]}</a>'
    
    # --- Transform Picture to Base64
    @staticmethod
    def image_to_b64(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    
    # --- Get file from III database
    @staticmethod
    def get_pptx(project_id):

        path = f"[主題式]{project_id}.pptx"

        url = 'http://61.64.60.30/news-crawler/api/file/?'
        
        headers = {
            'Authorization': st.secrets['III_KEY']
        }

        end_point_params = {
            'file_name': path
        }

        response = requests.get(url, params = end_point_params, headers = headers)
        
        try:
            response_b64 = response.json()['file_content']
            return response_b64
        except:
            raise ValueError("No such file in the database!")
    
    # --- Post file to III database
    @staticmethod
    def post_pptx(
            project_id, 
            file_content, 
            expiration, 
            user_name, 
            user_email
            ):

        # form_values = '{"name": "%s", "email": %s"}'%(user_name, user_email)
        # print(form_values)

        path = f"[主題式]{project_id}.pptx"

        url = 'http://61.64.60.30/news-crawler/api/file/?'

        headers = {
            'Authorization': st.secrets['III_KEY']
        }

        payload = {
            'file_name': path,
            'file_content': file_content,
            'expire_at': expiration,
            'form_values': {'name': user_name, 'email': user_email}
            }

        # *** Set up retries for the connection ***
        retry_strategy = Retry(
            total = 3,  # Number of retries
            status_forcelist = [429, 500, 502, 503, 504]  # Retry on these status codes
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.Session()
        http.mount("https://", adapter)
        http.mount("http://", adapter) 
        try:
            response = http.post(url, json = payload, headers = headers)
            # st.info(f"File {json.loads(response.content)['file_name']} has been updated to III's database")
        except:
            response = http.post(url, json = payload, headers = headers)
            st.warning(response.content)

        return response