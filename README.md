# sample_scripts

## Setup
- Login to your Reality Defender web application and generate an API key
- The API key needs to be added to your .env file in the following format: `RD_API={api-key}`
- The necessary requirements are included in requirements.txt and can be installed using the `pip install -r requirements.txt` terminal command

## bulk_upload.py
This script bulk uploads files from a local directory to Reality Defender API. 
It writes intermediate results into uploads.csv. This includes the filename, filepath, and requestId from Reality Defender. You can use the requestId to get results from Reality Defender. 
- You will need to set up a directory that contains the files you want to upload
- The script accepts both a file and directory. If given a directory, it will traverse the directory
`Usage: python bulk_upload.py <directory_path>`

Once you have finished uploading, you may want to wait for several minutes to make sure all the files have been processed by Reality Defender before running the next script. Reality Defender offers a webhook that you can use in production as an alternative to waiting or polling. 

## get_results.py


