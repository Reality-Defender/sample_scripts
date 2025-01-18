# sample_scripts

## Setup
- Login to your Reality Defender web application and generate an API key
- The API key needs to be added to your .env file in the following format: `RD_API={api-key}`
- The necessary requirements are included in requirements.txt and can be installed using the `pip install -r requirements.txt` terminal command

## bulk_upload.py
This script bulk uploads files from a local directory to Reality Defender API. 
`Usage: python bulk_upload.py <directory_path>`

Accepted Inputs:
- Directory path or file path. If directory path is provided, the script will traverse the directory and upload every file. If file path is provided, the script will only upload that file. 

Outputs:
- Intermediate results are saved in uploads.csv. This includes the file_name, file_path, and reqeust_id from Reality Defender. You can use this CSV as an input into the `get_results.py` script. 

> **Notice:**  
> After completing the upload process, it is advisable to wait for several minutes to ensure all files have been processed by Reality Defender before proceeding with the next script. For production environments, Reality Defender provides a webhook as an alternative to waiting or polling.

## get_results.py
This script bulk downloads results from the Reality Defender API. 

Accepted Inputs:
- CSV file containing the file_name and request_id. Those two columns must be contained in the CSV
- No input. The script will automatically bulk download all the results from your account. 

Outputs:
- Results will be stored in results.csv. If a CSV was included as an input, that CSV will be merged with the results and all columns contained in the CSV will also appear in results.csv.

