import pandas as pd
import numpy as np
import openai
from openai import OpenAI
import requests
import re
import os
from dotenv import load_dotenv, dotenv_values 

def to_camel_case(s):
    return re.sub(r'(_|-|\s)+(.)', lambda m: m.group(2).upper(), s.lower())

def generate_html_content(data):
    items = []
    for entry in data:
        category_camel_case = to_camel_case(entry['Category'])
        carbon_footprint = entry['Carbon Footprint']
        items.append(f"<li>In the category of {category_camel_case}, your carbon footprint is {carbon_footprint}.</li>")
    
    html_content = "<ul>" + "\n".join(items) + "</ul>"
    return html_content

def generate_gpt_response(client, sorted_df, max_exp, max_foot, persona):
    prompt = f"Based on the following purchases grouped that is sorted from greatest to least {sorted_df}, the carbon footprints for these purchases {max_exp}, the purchases the user has the most carbon footprint in {max_foot}, and persona description provided to you {persona}, generate a personalized response. The answer provided should give specific carbon footprint or environmental-based quantitative data for the user. Recommended action to take should also be incorporated, identifying the risks behind current actions or benefits of current good actions, and more motivating language and specific actions to help improve ecological standing. Do not user markdown formatting, * or #. NO numbered lists or bullet points, ONLY paragraph. Use 30-50 words, 50 words MAX."
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="gpt-4",
        temperature=0
    )
    return chat_completion.choices[0].message.content

def calculate_carbon_footprint(activity_id, amount):

    api_key = os.getenv("CLIMATIQ_APIKEY")

    url = "https://api.climatiq.io/data/v1/estimate"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    search_url = "https://api.climatiq.io/data/v1/search"
    
    payload = {
        "emission_factor": {
            "activity_id": activity_id,
            "data_version": "14.14"  # Ensure this is the latest version
        },
        "parameters": {
            "money": amount,
            "money_unit": "usd"
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json().get("co2e", 0)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if response is not None and response.content:
            try:
                error_details = response.json()
                print(f"Error: {error_details.get('error')}")
                print(f"Error Code: {error_details.get('error_code')}")
                print(f"Message: {error_details.get('message')}")
                print(f"Valid Values: {error_details.get('valid_values')}")
            except ValueError:
                print(f"Response content: {response.content.decode('utf-8')}")
        return 0


def carbon_footprint_data(sorted_df):
    expenditure_data = [
        {'category': 'GROCERY STORES/SUPERMARKETS', 'activity_id': 'consumer_goods-type_supermarkets_and_other_grocery_except_convenience_stores', 'amount_spent': 1957.82},
        {'category': 'RESTAURANTS', 'activity_id': 'consumer_goods-type_restaurant_meals', 'amount_spent': 729.6800000000001},
        {'category': 'BARS/TAVERNS/LOUNGES/DISCOS', 'activity_id': 'metals-type_steel_rebar', 'amount_spent': 590.57},
        {'category': 'LOCAL COMMUTER TRANSPORT', 'activity_id': 'passenger_train-route_type_urban-fuel_source_electric', 'amount_spent': 586.62},
        {'category': 'MISC SPECIALTY RETAIL', 'activity_id': 'general_retail-type_all_other_retail', 'amount_spent': 476.46},
        {'category': 'MISC FOOD STORES - DEFAULT', 'activity_id': 'consumer_goods-type_all_other_specialty_food_stores', 'amount_spent': 341.27},
        {'category': 'BANDS/ORCHESTRAS/ENTERTAIN', 'activity_id': 'consumer_goods-type_creative_arts_and_entertainment_services', 'amount_spent': 163.29999999999998},
        {'category': 'DIGITAL GOODS BOOKSMOVIEMUSIC', 'activity_id': 'consumer_goods-type_digital_imports_to_households', 'amount_spent': 115.33},
        {'category': 'THEATRICAL PRODUCERS', 'activity_id': 'consumer_goods-type_theater_companies_and_dinner_theaters', 'amount_spent': 114.64},
        {'category': 'NURSERIES, LAWN/GARDEN SUPPLY', 'activity_id': 'equipment_gardening_diy-type_nursery_garden_center_and_farm_supply_stores', 'amount_spent': 51.75},
        {'category': 'PARKING LOTS,METERS,GARAGES', 'activity_id': 'domestic_services-type_parking_lots_and_garages', 'amount_spent': 40.77},
        {'category': 'CONTINUITY/SUBSCRIPTION MERCHT', 'activity_id': 'consumer_goods-type_cable_subscription_programming', 'amount_spent': 38.239999999999995},
        {'category': 'LARGE DIGITAL GOODS MERCHANT', 'activity_id': 'consumer_goods-type_digital_imports_to_households', 'amount_spent': 26.3},
        {'category': 'BAKERIES', 'activity_id': 'consumer_goods-type_bakery_and_farinaceous_products', 'amount_spent': 18.33},
        {'category': 'BUSINESS SERVICES - DEFAULT', 'activity_id': 'consumer_services-type_other_business_services', 'amount_spent': 5.24}
    ]
    
    
    expenditure_dict = {item['category'].lower(): {'activity_id': item['activity_id'], 'amount_spent': item['amount_spent']} for item in expenditure_data}

    for category_from_df, amount_spent_df in sorted_df.items():
        if(category_from_df.lower() in expenditure_dict.keys()):
            expenditure_dict[category_from_df.lower()]['amount_spent'] = int(amount_spent_df)
        
    sorted_expenditure = sorted(expenditure_dict.items(), key=lambda x: x[1]['amount_spent'], reverse=True)

    
    footprint_results = []
    total_carbon_footprint = 0
    counter = 0
    for index, item in sorted_expenditure:
        money_amount = item["amount_spent"] 
        carbon_footprint = calculate_carbon_footprint(item["activity_id"], money_amount)
        
        total_carbon_footprint += carbon_footprint
        footprint_results.append({"Category": index, "Carbon Footprint": int(carbon_footprint)})
        counter += 1
        
    max_expenditures = footprint_results[:5]
    max_footprints = sorted(footprint_results, key=lambda x: x["Carbon Footprint"], reverse=True)
    max_footprints = max_footprints[:5]
    
    return (max_expenditures, max_footprints)

def json_to_string(json_object):
    result_string = ""
    for item in json_object:
        result_string += f"Category: {item['Category'].lower()}, Carbon Footprint: {item['Carbon Footprint']}\n"
    return result_string.strip()

def analyze_new_entry(df, cluster_name):
    
    filtered_df = df[df['cluster_name_adjusted'] == cluster_name]
    grouped_df = filtered_df.groupby('mrch_catg_rlup_nm')['spend'].sum()
    sorted_df = grouped_df.sort_values(ascending=False)
    sorted_dict = sorted_df.to_dict()
    print(sorted_dict)

    
    (max_expenditures, max_footprints) = carbon_footprint_data(sorted_df)

    
    client = OpenAI(api_key=(os.getenv("CHATGPT_APIKEY")))
    chat_suggestion = generate_gpt_response(client, sorted_df, max_footprints, max_expenditures, cluster_name)
    
    
    return {
        "user_id": cluster_name,
        "gpt_response": chat_suggestion,
        "max_expenditures": max_expenditures, 
        "max_footprints": max_footprints
    }

