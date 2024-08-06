import time
import pandas as pd
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
import analyze
import os
from dotenv import load_dotenv, dotenv_values 

class CSVHandler(FileSystemEventHandler):
    def __init__(self, csv_path, user_data):
        self.csv_path = os.path.abspath(csv_path)
        self.user_data = user_data
        self.previous_entries = pd.read_csv(self.csv_path).shape[0]
        print(f"Initial number of entries: {self.previous_entries}")
        print(f"Monitoring file: {self.csv_path}")
        self.process_initial_entries()

    def process_initial_entries(self):
        df = pd.read_csv(self.csv_path)
        unique_users = df["cluster_name_adjusted"].unique()
        for unique_username in unique_users:
            print(f"Processing initial entry for user_id: {unique_username}")
            data = analyze.analyze_new_entry(df, unique_username)
            self.user_data[unique_username] = data
            self.send_data_to_flask(unique_username, data)
        self.previous_entries = df.shape[0]

    def on_any_event(self, event):
        print(f"Event detected: {event.event_type} - {event.src_path}")
        if event.event_type == 'modified' and os.path.abspath(event.src_path) == self.csv_path:
            print("CSV file modified.")
            self.process_new_entries()

    def process_new_entries(self):
        df = pd.read_csv(self.csv_path)
        new_entries = df.iloc[self.previous_entries:]
        self.previous_entries = df.shape[0]
        for index, row in new_entries.iterrows():
            print(f"New entry: {row.to_dict()}")  

        if not new_entries.empty:
            print("Processing new entries.")
            user_persona = new_entries["cluster_name_adjusted"].values[0]
            results_to_inject = analyze.analyze_new_entry(df, user_persona)
            print("NEW ENTRY RESULTS")
            print(results_to_inject)
            self.user_data[user_persona] = results_to_inject
            self.send_data_to_flask(user_persona, results_to_inject)
        else:
            print("No new entries!")

    def send_data_to_flask(self, user_id, data):
        url_id = ''.join(user_id.split()).lower()
        url = f"http://localhost:5000/user/{url_id}"
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"Successfully sent data for user: {user_id}")
        else:
            print(f"Failed to send data for user: {user_id}, status code: {response.status_code}")

def monitor_csv(csv_path, user_data):
    event_handler = CSVHandler(csv_path, user_data)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(csv_path), recursive=False)
    observer.start()
    print("Started monitoring the CSV file.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("Stopped monitoring.")
    observer.join()
