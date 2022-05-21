import json
import urllib.parse
import boto3
import csv
import nltk
import os
from datetime import datetime


s3 = boto3.client('s3')
text_classification = boto3.client('runtime.sagemaker')
dict_for_web = []

def lambda_handler(event, context):

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e

    data = response['Body'].read().decode('utf-8').splitlines()
    data = csv.reader(data)
    
    for record in data:
        tokenized_sentence = nltk.word_tokenize(record[5])
        payload = {"instances": tokenized_sentence}
        payload = json.dumps(payload)
        response = text_classification.invoke_endpoint(EndpointName=os.environ["ENDPOINT_NAME"], ContentType='application/json', Body=payload)
        my_json = json.loads(response['Body'].read())

        for item in my_json:
            dt_object = datetime.fromtimestamp(int(float(record[0])))
            obj = {
                'timestamp': str(dt_object), 
                'src_ip': record[1],
                'src_port': record[2],
                'dst_ip': record[3], 
                'dst_port': record[4], 
                'prediction': [item['label'], item['prob']]
            }
        dict_for_web.append(obj)

    print("LOG: Amount of packets", len(dict_for_web))
    json_object = json.dumps(dict_for_web, indent=4)
    s3.put_object(Bucket=os.environ["BUCKET_NAME"], Key=os.environ["FILE_LOCATION"],Body=json_object)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Execution completed!')
    }