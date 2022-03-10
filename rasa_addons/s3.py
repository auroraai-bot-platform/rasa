import os
import boto3
import logging

logger = logging.getLogger(__name__)

def download_dir(client, resource, dist, local='/tmp', bucket='your_bucket'):
    paginator = client.get_paginator('list_objects')
    for result in paginator.paginate(Bucket=bucket, Delimiter='/', Prefix=dist):
        if result.get('CommonPrefixes') is not None:
            for subdir in result.get('CommonPrefixes'):
                download_dir(client, resource, subdir.get('Prefix'), local, bucket)
        for file in result.get('Contents', []):
            dest_pathname = os.path.join(local, file.get('Key'))
            if not os.path.exists(os.path.dirname(dest_pathname)):
                os.makedirs(os.path.dirname(dest_pathname))
            if not file.get('Key').endswith('/'):
                logger.info(f"Loading language model file {dest_pathname}")
                resource.meta.client.download_file(bucket, file.get('Key'), dest_pathname)

def load_s3_language_models():
    s3_bucket = os.environ['MODEL_BUCKET']
    s3_dir = os.environ['LANGUAGE_MODEL_S3_DIR']
    local_dir = os.environ['LANGUAGE_MODEL_LOCAL_DIR']
    aws_endpoint = os.environ['AWS_ENDPOINT']
    region = os.environ['AWS_DEFAULT_REGION']

    if aws_endpoint == '':
        client = boto3.client('s3')
        resource = boto3.resource('s3')
    else:
        client = boto3.client('s3', region_name=region,  endpoint_url=aws_endpoint)
        resource = boto3.resource('s3', region_name=region, endpoint_url=aws_endpoint)

    
    download_dir(client, resource, s3_dir, local_dir, s3_bucket)