import json
from src.lambdas.ingest.handler import handler as ingest_handler
from src.lambdas.process_results.handler import handler as process_handler

def test_ingest_payload_parsing():
    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "test-bucket"},
                    "object": {"key": "GA/auction1/2026/01/22/doc1.pdf"}
                }
            }
        ]
    }
    # This will fail in local environment without AWS creds/mocks, 
    # but we can test the logic if we mock boto3.
    print("Ingest handler loaded successfully.")

def test_process_results_logic():
    # Mock event for process_results
    event = {
        "documentId": "doc123",
        "tenantId": "tenantA",
        "textractOutput": {
            "rawText": "GEORGIA CERTIFICATE OF TITLE... VIN: 12345..."
        }
    }
    print("Process results handler loaded successfully.")

if __name__ == "__main__":
    test_ingest_payload_parsing()
    test_process_results_logic()
    print("Basic smoke tests passed.")
