import enum
from typing import Optional
from pydantic import BaseModel, Field

class ProcessingStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    EXTRACTED = "EXTRACTED"
    CLASSIFIED_PENDING_DECISION = "CLASSIFIED_PENDING_DECISION"
    FINALIZED = "FINALIZED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    CLASSIFICATION_FAILED = "CLASSIFICATION_FAILED"

class DecisionSource(str, enum.Enum):
    AI = "AI"
    HUMAN = "HUMAN"

class DocumentRecord(BaseModel):
    pk: str  # tenantId#documentId
    sk: str = "v1"
    documentId: str
    tenantId: str
    status: ProcessingStatus
    s3Pointer: str
    createdAt: str
    updatedAt: str
    auctionId: Optional[str] = None
    sourceSystem: Optional[str] = None
    requestId: Optional[str] = None
    finalDecisionSource: Optional[DecisionSource] = None
