import boto3
import os

textract = boto3.client('textract')

def handler(event, context):
    """
    Textract Extractor:
    Extracts raw text from the document in S3.
    """
    s3_pointer = event['s3Pointer']
    # s3_pointer is in format s3://bucket/key
    parts = s3_pointer.replace("s3://", "").split("/", 1)
    bucket = parts[0]
    key = parts[1]

    try:
        response = textract.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        
        # Consolidate raw text
        raw_text = ""
        for item in response.get('Blocks', []):
            if item['BlockType'] == 'LINE':
                raw_text += item['Text'] + "\n"
                
        return {
            "rawText": raw_text,
            "textractConfidence": 1.0 # Simplified for demo
        }
    except Exception as e:
        print(f"Textract error: {e}")
        raise e
