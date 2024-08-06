
import pandas as pd
import numpy as np
import openai
from openai import OpenAI
import requests
import os
from dotenv import load_dotenv, dotenv_values 

client = OpenAI(api_key=(os.getenv("CHATGPT_APIKEY")))

def update_chat(messages, role, content):
  messages.append({"role": role, "content": content})
  return messages

chat_prompt = "Based on the following purchases grouped that is sorted from greatest to least {sorted_df} and persona description provided to you {persona}, generate a personalized response. The answer provided should give specific carbon footprint or environmental-based quantitative data for the user. Recommended action to take should also be incorporated, identifying the risks behind current actions or benefits of current good actions, and more motivating language and specific actions to help improve ecological standing. Do not user markdown formatting, * or #. NO numbered lists or bullet points, ONLY paragraph. Use 30-50 words, 50 words MAX."
messages=[
            {"role": "user", "content": chat_prompt}
]

def get_chatgpt_response(messages):
    chat_completion = client.chat.completions.create(
        messages = messages,
        model="gpt-4",
        temperature=0
    )
    return chat_completion.choices[0].message.content


