import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv, dotenv_values 

CREDENTIALS_FILE = os.getenv('CREDENTIALS')
SPREADSHEET_ID = os.getenv('SPREADHSHEET_ID')

WORKSHEET_NAME = os.getenv('WORKSHEET_NAME')
csv_path = os.getenv("CSV_URL")
LOCAL_CSV_FILE = csv_path

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
client = gspread.authorize(creds)

def update_csv():
    sheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = sheet.worksheet(WORKSHEET_NAME)
    
    data = worksheet.get_all_values()
    
    df = pd.DataFrame(data[1:], columns=data[0])
    
    try:
        local_df = pd.read_csv(LOCAL_CSV_FILE)
    except FileNotFoundError:
        local_df = pd.DataFrame(columns=df.columns)

    updated_df = pd.concat([local_df, df], ignore_index=True).drop_duplicates()
    
    updated_df.to_csv(LOCAL_CSV_FILE, index=False)

