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


# Get OpenAI API key from .env or environment
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.warning("OpenAI API key not found in environment variables or .env file.")
    st.stop()

# Set up LangChain LLM
llm = OpenAI(openai_api_key=openai_api_key, temperature=0.2)


# Get Google API key and CX from .env or environment
google_api_key = os.getenv("GOOGLE_API_KEY")
google_cx = os.getenv("GOOGLE_CSE_ID")
if not google_api_key or not google_cx:
    st.warning("Google API key or Custom Search CX not found in environment variables or .env file.")
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
st.markdown(
    "*If you want to know who represents the Left or Right, ask [@BTurtel](https://x.com/messages/compose?recipient_id=BTurtel) on X.*",
    unsafe_allow_html=True
)

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

    st.subheader(f"Found {len(events)} Recent Events")

    # Prepare data for table
    table_data = []
    for i, (event, left_res, right_res) in enumerate(zip(events, left_results, right_results)):
        left_icon = "✔️" if "yes" in left_res.lower() else "❌"
        right_icon = "✔️" if "yes" in right_res.lower() else "❌"
        table_data.append({
            "Left Condemned?": left_icon,
            "Event Description": event,
            "Right Condemned?": right_icon
        })

    # Display as a table
    import pandas as pd
    df = pd.DataFrame(table_data)
    st.table(df)
