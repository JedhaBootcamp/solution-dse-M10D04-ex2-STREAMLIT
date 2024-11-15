FROM continuumio/miniconda3

WORKDIR /home/app 

RUN pip install streamlit requests pandas numpy langserve langgraph langgraph_sdk

CMD ["bash"]