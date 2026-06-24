
import time

import streamlit as st
from agent.react_agent import ReactAgent

#标题
st.title("高考/考研志愿报名智能体")
st.divider()    #分隔符


if "agent" not in st.session_state:
    st.session_state["agent"]=ReactAgent()

if "message" not in st.session_state:
    st.session_state["message"]=[]

for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])


#要求用户输入提示词
prompt=st.chat_input()

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role":"user","content":prompt})
    
    response_messages=[]
    with st.spinner("thinking..."):
        res_stream=st.session_state["agent"].execute_stream(prompt)
        
        def caputer(generator,cache_list):
            for chunk in generator:
                cache_list.append(chunk)
                
                for char in chunk:
                    time.sleep(0.01)
                    yield char
        
        st.chat_message("assistant").write_stream(caputer(res_stream,response_messages))
        st.session_state["message"].append({"role":"assistant","content":response_messages[-1]}) 
        st.rerun()