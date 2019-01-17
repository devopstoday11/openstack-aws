Setup
------
Intsall required package to run Trilio-Vault application
command : pip install -r requirements.txt
requirements.txt available on trilio directory

Configure aws by following below link
-------------------------------------
http://docs.aws.amazon.com/streams/latest/dev/kinesis-tutorial-cli-installation.html

provide require configurations to run Trilio-Vault application
--------------------------------------------------------------
config file available in scripts directory.

Short description of configurations:
------------------------------------
mandatory values to be changed in config file
---------------------------------------------
bucket_name : Name of s3 bucket to copy converted raw image to take snapshot 
region: Name of the region which user has access to perform operations like register ami and launch instance etc..
key_pair : Path to aws key-pair to access the instace after launching.

below config values works with defaults availble in config file
----------------------------------------------------------------
trilio_base_dir : Base directory of trilio vault workloads.
app_name : Name of the application 
log_level : log level to use in logging
container_json_path : Path to container json, which is used while uploading image to S3

How to Run
-----------
Extract trilio.zip and Navigate to scripts under trilio directory and then execute trilio_vault.py
command : python trilio_vault.py
