import json
import os
import boto3
from datetime import datetime
from src.common.models import ProcessingStatus, DecisionSource

bedrock = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')

TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'VehicleTitleRecords')
MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')

def handler(event, context):
    """
    Process Results Lambda:
    - Pre-processes Textract output.
    - Calls Bedrock for classification.
    - Applies decision rules.
    - Updates DynamoDB.
    """
    document_id = event['documentId']
    tenant_id = event['tenantId']
    textract_output = event.get('textractOutput', {}) # This would contain extracted text
    
    # 1. Sanitize and prepare text for Bedrock
    raw_text = textract_output.get('rawText', '')
    # Truncate if too long for the model context (simplified)
    sanitized_text = raw_text[:30000] 

    # 2. Build Bedrock Prompt
    prompt = f"""
    You are an expert vehicle title classifier. 
    Analyze the following text extracted from a document and classify it.

    Allowed Document Classes: VEHICLE_TITLE, NON_TITLE, UNKNOWN
    Allowed States: 2-letter US state codes (e.g., GA, FL, TX) or UNKNOWN.
    
    Extracted Text:
    {sanitized_text}

    Return the result in JSON format:
    {{
        "documentClass": "...",
        "state": "...",
        "titleType": "...",
        "modelConfidence": 0.0-1.0,
        "rationale": "short explanation"
    }}
    """

    # 3. Call Bedrock
    try:
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            })
        )
        response_body = json.loads(response.get('body').read())
        classification = json.loads(response_body['content'][0]['text'])
    except Exception as e:
        print(f"Bedrock invocation failed: {e}")
        return {
            "status": ProcessingStatus.CLASSIFICATION_FAILED,
            "error": str(e)
        }

    # 4. Apply Decision Rules (Section 6 of Spec)
    confidence = classification.get('modelConfidence', 0)
    doc_class = classification.get('documentClass', 'UNKNOWN')
    
    final_status = ProcessingStatus.FINALIZED
    decision_source = DecisionSource.AI
    
    if doc_class != 'VEHICLE_TITLE' or confidence < 0.95:
        if confidence >= 0.80:
            final_status = ProcessingStatus.REVIEW_REQUIRED
        else:
            final_status = ProcessingStatus.REVIEW_REQUIRED # Or REJECTED if extremely low

    # 5. Update DynamoDB
    table = dynamodb.Table(TABLE_NAME)
    now = datetime.utcnow().isoformat()
    
    table.update_item(
        Key={'pk': f"{tenant_id}#{document_id}", 'sk': 'v1'},
        UpdateExpression="SET #s = :s, #c = :c, #upa = :upa, #ds = :ds",
        ExpressionAttributeNames={
            '#s': 'status',
            '#c': 'classification',
            '#upa': 'updatedAt',
            '#ds': 'finalDecisionSource'
        },
        ExpressionAttributeValues={
            ':s': final_status,
            ':c': classification,
            ':upa': now,
            ':ds': decision_source if final_status == ProcessingStatus.FINALIZED else None
        }
    )

    return {
        "documentId": document_id,
        "tenantId": tenant_id,
        "status": final_status,
        "classification": classification
    }
