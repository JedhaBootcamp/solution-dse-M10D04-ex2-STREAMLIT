import streamlit as st
from langgraph_sdk import get_sync_client # It's important to use get_sync_client to have a SYNCHRONOUS client. Otherwise the app won't work

# Streamlit application layout
st.title("Orange Customer Success Chatbot")
st.write("Welcome! I’m here to help you with your inquiries about Orange's products and services. How can I assist you today?")

# Store conversation history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi, I'm here to help you with Orange's products and services. How can I assist you today?"}]

# Function to clear the chat history
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "Hi, I'm here to help you with Orange's products and services. How can I assist you today?"}]

st.sidebar.button("Clear chat history", on_click=clear_chat_history)

# Display past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Initialize LangGraph client
remote_url = "REPLACE_WITH_YOUR_LIGHTNING_API_STUDIO_API"  # REPLACE WITH YOUR LIGHTNING AI STUDIO API 
sync_client = get_sync_client(url=remote_url, api_key="REPLACE_WITH_YOUR_API_KEY")


# We are going to define a function for streaming the output 
# because we want to be able to use a specific st.write_steam method from steamlit 
# that takes a generator as parameter which can only be done inside a function 
# Especially if we need to have a custom logic for handling streaming tokens 
# like we have below (read inside the function for more details)
def stream_answer(assistant_id, thread, payload):
    
    # This is the streamer 
    generator = sync_client.runs.stream(
        thread["thread_id"],
        assistant_id,
        input=payload,
        stream_mode="messages", # This part is important
    )

    # Below is the logic for handling each token generated 
    # By default `chunk` will contain all previous tokens + the newest token 
    # Meaning if you `print(chunk.data)` you will see 
    # token 1 
    # token 1 | token 2 
    # token 1 | token 2 | token 3
    # token 1 | token 2 | token 3 | token 4
    # [...]
    # What we want is to generate 
    # token 1 | token 2 | token 3 | token 4 [...]
    # To do so we need to handle with a custom logic 
    # that you see after the "else" statement
    seen_text=""
    for chunk in generator:
        if isinstance(chunk.data, dict):
            # Ignore dictionary-based chunks as they're meta-information
            continue
        else:
            # Extract the latest token
            new_content = chunk.data[-1]["content"]
            new_part = new_content[len(seen_text):] 
            
            # yield outputs each new token one by one as they are generated from the LLM
            yield new_part

            # Update the seen content
            seen_text = new_content

# User input
# This will be generated in the streamlit app whenever the user provide a prompt
if prompt := st.chat_input():

    # This st.session_state.messages will keep a history of messages while 
    # user is still in the current session. 
    # Whenever a user will refresh the page or leave it for too long 
    # the session will be reset
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Placeholder for assistant's streaming response
    assistant_message_placeholder = st.chat_message("assistant")
    
    # Create a new thread for the conversation
    user_input_payload = {"messages": [{"role": "user", "content": prompt}]}

    # This will create a new thread each time the program will be rerun.
    # You will need to implement more custom logic if you wanted to retrieve a past thread 
    thread = sync_client.threads.create()

    # This is a cool feature from streamlit that streams answer of a given function
    response = st.write_stream(stream_answer(assistant_id="agent", thread=thread, payload=user_input_payload))

    # Once the response has been fully generated we will append it to look more like a real "chatGPT-like conversation"
    st.session_state.messages.append({"role": "assistant", "content": response})
