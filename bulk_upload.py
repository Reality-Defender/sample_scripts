import requests
import pandas as pd
import os 
import sys
import time
from dotenv import load_dotenv

load_dotenv()

# This function gets a pre-signed url that you can post a file to
def get_signed_url(file_name, token, retries=3, delay=2):
    url = "https://api.prd.realitydefender.xyz/api/files/aws-presigned"
    # Extract just the filename from the full path if given
    file_name = os.path.basename(file_name)
    payload = {
        "fileName": file_name
    }
    headers = {"X-API-KEY": token, "Content-Type": "application/json"}
    
    for attempt in range(retries):
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                # print("Response from get_signed_url:", response_data)
                return response_data
            except ValueError:
                print("Error: Response is not in JSON format")
                return None
        else:
            print(f"Error: Received status code {response.status_code}")
            print("Response content:", response.text)
            if response.status_code == 502:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                return None
    print("Max retries reached. Exiting.")
    return None

# This function uploads the file to the pre-signed url you received in the prior function
def upload_file(file_path, token, signed_url):
    with open(file_path, 'rb') as file:
        file_data = file.read()
    
    try:
        response = requests.put(signed_url, data=file_data, timeout=20)
        response.raise_for_status()
        print('File upload successful! ' + os.path.basename(file_path))
        return response
    except requests.exceptions.Timeout:
        print(f'File upload failed: The request timed out after 20 seconds for file {os.path.basename(file_path)}')
    except requests.exceptions.RequestException as e:
        print(f'File upload failed with error: {e}')
    
if __name__ == "__main__":
    # Get RD_API key from environment variables (must be included in .env file)
    token = os.getenv("RD_API")

    # Accepts a file path or directory path from the command line
    if len(sys.argv) != 2:
        print("Usage: python bulk_upload.py <directory_path>")
        sys.exit(1)

    path = sys.argv[1]

    # Create a dataframe to store file names and request IDs
    results_df = pd.DataFrame(columns=['file_name', 'request_id', 'file_path'])

    if os.path.isfile(path):
        response = get_signed_url(path, token)
        if "response" in response:
            signed_url = response["response"].get("signedUrl")
            request_id = upload_file(path, token, signed_url).get("requestId")
        else:
            print("Error: Invalid response structure or failed to get signed URL.")
    elif os.path.isdir(path):
        # Walk through the file structure and upload files
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                response_data = get_signed_url(file, token)
                if "response" in response_data:
                    signed_url = response_data["response"].get("signedUrl")
                    request_id = upload_file(file_path, token, signed_url).get("requestId")
                    # Append file name and request ID to results dataframe
                    results_df.loc[len(results_df)] = [file, request_id, file_path]
                else:
                    print(f"Error: Invalid response structure or failed to get signed URL for file {file}.")
        # Save results to CSV file
        results_df.to_csv('uploads.csv', index=False)
        print("Results saved to uploads.csv")
    else:
        print(f"Error: {path} is not a valid file or directory.")
        sys.exit(1)
