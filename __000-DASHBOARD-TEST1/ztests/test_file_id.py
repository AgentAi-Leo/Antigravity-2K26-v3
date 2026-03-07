import streamlit as st
print(hasattr(st.uploaded_file_manager.UploadedFileRec, "file_id") if hasattr(st, "uploaded_file_manager") else "cannot check easily")
