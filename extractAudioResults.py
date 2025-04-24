import requests
import sys
import os
import pandas as pd
from dotenv import load_dotenv
import csv

def process_response_data(video_request_id, audio_request_id, response_data, results_df):
    for item in response_data.get('data', []):
        overall_status = item["resultsSummary"].get('status', 'N/A')
        score = item["resultsSummary"].get('metadata', {}).get('finalScore', 'N/A')

        # Append the data to the DataFrame
        results_df = pd.concat([results_df, pd.DataFrame([{
            'video_request_id': video_request_id,
            'audio_request_id': audio_request_id,
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

def get_audio_request_id(video_request_id, token):
    headers = {"x-api-key": token, "Content-Type": "application/json"}
    try:
        response = requests.get(f"https://api.prd.realitydefender.xyz/api/media/users/{video_request_id}", headers=headers)
        response.raise_for_status()
        return response.json().get('audioRequestId')
    except requests.exceptions.RequestException as e:
        print(f'Error getting audio request ID: {e}')
        return None

def enable_audio_results(audio_request_id, video_request_id, token):
    headers = {"x-api-key": token, "Content-Type": "application/json"}
    payload = {
        "audioRequestId": audio_request_id,
        "videoRequestId": video_request_id
    }
    try:
        response = requests.post("https://api.prd.realitydefender.xyz/api/files/show-audio-result/", 
                               headers=headers,
                               json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        if hasattr(e.response, 'text'):
            print(f'Error response: {e.response.text}')
        return False

def get_media_detail(video_request_id, token, results_df):
    # First get the audio request ID
    audio_request_id = get_audio_request_id(video_request_id, token)
    if not audio_request_id:
        print(f"Could not get audio request ID for video request ID: {video_request_id}")
        return results_df

    # Enable audio results before fetching details
    if not enable_audio_results(audio_request_id, video_request_id, token):
        print(f"Could not enable audio results for audio request ID: {audio_request_id}")
        return results_df

    page_index = 1
    headers = {"x-api-key": token, "Content-Type": "application/json"}
    url = f"https://api.prd.realitydefender.xyz/api/media/users/{audio_request_id}?pageIndex={page_index}"
    
    if audio_request_id == "":
        while True:
            print(f"getting page {page_index}")
            
            response_data = fetch_data_from_api(url, headers)
            if response_data is None or not response_data.get('data'):
                print(f"No data found for page {page_index}. Skipping.")
                page_index += 1
                continue

            results_df = process_response_data(video_request_id, audio_request_id, response_data, results_df)

            total_pages = response_data.get('totalPages', 1)

            if page_index >= total_pages:
                break
            page_index += 1
            
    else:
        response_data = fetch_data_from_api(url, headers)
        print(f"fetching audio request ID: {audio_request_id}")
        if response_data:
            results_df = process_response_data(video_request_id, audio_request_id, {'data': [response_data]}, results_df)
    
    return results_df

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extractAudioResults.py <csv_file_path>")
        sys.exit(1)

    load_dotenv()
    token = os.getenv("RD_API")
    results_df = pd.DataFrame(columns=['video_request_id', 'audio_request_id', 'status', 'score'])
    csv_file_path = sys.argv[1]

    try:
        # Load the CSV into a DataFrame
        df = pd.read_csv(csv_file_path)

        # Validate that the requestId column is present
        if 'requestId' not in df.columns:
            print("Error: CSV file must contain a 'requestId' column")
            sys.exit(1)

        # Iterate over each row in the DataFrame
        for _, row in df.iterrows():
            video_request_id = row['requestId']
            if video_request_id:
                results_df = get_media_detail(video_request_id, token, results_df)

        # Merge the results with the original DataFrame
        merged_df = pd.merge(df, results_df, left_on='requestId', right_on='video_request_id', how='left')
        merged_df.to_csv('results.csv', index=False)
        print("Results saved to results.csv")
    except FileNotFoundError:
        print(f"Error: File {csv_file_path} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
