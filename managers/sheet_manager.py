from streamlit_gsheets import GSheetsConnection
import streamlit as st
import pandas as pd
import datetime

from managers.export_manager import ExportManager
from managers.data_manager import DataManager



class SheetManager:

    # --- Communicate with Google Sheet that records the project name & id
    @staticmethod
    @st.cache_data
    def gs_conn(
        method: str, 
        project_name: str = None, 
        used_news_count: int = None, 
        used_pdfs: list = None, 
        user: str = None, 
        email: str = None,
        created_time: datetime.datetime.timestamp = None):
        
        assert method in ['fetch', 'update'], "parameter 'method' must be either 'fetch' or 'update'."

        if method == 'fetch':
            conn = st.connection("gsheets", type = GSheetsConnection)
            df_project = conn.read(worksheet = 'project', ttl = 0)
            df_pdfs = conn.read(worksheet = 'pdfs', ttl = 0)

            return {"project": df_project, "pdfs": df_pdfs}
        
        elif method == 'update':

            assert not None in [project_name, used_news_count, used_pdfs, user, email, created_time], '"Update" method requires all augements!'

            conn = st.connection("gsheets", type = GSheetsConnection)

            # * update 'project' sheet
            df_project = conn.read(worksheet = 'project', ttl = 0)

            df_project_append = pd.DataFrame([{
                "id": project_name + str(created_time),
                "project_name": project_name,
                "used_news_count": used_news_count,
                "user": user,
                "email": email,
                "created_time": created_time
            }])

            df_project_updated = conn.update(worksheet = 'project',
                                    data = pd.concat([df_project, df_project_append], ignore_index = True))
            
            # * update 'pdfs' sheet
            df_pdfs = conn.read(worksheet = 'pdfs', ttl = 0)
            df_pdfs_append = pd.DataFrame({
                "id": project_name + str(created_time),
                "pdf_name": used_pdfs
            })

            df_pdfs_updated = conn.update(worksheet = 'pdfs',
                                    data = pd.concat([df_pdfs, df_pdfs_append], ignore_index = True))
            
            return f'project {project_name} has been recorded to Google Sheet.'
            
if __name__ == "__main__":
    # SheetManager.gs_conn(
    #     "update",
    #     "TEST",
    #     300,
    #     ["a.pdf", "b.pdf"],
    #     "Wally",
    #     "huang0jin@gmail.com",
    #     datetime.datetime.timestamp(datetime.datetime.now())
    # )
    for _, row in SheetManager.gs_conn('fetch')['project'].iterrows():

        st.markdown(DataManager.get_output_download_link(
            row['id'], 'pptx', DataManager.get_pptx(row['id'])
        ), unsafe_allow_html = True)