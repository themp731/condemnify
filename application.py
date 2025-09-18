import os
import streamlit as st
import os

# Ensure Streamlit listens on the correct port and address for Elastic Beanstalk
if 'PORT' in os.environ:
    port = int(os.environ['PORT'])
else:
    port = 8000
os.environ['STREAMLIT_SERVER_PORT'] = str(port)
os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
from langchain.agents import initialize_agent, Tool
from langchain_community.llms import OpenAI
from langchain_community.utilities import GoogleSearchAPIWrapper
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

st.set_page_config(page_title="Condemnify", layout="wide")
st.title("Condemnify: Who Condemned It?")

# Get OpenAI API key from .env or sidebar
openai_api_key = os.getenv("OPENAI_API_KEY") or st.sidebar.text_input("Enter your OpenAI API Key", type="password")
if not openai_api_key:
    st.warning("Please enter your OpenAI API key in the sidebar or .env file.")
    st.stop()

# Set up LangChain LLM
llm = OpenAI(openai_api_key=openai_api_key, temperature=0.2)

# Get Google API key and CX from .env or sidebar
google_api_key = os.getenv("GOOGLE_API_KEY") or st.sidebar.text_input("Google API Key", type="password")
google_cx = os.getenv("GOOGLE_CSE_ID") or st.sidebar.text_input("Google Custom Search CX")
if not google_api_key or not google_cx:
    st.warning("Please enter your Google API Key and CX in the sidebar or .env file.")
    st.stop()

search = GoogleSearchAPIWrapper(google_api_key=google_api_key, google_cse_id=google_cx)

# Helper function to truncate text to 100 words
def truncate_to_words(text, max_words=100):
    words = text.split()
    if len(words) <= max_words:
        return text
    return ' '.join(words[:max_words]) + '...'

# Agent 1: Find recent acts of violence, extremism, criminality, or misdeeds in the US
def find_recent_events():
    query = "recent acts of violence, extremism, or criminality in the United States"
    results = search.run(query)
    # Return the top 10 results as events and truncate each to 100 words
    events = results.split("\n")[:10]
    return [truncate_to_words(event) for event in events if event.strip()]

# Agent 2: For each event, check if the Left or Right condemned it
def check_condemnation(event, side):
    # side: "left" or "right"
    query = f"Did {side} wing leaders condemn {event}?"
    result = search.run(query)
    # Use LLM to summarize if condemnation is found
    prompt = f"Based on the following search result, did the {side} condemn the event '{event}'? Answer 'yes' or 'no' and provide a short explanation.\nSearch result: {result}"
    answer = llm(prompt)
    return answer

# Main app logic
st.write("This app shows whether leadership from the Left or Right has condemned recent acts of violence or misdeeds in the US.")

if st.button("Find Recent Events"):
    events = find_recent_events()
    left_results = []
    right_results = []
    for event in events:
        with st.spinner(f"Checking condemnation for: {event[:50]}..."):
            left = check_condemnation(event, "left")
            right = check_condemnation(event, "right")
            left_results.append(left)
            right_results.append(right)
    
    # Display results in a table-like format with proper row separation
    st.subheader(f"Found {len(events)} Recent Events")
    
    # Create header row
    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        st.write("**Left Condemned?**")
    with col2:
        st.write("**Event Description**")
    with col3:
        st.write("**Right Condemned?**")
    
    st.divider()
    
    # Display each event as a row
    for i, (event, left_res, right_res) in enumerate(zip(events, left_results, right_results)):
        col1, col2, col3 = st.columns([1,2,1])
        with col1:
            st.write("✔️" if "yes" in left_res.lower() else "❌")
            with st.expander("Details"):
                st.caption(left_res)
        with col2:
            st.write(f"**Event {i+1}:** {event}")
        with col3:
            st.write("✔️" if "yes" in right_res.lower() else "❌")
            with st.expander("Details"):
                st.caption(right_res)
        
        if i < len(events) - 1:  # Don't add divider after last row
            st.divider()

st.info("To deploy on Elastic Beanstalk, make sure to set your API keys as environment variables or use the sidebar inputs.")
