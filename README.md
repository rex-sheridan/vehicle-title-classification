# Vehicle Title Classification Pipeline (AWS Serverless)

Automate classification of U.S. vehicle title documents by **state** and **title type** using AWS Serverless services and Generative AI.

## 🚀 Overview

This project implements a high-trust document classification pipeline designed to reduce manual review volume while maintaining high precision. It uses **Amazon Textract** for OCR and **Amazon Bedrock (Claude 3)** for intelligent classification and rationale generation.

### Key Features
- **Automated Ingestion**: Triggered by S3 object creation.
- **High-Precision AI**: Uses Claude 3 to classify titles with confidence thresholds.
- **State Machine Orchestration**: AWS Step Functions coordinates multiple services.
- **Human-in-the-loop (HITL)**: Automated escalation to Amazon A2I for low-confidence results.
- **Auditability**: Complete traceability in DynamoDB with status tracking and rationale.

## 🏗️ Architecture

The system follows a serverless architecture:

- **Ingestion**: S3 -> Lambda
- **Orchestration**: AWS Step Functions
- **Processing**: Amazon Textract (OCR) -> Amazon Bedrock (Classification) -> DynamoDB (Storage)
- **Eventing**: Amazon EventBridge for downstream integration.

For detailed diagrams, see [docs/architecture.md](./docs/architecture.md).

## 📁 Project Structure

```text
.
├── src/
│   ├── common/             # Shared models and utilities
│   └── lambdas/            # AWS Lambda function handlers
│       ├── ingest/         # S3 entry point
│       ├── textract/       # OCR extraction logic
│       └── process/        # Bedrock classification & decision logic
├── statemachine/           # Step Functions ASL definition
├── docs/                   # Architecture diagrams and documentation
├── tests/                  # Unit and integration tests
├── template.yaml           # AWS SAM deployment template
└── requirements.txt        # Python dependencies
```

## 🛠️ Getting Started

### Prerequisites
- AWS CLI configured with appropriate permissions.
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) installed.
- Python 3.9 or higher.

### Setup
1. Clone the repository.
2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Deployment
Deploy the pipeline to your AWS account using SAM:
```bash
sam build
sam deploy --guided
```

## 🧪 Testing

### Smoke Tests
Run the basic verification script to ensure handlers are correctly configured:
```bash
export PYTHONPATH=$PYTHONPATH:.
export AWS_DEFAULT_REGION=us-east-1
python3 tests/smoke_test.py
```

## 🛡️ Security & Observability
- **Encryption**: S3 SSE-KMS and DynamoDB encryption at rest.
- **Least Privilege**: IAM roles scoped to specific resources.
- **Monitoring**: Alarms on error rates and latency in CloudWatch.

## 📄 License
Internal Use Only - Manheim Title Services.
