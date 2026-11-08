"""
InsureGraph AI — Insurance Entity Definitions
Defines the taxonomy of P&C insurance entities and relationship types.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class EntityType(str, Enum):
    # Core Policy Entities
    POLICY = "Policy"
    POLICYHOLDER = "Policyholder"
    INSURED = "Insured"
    INSURER = "Insurer"
    AGENT = "Agent"

    # Asset Entities
    INSURED_PROPERTY = "InsuredProperty"
    VEHICLE = "Vehicle"
    BUSINESS = "Business"

    # Financial Entities
    COVERAGE = "Coverage"
    COVERAGE_LIMIT = "CoverageLimit"
    DEDUCTIBLE = "Deductible"
    PREMIUM = "Premium"
    ENDORSEMENT = "Endorsement"

    # Condition Entities
    EXCLUSION = "Exclusion"
    CONDITION = "Condition"
    WAITING_PERIOD = "WaitingPeriod"

    # Event Entities
    PERIL = "Peril"
    CLAIM = "Claim"
    LOSS_EVENT = "LossEvent"

    # Legal / Regulatory
    JURISDICTION = "Jurisdiction"
    TERM = "PolicyTerm"


class RelationshipType(str, Enum):
    # Ownership / Parties
    HOLDS_POLICY = "HOLDS_POLICY"
    INSURES = "INSURES"
    ISSUED_BY = "ISSUED_BY"
    COVERS = "COVERS"
    OWNED_BY = "OWNED_BY"

    # Financial
    HAS_DEDUCTIBLE = "HAS_DEDUCTIBLE"
    HAS_LIMIT = "HAS_LIMIT"
    HAS_PREMIUM = "HAS_PREMIUM"
    INCLUDES_ENDORSEMENT = "INCLUDES_ENDORSEMENT"

    # Conditions
    EXCLUDES = "EXCLUDES"
    SUBJECT_TO = "SUBJECT_TO"
    REQUIRES = "REQUIRES"
    APPLIES_TO = "APPLIES_TO"

    # Claims
    TRIGGERS = "TRIGGERS"
    RESULTS_IN = "RESULTS_IN"
    COVERED_UNDER = "COVERED_UNDER"

    # Temporal
    EFFECTIVE_DURING = "EFFECTIVE_DURING"
    EXPIRES_AFTER = "EXPIRES_AFTER"


@dataclass
class InsuranceEntity:
    """Represents an extracted insurance entity node."""
    id: str
    entity_type: EntityType
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)
    source_text: str = ""
    document_id: str = ""
    page_number: Optional[int] = None
    confidence: float = 1.0


@dataclass
class InsuranceRelationship:
    """Represents an extracted relationship edge between entities."""
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    properties: Dict[str, Any] = field(default_factory=dict)
    source_text: str = ""
    confidence: float = 1.0


# Entity extraction prompt template
ENTITY_EXTRACTION_PROMPT = """You are an expert insurance policy analyst. Extract all insurance entities and relationships from the following policy text.

Return a JSON object with:
1. "entities": list of entities, each with:
   - "id": unique snake_case identifier
   - "entity_type": one of {entity_types}
   - "label": human-readable name
   - "properties": dict of relevant attributes (amounts, dates, conditions, etc.)
   - "source_text": the exact text snippet this was extracted from

2. "relationships": list of relationships, each with:
   - "source_id": entity id
   - "target_id": entity id  
   - "relationship_type": one of {relationship_types}
   - "properties": dict of relationship attributes
   - "source_text": supporting text

Policy Text:
{text}

Focus on:
- Coverage amounts and limits (extract exact dollar values)
- Deductibles (per-occurrence, aggregate, percentage-based)
- Exclusions (what is NOT covered)
- Named perils vs. open peril policies
- Conditions and endorsements
- Policyholder and insured party details
- Policy term dates and premium amounts

Return ONLY valid JSON, no explanation."""

ENTITY_TYPES_LIST = [e.value for e in EntityType]
RELATIONSHIP_TYPES_LIST = [r.value for r in RelationshipType]
