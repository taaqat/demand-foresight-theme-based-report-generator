## 主題型趨勢報告（資料源為使用者上傳）

#### `page_main.py`
Main UI front-end script.

#### `scripts`
##### `generator.py`
This file contains class `Generator` that is composed of four functions (four steps for generation).
        1. `news_gen()`:
            Generate trend reports by parts based on the input news data. Id `i` should be passed in to identify the iteration. The result would be stored in `trends_in_parts` session state.
        2. `news_aggregate()`:
            Load data in the session state `trend_in_parts` and aggregate several trend reports in the previous step into one. The result would be stored in `trends_merged` session state.
        3. `pdf_gen()`:
            Load data in session state `trends_merged` and search key data that supports the trend report from the uploaded pdf research report. Key data for all pdf files would be stored in `pdf_results` session state.
        4. `merge()`:
            Merge `trends_merged` and `pdf_files` and generate the final trend report.
            
##### `executor.py`
串接 `generator.py` 裡面的函數，於 UI 只需要呼叫 `Executor.execute()` 並傳入指定引述即可

#### `managers`
`data_manager.py`
Defines function for data transformation and loading.

`export_manager.py`
Defines function for generating pptx file.

`llm_manager.py`
Defines function that communicates with LangChain anthropic.

`prompt_manager.py`
Defines prompts for each step.

#### `summarize.py`
Summarize news contents in advance. (Execute this file if the news data does not have summary for each news.)