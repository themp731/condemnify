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

# Agent 1: Find recent acts of violence, extremism, criminality, or misdeeds in the US
def find_recent_events():
    query = "recent acts of violence, extremism, or criminality in the United States"
    results = search.run(query)
    # For demo, just return the top 10 results as events
    return results.split("\n")[:10]

def truncate_to_100_words(text):
    """Truncate text to maximum 100 words"""
    if not text:
        return text
    words = text.split()
    if len(words) <= 100:
        return text
    return " ".join(words[:100]) + "..."

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
        with st.spinner(f"Checking condemnation for: {event}"):
            left = check_condemnation(event, "left")
            right = check_condemnation(event, "right")
            left_results.append(left)
            right_results.append(right)
    
    # Display results in table format with multiple rows
    st.subheader("Recent Events and Condemnation Status")
    
    for i, (event, left_res, right_res) in enumerate(zip(events, left_results, right_results)):
        # Create a container for each row
        with st.container():
            # Create three columns for each event row
            col1, col2, col3 = st.columns([2, 4, 2])
            
            with col1:
                if i == 0:  # Only show header for first row
                    st.markdown("**Left Condemned?**")
                left_icon = "✔️" if "yes" in left_res.lower() else "❌"
                st.write(f"{left_icon}")
                with st.expander("Details"):
                    st.caption(left_res)
            
            with col2:
                if i == 0:  # Only show header for first row
                    st.markdown("**Event Description**")
                truncated_event = truncate_to_100_words(event)
                st.write(truncated_event)
            
            with col3:
                if i == 0:  # Only show header for first row
                    st.markdown("**Right Condemned?**")
                right_icon = "✔️" if "yes" in right_res.lower() else "❌"
                st.write(f"{right_icon}")
                with st.expander("Details"):
                    st.caption(right_res)
        
        # Add a divider between rows (except for the last row)
        if i < len(events) - 1:
            st.divider()

st.info("To deploy on Elastic Beanstalk, make sure to set your API keys as environment variables or use the sidebar inputs.")
