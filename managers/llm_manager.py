import datetime as dt
import pandas as pd
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
from streamlit_gsheets import GSheetsConnection

from .data_manager import DataManager

class LlmManager:
    CLAUDE_KEY = st.secrets['CLAUDE_KEY']
    model = ChatAnthropic(model = 'claude-3-5-sonnet-20241022',
                            api_key = CLAUDE_KEY,
                            max_tokens = 8000,
                            temperature = 0.0,
                            verbose = True
                            )

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
    def create_prompt_chain(sys_prompt):

        # *** Create the Prompt ***
        prompt_obj = ChatPromptTemplate.from_messages(
            [
                ("system", sys_prompt),
                ("human", "{input}"),
                ("assistant", "{memory}")
            ]
        )

        # *** Create LLM Chain ***
        chain = prompt_obj | LlmManager.model

        return chain