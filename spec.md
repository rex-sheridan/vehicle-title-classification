**AI Spec: Vehicle Title Classification Pipeline (AWS Serverless)**
-------------------------------------------------------------------

### **1\. Problem Statement and Intent**

Automate classification of vehicle title documents by **U.S. state** and **title type** (and optionally key fields) to reduce manual processing time while maintaining auditability, security, and operational reliability.

**Primary outcomes**

*   Faster check-in/check-out and downstream processing by reducing manual review load.
    
*   High trust classifications with explicit confidence thresholds and human escalation.
    
*   Full traceability for compliance and dispute resolution.
    

**Success metrics**

*   ≥40% reduction in manual review volume after stabilization period
    
*   Auto-accept precision ≥99% on in-scope title types (measured on labeled validation set)
    
*   p95 end-to-end processing latency ≤ 10 seconds per document (excluding human review)
    
*   Zero P0 incidents caused by misclassification in critical downstream flows (tracked via defect taxonomy)
    

### **2\. Actors and Responsibilities**

*   **Uploader (system/user):** Places title image into S3.
    
*   **Ingestion Lambda:** Validates object metadata, assigns correlation IDs, starts workflow.
    
*   **Textract Extractor:** Extracts text and structured form/key-value data.
    
*   **Bedrock Classifier:** Classifies state + title type; returns confidence and rationale.
    
*   **DynamoDB Record Store:** Stores extraction and classification results for retrieval and analytics.
    
*   **A2I Human Review:** Reviews low-confidence or exception cases; provides final label.
    
*   **Audit/Analytics Consumers:** Use DynamoDB + logs for monitoring, QA, and governance.
    

Principle: **AI proposes, workflow decides, humans arbitrate exceptions.**

### **3\. Scope and Constraints**

**In-scope**

*   U.S. vehicle title images (PDF, JPG, PNG) within size limits.
    
*   State classification, title type classification, and optional extraction of specific fields (VIN, owner name, issue date) if required by downstream.
    

**Out-of-scope (initial)**

*   Non-title documents (insurance, bills of sale) except as “not a title” classification.
    
*   Fully automated dispute resolution or downstream record updates without human oversight.
    

### **4\. Inputs and Outputs**

**Input (S3 object)**

*   Bucket: manheim-title-ingest-
    
*   Key naming: /{tenant}/{auction}/{yyyy}/{mm}/{dd}/{uuid}.{ext}
    
*   Metadata (optional): tenantId, auctionId, sourceSystem, requestId
    

**Extraction output (Textract)**

*   rawText: string (bounded)
    
*   forms: key-value pairs
    
*   tables: optional
    
*   textractConfidence: aggregate metric
    

**Classification output (Bedrock)**

*   documentClass: enum: VEHICLE\_TITLE, NON\_TITLE, UNKNOWN
    
*   state: 2-letter code, or UNKNOWN
    
*   titleType: enum (configurable)
    
*   modelConfidence: float 0.0–1.0
    
*   rationale: short structured explanation (non-sensitive)
    

**DynamoDB item (single-record retrieval)**

Partition key: pk = tenantId#documentId

Sort key: sk = v1

Attributes: extraction summary, classification, status, timestamps, model version, reviewer outcome, links to raw artifacts.

### **5\. Workflow and Architecture (Serverless)**

**Step 1: Ingestion**

*   S3 ObjectCreated triggers **Lambda Ingest**.
    
*   Lambda validates file type, size, and required metadata.
    
*   Lambda writes initial record to DynamoDB with status RECEIVED.
    
*   Lambda invokes workflow orchestrator (recommended: **AWS Step Functions**) with documentId and S3 pointer.
    

**Step 2: Extraction**

*   Step Functions calls Textract (async preferred for PDFs).
    
*   Store Textract job ID and results pointer.
    
*   Update DynamoDB status EXTRACTED.
    

**Step 3: Classification**

*   Pre-process extracted text (sanitize, truncate, normalize).
    
*   Call Bedrock model (e.g., Claude) with constrained prompt and allowed labels.
    
*   Update DynamoDB status CLASSIFIED\_PENDING\_DECISION.
    

**Step 4: Decision and Storage**

*   Apply decision rules (below).
    
*   Persist final outcome to DynamoDB with immutable audit fields.
    
