import requests
import sys
import os
import pandas as pd
from dotenv import load_dotenv
import csv
import argparse

def process_response_data(request_id, response_data, results_df):
    data = response_data.get("mediaList") or response_data.get("data") or []
    for item in data:
        results_summary = item.get("resultsSummary", {})
        
        overall_status = results_summary.get('status', 'UNABLE_TO_EVALUATE') if results_summary else 'UNABLE_TO_EVALUATE'
        score = results_summary.get('metadata', {}).get('finalScore', '') if results_summary else ''

        # Append the data to the DataFrame
        results_df = pd.concat([results_df, pd.DataFrame([{
            'file_name': item.get('originalFileName', ''),
            'request_id': request_id if request_id else item.get('requestId', ''),
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

def get_media_detail(request_id, token, results_df, include_all_users=False):
    page_index = 0
    headers = {"x-api-key": token, "Content-Type": "application/json"}
    
    if request_id == "":
        while True:
            url = (f"https://api.dev.realitydefender.xyz/api/v2/media/users/pages/{page_index}?userIds=[]" 
                  if include_all_users 
                  else f"https://api.dev.realitydefender.xyz/api/v2/media/users/pages/{page_index}")
            print(f"getting page {page_index}")
            
            response_data = fetch_data_from_api(url, headers)
            if response_data is None:
                print(f"Error fetching page {page_index}. Stopping.")
                break
                
            if not response_data.get('mediaList'):
                print(f"No data found for page {page_index}. Stopping.")
                break

            results_df = process_response_data(request_id, response_data, results_df)

            total_pages = response_data.get('totalPages', 0)
            
            if page_index >= total_pages:
                break
            page_index += 1
            
    else:
        url = f"https://api.dev.realitydefender.xyz/api/media/users/{request_id}"
        response_data = fetch_data_from_api(url, headers)
        print(f"fetching {request_id}")
        if response_data:
            results_df = process_response_data(request_id, {'data': [response_data]}, results_df)
    
    return results_df

if __name__ == "__main__":
    load_dotenv()
    token = os.getenv("RD_API")
    results_df = pd.DataFrame(columns=['file_name', 'request_id', 'status', 'score'])

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Fetch media details from Reality Defender API')
    parser.add_argument('--get-all', action='store_true', help='Get media details for all users')
    parser.add_argument('csv_file', nargs='?', default=None, help='Path to CSV file containing request IDs')
    
    args = parser.parse_args()

    if args.csv_file:
        try:
            # Load the CSV into a DataFrame
            df = pd.read_csv(args.csv_file)

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
            merged_df = pd.merge(df, results_df, on='request_id', how='left')
            merged_df.to_csv('results.csv', index=False)
            print("Results saved to results.csv")
        except FileNotFoundError:
            print(f"Error: File {args.csv_file} not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        request_id = ""
        results_df = get_media_detail(request_id, token, results_df, include_all_users=args.get_all)
        results_df.to_csv('results.csv', index=False)
        print("Results saved to results.csv")
