import time
from RAG import RagService
import streamlit as st
import config_data as config

# 标题
st.title("智能客服")
st.divider()        # 分隔符

if "message" not in st.session_state:
    st.session_state["message"] = [{"role": "assistant", "content": "你好有什么可以帮助你？"}]

if "rag" not in st.session_state:
    st.session_state["rag"] = RagService()

# 把历史的记录都打印到界面
for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])

# 在页面最下方提供用户输入栏
prompt = st.chat_input()

if prompt:
    # 在页面输出用户提问
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role": "user", "content": prompt})

    ai_res_list = []
    with st.spinner("AI思考中。。。。"):
        res_stream = st.session_state["rag"].chain.stream({"input": prompt}, config.session_config)

        # 只是抓取流然后再原封不动的返回，这期间把这个流存成list就能变成一个整体给最下面的content
        def capture(stream_chunk, total_list):
            for chunk in stream_chunk:
                total_list.append(chunk)
                yield chunk

        st.chat_message("assistant").write_stream(capture(res_stream, ai_res_list))
        # 加到页面的历史记录，但是上面改成流式输出之后就没法把res_stream放到下面的content中，
        # 因为它要的是字符串，而不是一个个段，这时就需要用到抓包来处理
        # ["a","b","c"]  -> "".join(list)  -> abc，用空字符串join就是把列表中的内容拼成abc
        # ["a","b","c"]  -> ",".join(list)  -> abc，用,来join就是把列表中的内容拼成a,b,c
        st.session_state["message"].append({"role": "assistant", "content": "".join(ai_res_list)})
