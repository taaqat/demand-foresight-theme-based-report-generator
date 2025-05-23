import datetime as dt
import pandas as pd
import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
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
from streamlit_gsheets import GSheetsConnection

from .data_manager import DataManager

class LlmManager:
    if 'KEY_verified' not in st.session_state:
        st.session_state['KEY_verified'] = False

    # * initialize model
    @staticmethod
    def init_model():
        if st.session_state['model_type'] == "":
            raise ValueError("Model type not specified!")
        elif st.session_state['model_type'] == "claude-3-5-sonnet-20241022":
            model = ChatAnthropic(model = 'claude-3-5-sonnet-20241022',
                                    api_key = st.session_state['LLM_KEY'],
                                    max_tokens = 8000,
                                    temperature = 0.0,
                                    verbose = True
                                    )
        elif st.session_state['model_type'] == "gpt-4o":
            model = ChatOpenAI(model = "gpt-4o",
                               api_key = st.session_state['LLM_KEY'],
                               max_tokens = 16000,
                               temperature = 0.0,
                               verbose = True)
        return model
    
    # * test if the api key is valid
    @staticmethod
    def api_key_verify(model):
        response = model([HumanMessage(content = "Hello, Claude!")])
        st.session_state['KEY_verified'] = True
        return response

    @staticmethod
    @st.dialog("輸入基本資料：")
    def user_info():
        
        if st.secrets['permission']['user_token'] == True:
            model_select = st.selectbox("請選擇欲使用的語言模型", ["claude-3-5-sonnet-20241022", "gpt-4o"])
            if model_select == "claude-3-5-sonnet-20241022":
                tk = st.text_input("請輸入您的 Claude API Key")
            elif model_select == "gpt-4o":
                tk = st.text_input("請輸入您的 OpenAI API Key")
            if st.button("確認"):
                st.session_state['model_type'] = model_select
                st.session_state["user"] = 'iii-demand-foresight-theme-based'
                st.session_state["email"] = 'linchunhuang@iii.org.tw'
                st.session_state['LLM_KEY'] = tk
                st.session_state['model'] = LlmManager.init_model()
                with st.spinner("Verifying API key..."):
                    try:
                        LlmManager.api_key_verify(st.session_state['model'])
                        st.session_state["user_recorded"] = True
                        st.rerun()

                    except Exception as e:
                        st.warning("Invalid Token")
        else:
            
            model_select = st.selectbox("請選擇欲使用的語言模型", ["claude-3-5-sonnet-20241022", "gpt-4o"])
            if st.button("確認"):
                st.session_state['model_type'] = model_select
                st.session_state["user"] = 'iii-demand-foresight-theme-based'
                st.session_state["email"] = 'linchunhuang@iii.org.tw'
                if model_select == "claude-3-5-sonnet-20241022":
                    st.session_state['LLM_KEY'] = st.secrets['CLAUDE_KEY']
                elif model_select == "gpt-4o":
                    st.session_state['LLM_KEY'] = st.secrets['OPENAI_KEY']
                st.session_state['model'] = LlmManager.init_model()
                st.session_state["user_recorded"] = True
                st.rerun()


    # Implement Anthropic API call 
    # *** input: chain(prompt | model), in_message(str) ***
    # *** output: json ***
    @staticmethod
    def llm_api_call(chain, in_message):

        summary_json = ""                      # initialize output value

        # This function ensures the return value from LLM is complete
        def run_with_memory(chain, in_message) -> str:
            memory = ""
            
            response = chain.invoke({"input": in_message, "memory": memory})
            while response.usage_metadata["output_tokens"] >= 5000:
                memory += response.content
                response = chain.invoke({"input": in_message, "memory": memory})
            memory += str(response.content)
            # st.write(memory)
            return memory
        
        summary_json = DataManager.find_json_object(run_with_memory(chain, in_message))
        # st.write(summary_json)

        fail_count = 0
        while (summary_json in ["null", "DecodeError", None]):
            # While encountering error, first let Claude rest for 10 secs
            time.sleep(10)

            memory = ""

            cutting_points = [i * (len(in_message) // 2) for i in range(1, 2)]
            intermediate = [
                run_with_memory(chain, in_message[:cutting_points[0]]),
                run_with_memory(chain, in_message[cutting_points[0]:])
            ]

            response = chain.invoke({"input": "\n\n".join(intermediate), "memory": memory})
            while response.usage_metadata["output_tokens"] >= 5000:
                memory += response.content
                response = chain.invoke({"input": "\n\n".join(intermediate), "memory": memory})
            memory += str(response.content)
            summary_json = DataManager.find_json_object(memory)

            fail_count += 1

            if fail_count == 10:
                print("Claude model crushed more than 10 times during runtime. Please consider re-running...")

        return summary_json
        
    @staticmethod
    def create_prompt_chain(sys_prompt, model):

        # *** Create the Prompt ***
        prompt_obj = ChatPromptTemplate.from_messages(
            [
                ("system", sys_prompt),
                ("human", "{input}"),
                ("assistant", "{memory}")
            ]
        )

        # *** Create LLM Chain ***
        chain = prompt_obj | model

        return chain