*   Update DynamoDB status FINALIZED or REVIEW\_REQUIRED.
    

**Step 5: Human-in-the-loop (A2I)**

*   If routed, create A2I task with relevant artifacts (image link, extracted text, candidate labels).
    
*   On human completion, update DynamoDB with humanLabel, humanConfidence, and finalDecisionSource = HUMAN.
    
*   Optionally publish event for downstream consumers.
    

**Step 6: Eventing (recommended)**

*   Publish TitleClassified event to EventBridge (or SNS) for downstream systems.
    
*   Downstream reads from DynamoDB or consumes event payload.
    

### **6\. Decision Boundaries and Confidence Thresholds**

**Autonomy policy**

*   *   documentClass == VEHICLE\_TITLE
        
    *   modelConfidence >= 0.95
        
    *   Textract quality above minimum threshold (configurable)
        
    *   No rule-based red flags (e.g., conflicting state indicators)
        
*   *   0.80 <= modelConfidence < 0.95, or
        
    *   Textract quality below threshold, or
        
    *   Conflicting signals detected
        
*   *   modelConfidence < 0.80, or
        
    *   documentClass in {UNKNOWN, NON\_TITLE} but downstream expects a title
        

All thresholds are config-driven per tenant and environment.

### **7\. Non-Functional Requirements**

**Reliability**

*   Availability 99.9% during auction hours
    
*   All steps idempotent using documentId
    
*   Retry policy with exponential backoff; dead-letter handling for failed executions
    

**Performance**

*   p95 pipeline time ≤ 10 seconds for non-human path
    
*   Concurrency controls to avoid Textract and Bedrock throttling
    

**Security and privacy**

*   S3 SSE-KMS encryption
    
*   DynamoDB encryption at rest; strict IAM least privilege
    
*   PII handling: redact or tokenize where needed in logs and prompts
    
*   No raw document images stored in DynamoDB
    

**Cost**

*   Budget guardrails per environment
    
*   Track per-document costs (Textract + Bedrock) as part of metrics
    

**Operational excellence**

*   Structured logs with correlation ID
    
*   Alarms on error rates, latency, throttles, review backlog
    

### **8\. Failure Modes and Safe Degradation**

*   Textract failure: mark EXTRACTION\_FAILED, route to manual workflow
    
*   Bedrock failure/timeouts: retry within limits; then route to manual
    
*   Low OCR quality: route to human with image-first UI
    
*   Service throttling: backpressure via Step Functions, reserved concurrency, and queueing if needed
    
*   Drift signals: automatically tighten thresholds and increase review sampling
    

### **9\. Observability and Auditability**

**Metrics**

*   Volume processed, auto-accept rate, review rate, reject rate
    
*   Accuracy estimates (from human-reviewed sample)
    
*   p95 latency per step
    
*   Textract confidence distribution
    
*   Model confidence distribution and calibration
    

**Audit logs**

*   Store: model ID/version, prompt version, confidence, decision rule path, timestamps
    
*   Every final decision is replayable using stored artifacts pointers and versions
    

### **10\. Governance and Change Management**

*   Model and prompt versions are controlled artifacts (versioned in repo)
    
*   Changes require architecture review and gated rollout (dev → stage → prod)
    
*   Human review feedback used for periodic evaluation and retraining strategy (if applicable)
    
*   Documented ethical constraints and data retention policy
    

### **11\. Testing Strategy**

*   Unit tests: parsing, validation, decision logic, idempotency
    
*   Integration tests: S3 → Lambda → Textract → Bedrock → DynamoDB
    
*   Golden set evaluation: labeled title set per state and title type
    
*   Regression tests on prompt/model version changes
    
*   Load tests for auction peak scenarios
    

### **12\. AI Execution Constraints**

*   Bedrock is limited to classification and structured output only
    
*   Allowed labels enumerated and validated; reject free-form categories
    
*   Hard token and length caps; sanitized input only
    
*   No autonomous writes to downstream systems without finalization and audit record
    

If you want, I can turn this into a **verbal walkthrough script** for Jigar (what to say in 90 seconds, then how to handle follow-ups on security, drift, and cost), or I can **refine the DynamoDB schema and event payload** to match a multi-tenant Manheim domain model.