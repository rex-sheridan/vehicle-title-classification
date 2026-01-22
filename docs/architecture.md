# Architecture Diagrams

This document outlines the architectural design for the Vehicle Title Classification Pipeline.

## 1. System Architecture Diagram

This diagram shows the high-level AWS components and their relationships.

```mermaid
graph TD
    subgraph "Ingestion Layer"
        U[Uploader] -->|Upload Document| S3[S3 Ingest Bucket]
        S3 -->|ObjectCreated| LambdaIngest[Ingestion Lambda]
    end

    subgraph "Orchestration Layer"
        LambdaIngest -->|Start Execution| SF[AWS Step Functions]
    end

    subgraph "Processing Layer"
        SF -->|OCR/Extraction| Textract[Amazon Textract]
        SF -->|Classification| Bedrock[Amazon Bedrock]
    end

    subgraph "Storage & Human-in-the-loop"
        SF -->|Store Results| DDB[DynamoDB Record Store]
        SF -->|Escalate if Low Confidence| A2I[Amazon A2I Human Review]
        A2I -->|Update Label| DDB
    end

    subgraph "Eventing Layer"
        SF -->|Publish Event| EB[Amazon EventBridge]
        EB -->|Consume Result| Consumers[Downstream Systems]
    end
```

## 2. Data Flow Diagram

The sequence of operations during document processing.

```mermaid
sequenceDiagram
    participant S3 as S3 Ingest Bucket
    participant L as Ingestion Lambda
    participant SF as Step Functions
    participant T as Textract
    participant B as Bedrock
    participant D as DynamoDB
    participant A2I as A2I Human Review
    participant EB as EventBridge

    S3->>L: Object Created
    L->>D: Create Initial Record (Status: RECEIVED)
    L->>SF: Start Workflow
    SF->>T: DetectDocumentText / AnalyzeDocument
    T-->>SF: OCR Results (text, forms)
    SF->>D: Update Record (Status: EXTRACTED)
    SF->>B: Invoke Model (Claude)
    B-->>SF: docClass, state, type, confidence, rationale
    SF->>D: Update Record (Status: CLASSIFIED_PENDING_DECISION)
    
    ALT modelConfidence >= 0.95
        SF->>D: Finalize Record (Status: FINALIZED, finalDecisionSource: AI)
        SF->>EB: Publish TitleClassified Event
    ELSE modelConfidence < 0.95
        SF->>A2I: Create Human Review Task
        A2I-->>D: Update Record (Status: FINALIZED, finalDecisionSource: HUMAN)
        SF->>EB: Publish TitleClassified Event
    END
```

## 3. DynamoDB Data Model

Logical structure of the document records.

```mermaid
erDiagram
    DOCUMENT ||--o{ EXTRACTION : contains
    DOCUMENT ||--o{ CLASSIFICATION : produces
    
    DOCUMENT {
        string _pk "tenantId#documentId"
        string sk "v1"
        string status "RECEIVED | EXTRACTED | CLASSIFIED | FINALIZED"
        string s3Pointer "s3://..."
        timestamp createdAt
        timestamp updatedAt
    }

    EXTRACTION {
        string rawText
        json forms
        float textractConfidence
    }

    CLASSIFICATION {
        string documentClass "VEHICLE_TITLE | NON_TITLE"
        string state "2-letter code"
        string titleType
        float modelConfidence
        string rationale
        string finalDecisionSource "AI | HUMAN"
    }
```

## 4. Step Functions Flow

Visualization of the AWS Step Functions workflow orchestration.

![Step Functions Graph](stepfunctions_graph.png)
