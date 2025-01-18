import requests
import sys
import os
import pandas as pd
from dotenv import load_dotenv
import csv

def process_response_data(response_data, results_df):
    for item in response_data.get('data', []):
        filename = item.get('originalFileName', 'N/A')
        overall_status = item["resultsSummary"].get('status', 'N/A')
        score = item["resultsSummary"].get('metadata', {}).get('finalScore', 'N/A')

        # Append the data to the DataFrame
        results_df = pd.concat([results_df, pd.DataFrame([{
            'file_name': filename,
            'status': overall_status,
            'score': score
        }])], ignore_index=True)
    return results_df

def fetch_data_from_api(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_media_detail(request_id, token, results_df):
    page_index = 1
    headers = {"x-api-key": token, "Content-Type": "application/json"}
    url = f"https://api.prd.realitydefender.xyz/api/media/users/{request_id}?pageIndex={page_index}"
    
    if request_id == "":
        while True:
            print(f"getting page {page_index}")
            
            response_data = fetch_data_from_api(url, headers)
            if response_data is None or not response_data.get('data'):
                print(f"No data found for page {page_index}. Skipping.")
                page_index += 1
                continue

            results_df = process_response_data(response_data, results_df)

            total_pages = response_data.get('totalPages', 1)

            if page_index >= total_pages:
                break
            page_index += 1
            
    else:
        response_data = fetch_data_from_api(url, headers)
        print(f"fetching {request_id}")
        if response_data:
            results_df = process_response_data({'data': [response_data]}, results_df)
    
    return results_df

if __name__ == "__main__":
    load_dotenv()
    token = os.getenv("RD_API")
    results_df = pd.DataFrame(columns=['file_name', 'status', 'score'])

    if len(sys.argv) > 2:
        print("Usage: python sample_get_script.py <csv_file_path_or_empty_to_get_all_media>")
        sys.exit(1)
    elif len(sys.argv) == 1:
        request_id = ""
        results_df = get_media_detail(request_id, token, results_df)
        results_df.to_csv('results.csv', index=False)
        print("Results saved to results.csv")
    else:
        csv_file_path = sys.argv[1]
        try:
            # Load the CSV into a DataFrame
            df = pd.read_csv(csv_file_path)

            # Validate that the required columns are present
            required_columns = {'file_name', 'request_id'}
            if not required_columns.issubset(df.columns):
                print(f"Error: CSV file must contain the columns: {', '.join(required_columns)}")
                sys.exit(1)

            # Iterate over each row in the DataFrame
            for _, row in df.iterrows():
                request_id = row.get('request_id', '')
                if request_id:
                    results_df = get_media_detail(request_id, token, results_df)
            merged_df = pd.merge(df, results_df, on='file_name', how='left')
            merged_df.to_csv('results.csv', index=False)
            print("Results saved to results.csv")
        except FileNotFoundError:
            print(f"Error: File {csv_file_path} not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
