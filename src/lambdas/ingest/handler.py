import json
import os
import uuid
import boto3
from datetime import datetime
from src.common.models import ProcessingStatus, DocumentRecord

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
stepfunctions = boto3.client('stepfunctions')

TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'VehicleTitleRecords')
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN')

def handler(event, context):
    """
    Ingestion Lambda: Handles S3 ObjectCreated events.
    Validates metadata, creates DDB record, and starts Step Functions workflow.
    """
    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        # 1. Get Object Metadata
        try:
            response = s3_client.head_object(Bucket=bucket, Key=key)
            metadata = response.get('Metadata', {})
        except Exception as e:
            print(f"Error getting metadata for {key}: {e}")
            continue

        # 2. Extract IDs from metadata or path
        # In-scope key naming: /{tenant}/{auction}/{yyyy}/{mm}/{dd}/{uuid}.{ext}
        path_parts = key.strip('/').split('/')
        tenant_id = metadata.get('tenantid') or (path_parts[0] if len(path_parts) > 0 else 'unknown')
        auction_id = metadata.get('auctionid') or (path_parts[1] if len(path_parts) > 1 else 'unknown')
        
        document_id = metadata.get('requestid') or str(uuid.uuid4())
        
        # 3. Create initial DynamoDB record
        now = datetime.utcnow().isoformat()
        doc_record = DocumentRecord(
            pk=f"{tenant_id}#{document_id}",
            documentId=document_id,
            tenantId=tenant_id,
            auctionId=auction_id,
            status=ProcessingStatus.RECEIVED,
            s3Pointer=f"s3://{bucket}/{key}",
            createdAt=now,
            updatedAt=now,
            sourceSystem=metadata.get('sourcesystem'),
            requestId=metadata.get('requestid')
        )
        
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item=doc_record.dict())
        
        # 4. Start Step Functions Execution
        if STATE_MACHINE_ARN:
            sf_input = {
                "documentId": document_id,
                "tenantId": tenant_id,
                "bucket": bucket,
                "key": key,
                "s3Pointer": doc_record.s3Pointer
            }
            stepfunctions.start_execution(
                stateMachineArn=STATE_MACHINE_ARN,
                name=f"{document_id}-{uuid.uuid4().hex[:8]}",
                input=json.dumps(sf_input)
            )
            print(f"Started workflow for document {document_id}")
        else:
            print("STATE_MACHINE_ARN not configured, skipping Step Functions invocation.")

    return {
        'statusCode': 200,
        'body': json.dumps('Ingestion processed successfully')
    }
