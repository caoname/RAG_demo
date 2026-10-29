"""
基于Streamlit完成 Web 页面上传文件服务

streamlit 有个核心机制就是，当web页面刷新，代码就会从头跑一遍，就会造成无法记录当前状态的问题
因此需要借助自带的组件sessionstate来进行记录
"""
import time

import streamlit as st
from knowledge_base import KnowledgeBaseService

# 添加网页标题
st.title("知识库更新服务")

# 添加网页上传的提示框
uploader_file = st.file_uploader(
    label="请上传txt文件",
    type=['txt'],
    accept_multiple_files=False     # 是否允许一次性上传多个文件
)

# 如果这么写每次上传文件或者web发生变化就会重新载入，浪费资源，所以要用sessionstate来记录
# service = KnowledgeBaseService()


if "service" not in st.session_state:
    # 这样后面就可以通过st.session_state["service"]直接调用类对象完成存入向量库的操作
    st.session_state["service"] = KnowledgeBaseService()


if uploader_file is not None:
    # 提取文件的信息
    file_name = uploader_file.name
    file_type = uploader_file.type
    file_size = uploader_file.size/1024         # 变成KB
    # 字标题
    st.subheader(f"文件名：{file_name}")
    st.write(f"格式：{file_type} | 大小：{file_size: .2f}KB")

    # 获取文件中的内容，get value得到的是字节bytes，所以要转成字符串。用decode（‘tuf8’）
    text = uploader_file.getvalue().decode('utf-8')

    with st.spinner("正在存入知识库中。。。"):
        time.sleep(1)
        res = st.session_state["service"].upload_by_str(text, file_name)
        st.write(res)
