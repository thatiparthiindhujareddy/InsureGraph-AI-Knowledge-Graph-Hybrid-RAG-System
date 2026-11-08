"""
InsureGraph AI — Golden Evaluation Dataset
25 complex P&C insurance Q&A pairs for the evaluation harness.
Covers multi-hop reasoning, exclusion analysis, deductible conditions, and coverage limits.
"""
from typing import List, Dict, Any

GOLDEN_DATASET: List[Dict[str, Any]] = [
    # ─── Coverage Questions ────────────────────────────────────────────────────
    {
        "id": "Q001",
        "category": "coverage",
        "difficulty": "medium",
        "question": "What is the maximum coverage limit for building damage under the commercial property policy?",
        "ground_truth": "The commercial property policy provides building coverage up to $2,500,000 per occurrence, subject to the applicable deductible.",
        "keywords": ["coverage limit", "building", "commercial property", "per occurrence"],
    },
    {
        "id": "Q002",
        "category": "exclusion",
        "difficulty": "hard",
        "question": "Is flood damage covered under the standard commercial property policy, and if not, what endorsements can provide this coverage?",
        "ground_truth": "Standard commercial property policies explicitly exclude flood damage caused by surface water, storm surge, or overflow of bodies of water. Coverage can be obtained through a separate Flood Insurance endorsement (ISO CP 10 65) or via the National Flood Insurance Program (NFIP). The standard exclusion applies regardless of whether the flood is caused by a named storm.",
        "keywords": ["flood", "exclusion", "endorsement", "NFIP"],
    },
    {
        "id": "Q003",
        "category": "deductible",
        "difficulty": "hard",
        "question": "Does the commercial property policy cover water damage if the deductible has not been met, and what are the exclusions?",
        "ground_truth": "Water damage from burst pipes or plumbing leaks is covered under the commercial property policy, but only after the applicable deductible is met. The standard deductible is $10,000 per occurrence. If the loss amount is below the deductible, no payment is made. Exclusions include: flood water, surface water, groundwater seepage, water backed up from sewers unless the sewer backup endorsement is attached, and damage from failure to maintain the property.",
        "keywords": ["water damage", "deductible", "burst pipes", "sewer backup", "exclusion"],
    },
    {
        "id": "Q004",
        "category": "liability",
        "difficulty": "medium",
        "question": "What is the general liability occurrence limit and aggregate limit under the commercial general liability policy?",
        "ground_truth": "The commercial general liability policy provides a $1,000,000 per occurrence limit for bodily injury and property damage, with a $2,000,000 general aggregate limit. The products-completed operations aggregate is also $2,000,000. Personal and advertising injury limit is $1,000,000 per occurrence.",
        "keywords": ["general liability", "occurrence limit", "aggregate", "bodily injury"],
    },
    {
        "id": "Q005",
        "category": "multi-hop",
        "difficulty": "hard",
        "question": "If a fire destroys the insured building and the business cannot operate for 3 months, will both property damage and business income losses be covered?",
        "ground_truth": "Yes, both coverages would apply. The commercial property coverage would pay for building reconstruction up to the $2,500,000 limit minus the $10,000 deductible. The business income coverage would then activate, covering lost net income and continuing expenses (like payroll, rent, and utilities) for the 3-month interruption period, subject to the 72-hour waiting period and the 12-month maximum indemnity period. The business income limit under this policy is $500,000.",
        "keywords": ["fire", "business income", "property damage", "interruption", "waiting period"],
    },
    {
        "id": "Q006",
        "category": "coverage",
        "difficulty": "easy",
        "question": "What perils are covered under the commercial property policy?",
        "ground_truth": "The commercial property policy is written on a Special Form (open perils) basis, covering all risks of direct physical loss unless specifically excluded. Covered perils include: fire, lightning, windstorm, hail, explosion, aircraft damage, vehicles, smoke, vandalism, theft, collapse, water damage from plumbing, and volcanic action. Named exclusions include: flood, earthquake, wear and tear, mechanical breakdown, government action, and nuclear hazard.",
        "keywords": ["perils", "covered", "open perils", "special form", "exclusions"],
    },
    {
        "id": "Q007",
        "category": "deductible",
        "difficulty": "medium",
        "question": "Is there a separate wind and hail deductible, and how is it calculated?",
        "ground_truth": "Yes, the policy includes a separate wind and hail deductible of 2% of the insured building value per occurrence, with a minimum of $5,000. For a $2,500,000 building, this equals a $50,000 wind/hail deductible. This is separate from and replaces the standard $10,000 deductible for wind and hail losses only.",
        "keywords": ["wind", "hail", "deductible", "percentage", "calculation"],
    },
    {
        "id": "Q008",
        "category": "exclusion",
        "difficulty": "medium",
        "question": "Are losses caused by employee theft covered under the commercial property policy?",
        "ground_truth": "Employee theft is excluded from the standard commercial property policy. Coverage for employee theft and dishonesty is available through a separate Crime policy or a Commercial Crime Coverage endorsement (ISO CR 00 21). The standard property policy excludes dishonest acts by employees, directors, trustees, and authorized representatives.",
        "keywords": ["employee theft", "crime", "dishonesty", "exclusion"],
    },
    {
        "id": "Q009",
        "category": "liability",
        "difficulty": "hard",
        "question": "Does the general liability policy cover bodily injury claims from products the insured sold 5 years ago?",
        "ground_truth": "Yes, products liability coverage under the commercial general liability policy covers bodily injury arising from products sold during the policy period, even if the claim is made years later, provided the policy in effect at the time of the original sale had products-completed operations coverage. The products-completed operations aggregate limit of $2,000,000 applies. Note: claims-made policies would require a separate tail coverage or extended reporting period endorsement.",
        "keywords": ["products liability", "bodily injury", "completed operations", "claims-made", "occurrence"],
    },
    {
        "id": "Q010",
        "category": "multi-hop",
        "difficulty": "hard",
        "question": "What happens to the coverage if the policyholder increases the building value by 30% through renovation but does not update the policy?",
        "ground_truth": "If the building value increases by 30% through renovation but the policy limits are not updated, the policyholder faces a coinsurance penalty. Under the 80% coinsurance clause, the insured must maintain coverage equal to at least 80% of the building's replacement cost value. If coverage falls below this threshold, the insurer will only pay a proportional share of any loss. For example, if the building is now worth $3,250,000 and the policy limit remains at $2,500,000, but the required 80% minimum is $2,600,000, the insured is under-insured and will receive reduced claim payments.",
        "keywords": ["coinsurance", "under-insured", "renovation", "replacement cost", "80% clause"],
    },
    # ─── Premium & Policy Term Questions ────────────────────────────────────────
    {
        "id": "Q011",
        "category": "premium",
        "difficulty": "easy",
        "question": "What is the annual premium for the commercial property policy?",
        "ground_truth": "The annual premium for the commercial property policy is $18,500, payable in quarterly installments of $4,625. A 3% premium discount applies if paid in full at inception.",
        "keywords": ["premium", "annual", "quarterly", "payment"],
    },
    {
        "id": "Q012",
        "category": "coverage",
        "difficulty": "medium",
        "question": "Does the policy cover outdoor signs and fences, and what are the sublimits?",
        "ground_truth": "Yes, outdoor signs and fences are covered under the policy but subject to sublimits. Outdoor signs are covered up to $10,000 per sign or $25,000 total. Fences are covered up to $15,000. These sublimits apply even if the building limit has not been exhausted. Both are subject to the standard $10,000 deductible.",
        "keywords": ["outdoor signs", "fences", "sublimits", "coverage"],
    },
    {
        "id": "Q013",
        "category": "exclusion",
        "difficulty": "hard",
        "question": "Is mold remediation covered if it results from a covered water damage loss?",
        "ground_truth": "Mold remediation is covered only when it results directly from a covered water damage loss (e.g., burst pipe) and only if it is reported and remediation begins within 30 days of the initial water damage loss. Coverage is subject to a $50,000 sublimit for mold remediation, separate from the building limit. Mold arising from long-term moisture, humidity, or pre-existing conditions is excluded entirely.",
        "keywords": ["mold", "remediation", "water damage", "sublimit", "30 days"],
    },
    {
        "id": "Q014",
        "category": "liability",
        "difficulty": "medium",
        "question": "Are contractors hired by the insured automatically covered as additional insureds under the general liability policy?",
        "ground_truth": "No, contractors are not automatically additional insureds. They must be specifically named as additional insureds via an endorsement (typically ISO CG 20 10 or CG 20 37). The policy requires that a written contract between the insured and contractor be in place before the loss. The additional insured coverage for contractors is limited to liability arising from the named insured's ongoing or completed operations.",
        "keywords": ["additional insured", "contractor", "endorsement", "written contract"],
    },
    {
        "id": "Q015",
        "category": "multi-hop",
        "difficulty": "hard",
        "question": "If a customer slips and falls in the insured premises due to a wet floor caused by roof leak (which is a covered peril), which policy section responds first?",
        "ground_truth": "This scenario involves both property and liability coverages. The roof leak would first be addressed under the commercial property coverage (repair costs subject to $10,000 deductible). The customer's slip-and-fall bodily injury claim would be handled separately under the commercial general liability policy, with the $1,000,000 per occurrence limit applying. Both coverages respond independently — the property claim does not reduce the liability limits. However, the insured must prove the roof leak was the direct cause and demonstrate reasonable premises maintenance to avoid a comparative negligence reduction.",
        "keywords": ["slip fall", "bodily injury", "property damage", "concurrent", "premises liability"],
    },
    # ─── Business Interruption ───────────────────────────────────────────────
    {
        "id": "Q016",
        "category": "business_interruption",
        "difficulty": "medium",
        "question": "What is the waiting period before business income coverage begins?",
        "ground_truth": "Business income coverage has a 72-hour (3-day) waiting period from the time of the direct physical loss before coverage begins. This waiting period acts as a time deductible. If the business interruption lasts less than 72 hours, no business income claim is payable. The maximum indemnity period is 12 months from the date of loss.",
        "keywords": ["business income", "waiting period", "72 hours", "indemnity period"],
    },
    {
        "id": "Q017",
        "category": "business_interruption",
        "difficulty": "hard",
        "question": "Are extra expenses incurred to continue operations at a temporary location covered?",
        "ground_truth": "Yes, Extra Expense coverage is included in the policy and covers additional costs incurred to continue operations at a temporary location or to expedite the restoration of normal business operations. Covered extra expenses include: temporary rent, expedited shipping, overtime labor, and equipment rental. Extra expenses that are also covered under business income (like payroll continuation) cannot be double-counted. The extra expense sublimit is $100,000 per occurrence.",
        "keywords": ["extra expense", "temporary location", "operations", "sublimit"],
    },
    {
        "id": "Q018",
        "category": "coverage",
        "difficulty": "medium",
        "question": "Does the policy cover equipment breakdown, and what are the coverage terms?",
        "ground_truth": "Equipment breakdown is not covered under the standard commercial property policy (it is excluded under the mechanical breakdown exclusion). However, Equipment Breakdown Coverage can be added via endorsement (ISO EB 00 20), which would cover sudden and accidental breakdown of boilers, pressure vessels, electrical equipment, HVAC systems, and production machinery. The endorsement limit is typically equal to the property limit with a separate $1,000 deductible.",
        "keywords": ["equipment breakdown", "mechanical breakdown", "exclusion", "endorsement", "boiler"],
    },
    {
        "id": "Q019",
        "category": "exclusion",
        "difficulty": "medium",
        "question": "Are losses caused by earth movement or earthquake covered?",
        "ground_truth": "Earthquake and earth movement are explicitly excluded from the commercial property policy. This includes: earthquake, volcanic eruption, landslide, mudslide, subsidence, and earth sinking. Coverage for earthquake can be obtained through a separate Earthquake endorsement or policy. Earthquake deductibles, when available, are typically 2-10% of the insured value per occurrence.",
        "keywords": ["earthquake", "earth movement", "exclusion", "volcanic"],
    },
    {
        "id": "Q020",
        "category": "multi-hop",
        "difficulty": "hard",
        "question": "If the insured files a claim for $500,000 in property damage and separately a $300,000 business income claim from the same fire, how much will the insurer pay in total?",
        "ground_truth": "For the property damage claim: The insurer pays $500,000 minus the $10,000 deductible = $490,000 (assuming the insured value and coinsurance requirements are met). For the business income claim: After the 72-hour waiting period, the insurer covers the $300,000 in lost income subject to the $500,000 business income limit — so the full $300,000 is paid (no separate deductible applies to business income under this policy). Total payout: $490,000 (property) + $300,000 (business income) = $790,000. Note: both coverages are separate and the deductible only applies once to the direct property loss.",
        "keywords": ["fire claim", "property damage", "business income", "deductible", "total payout"],
    },
    # ─── Liability Deep-Dives ─────────────────────────────────────────────────
    {
        "id": "Q021",
        "category": "liability",
        "difficulty": "hard",
        "question": "Does the general liability policy cover punitive damages awarded in a lawsuit?",
        "ground_truth": "Coverage for punitive damages depends on the jurisdiction. The commercial general liability policy covers 'compensatory damages' (actual losses). Many states prohibit insuring punitive damages as a matter of public policy. In states where insurability of punitive damages is permitted, the policy may cover them up to the occurrence limit. The policy contains a punitive damages exclusion only where required by law. Insureds should review their state-specific endorsements for clarity.",
        "keywords": ["punitive damages", "compensatory", "lawsuit", "jurisdiction", "exclusion"],
    },
    {
        "id": "Q022",
        "category": "coverage",
        "difficulty": "medium",
        "question": "What is the medical payments coverage limit, and does it require proof of negligence?",
        "ground_truth": "Medical Payments coverage has a $10,000 per person limit and pays medical expenses for bodily injury sustained on the insured premises regardless of fault or negligence. This is a goodwill coverage — no negligence needs to be proven. It covers: first aid, medical, surgical, dental, ambulance, hospital, and funeral expenses. Coverage applies for injuries occurring within 1 year of the accident date.",
        "keywords": ["medical payments", "negligence", "fault", "bodily injury", "premises"],
    },
    {
        "id": "Q023",
        "category": "conditions",
        "difficulty": "medium",
        "question": "What are the insured's duties after a loss?",
        "ground_truth": "After a loss, the insured must: (1) Notify the insurer as soon as practicable, (2) Notify police if loss involves theft or vandalism, (3) Protect property from further damage (costs covered), (4) Make a complete inventory of damaged property, (5) Submit a signed sworn proof of loss within 60 days of insurer's request, (6) Submit to examination under oath, (7) Cooperate with the insurer's investigation, and (8) Authorize release of financial records. Failure to comply with these conditions may result in claim denial.",
        "keywords": ["duties after loss", "proof of loss", "notification", "cooperation", "60 days"],
    },
    {
        "id": "Q024",
        "category": "multi-hop",
        "difficulty": "hard",
        "question": "The insured has a $10,000 deductible on the property policy. A windstorm causes $8,000 in roof damage and separately $15,000 in HVAC unit damage. How much is paid?",
        "ground_truth": "The deductible applies per occurrence. A single windstorm event constitutes one occurrence, so the $10,000 deductible applies once to the combined loss. Total loss: $8,000 (roof) + $15,000 (HVAC) = $23,000. Less: $10,000 deductible = $13,000 payable. Note: if the wind and hail percentage deductible applies (2% of building value = $50,000 for a $2.5M building), then the entire $23,000 loss would be below the deductible and nothing would be paid.",
        "keywords": ["windstorm", "per occurrence", "deductible", "roof", "HVAC", "combined loss"],
    },
    {
        "id": "Q025",
        "category": "conditions",
        "difficulty": "hard",
        "question": "Can the insurer cancel the commercial property policy mid-term, and what notice is required?",
        "ground_truth": "Yes, the insurer can cancel the policy mid-term but is subject to notice requirements. For cancellations due to non-payment of premium, a 10-day notice is required. For all other reasons (material misrepresentation, significant increase in hazard, policy conditions violation), a 30-day notice is required. After the first 60 days, the insurer's reasons for cancellation are limited to those specified above. The insured can cancel at any time with written notice. Upon cancellation, the insurer returns unearned premium on a pro-rata basis (or short-rate if insured cancels, per the policy terms).",
        "keywords": ["cancellation", "notice", "10 days", "30 days", "non-payment", "pro-rata"],
    },
]


def get_dataset() -> List[Dict[str, Any]]:
    """Return the full golden evaluation dataset."""
    return GOLDEN_DATASET


def get_dataset_by_category(category: str) -> List[Dict[str, Any]]:
    """Filter dataset by category."""
    return [q for q in GOLDEN_DATASET if q.get("category") == category]


def get_dataset_by_difficulty(difficulty: str) -> List[Dict[str, Any]]:
    """Filter dataset by difficulty."""
    return [q for q in GOLDEN_DATASET if q.get("difficulty") == difficulty]
