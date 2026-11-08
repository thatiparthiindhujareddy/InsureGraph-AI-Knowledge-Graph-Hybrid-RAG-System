"""
InsureGraph AI — Sample Policy PDF Generator
Creates sample P&C insurance policy PDFs for testing and demonstration.
Run: python generate_sample_pdfs.py
"""
from pathlib import Path
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def create_sample_pdf(filename: str, title: str, content: str):
    """Create a simple PDF using basic PDF syntax (no external deps)."""
    # We'll create a text file that simulates a policy for ingestion
    path = Path("data/sample_policies") / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.with_suffix(".txt").write_text(content, encoding="utf-8")
    print(f"Created: {path.with_suffix('.txt')}")


COMMERCIAL_PROPERTY_POLICY = """COMMERCIAL PROPERTY INSURANCE POLICY
=====================================
Policy Number: CP-2024-DEMO-001
Policyholder: Meridian Business Group LLC
Named Insured: Meridian Business Group LLC, and subsidiaries
Insured Premises: 800 Commerce Boulevard, Suite 1200, Chicago, IL 60601
Policy Period: January 1, 2024 — January 1, 2025
Annual Premium: $18,500 | Quarterly Installment: $4,625

DECLARATIONS PAGE
═══════════════════════════════════════════
COVERAGE SUMMARY:
  Coverage A - Building:                    $2,500,000
  Coverage B - Business Personal Property:    $500,000
  Coverage C - Business Income:               $500,000
  Extra Expense:                              $100,000
  
DEDUCTIBLES:
  Standard Deductible (per occurrence):        $10,000
  Wind and Hail Deductible:                2% of building value
  Earthquake Deductible (if endorsed):     5% of building value
  Minimum Wind/Hail Deductible:             $5,000

═══════════════════════════════════════════

SECTION I — COVERAGE A: BUILDING
The insurer agrees to pay for direct physical loss or damage to the 
described building and structures, including:
- Completed additions
- Fixtures, machinery, and equipment permanently installed
- Personal property owned by the insured used for building service
- Materials and supplies on or adjacent to the described premises

COVERAGE LIMIT: $2,500,000 per occurrence
VALUATION BASIS: Replacement Cost Value (RCV)
COINSURANCE REQUIREMENT: 80% of replacement cost value

COINSURANCE CLAUSE: If at the time of loss the amount of insurance 
applicable is less than 80% of the full replacement cost value of the 
building, the insurer will pay only the proportion of any loss that the 
limit of insurance bears to 80% of the replacement cost value.

SECTION II — COVERAGE B: BUSINESS PERSONAL PROPERTY (BPP)
Coverage applies to business personal property located within the 
described building or within 100 feet of the premises:
- Furniture, fixtures, and equipment
- Stock and inventory
- All other personal property owned and used in business operations
- Labor, materials, or services furnished or arranged by the insured on
  personal property of others
  
COVERAGE LIMIT: $500,000
SUBLIMITS:
  - Outdoor Signs: $10,000 per sign, $25,000 total
  - Fences: $15,000 total
  - Electronic Data: $10,000
  - Accounts Receivable: $25,000
  - Fine Arts: $5,000

SECTION III — COVERAGE C: BUSINESS INCOME AND EXTRA EXPENSE

BUSINESS INCOME COVERAGE:
We will pay for the actual loss of Business Income you sustain due to 
the necessary suspension of your operations during the period of 
restoration. The suspension must be caused by direct physical loss or 
damage to property at the described premises.

BUSINESS INCOME LIMIT: $500,000
WAITING PERIOD: 72 hours (3 days) from the time of direct physical loss
MAXIMUM INDEMNITY PERIOD: 12 months from the date of direct loss

EXTRA EXPENSE COVERAGE:
We will pay necessary Extra Expense you incur during the period of 
restoration that you would not have incurred if there had been no 
direct physical loss or damage to property at the described premises.

EXTRA EXPENSE SUBLIMIT: $100,000 per occurrence
COVERED EXTRA EXPENSES INCLUDE:
- Costs to operate at temporary location
- Costs to move to and from temporary location  
- Costs to expedite permanent restoration
- Overtime labor and premium equipment rental
- Temporary utilities and communications

SECTION IV — COVERED CAUSES OF LOSS (SPECIAL FORM)
This policy is written on a SPECIAL FORM basis, meaning all direct 
physical loss to covered property is covered UNLESS it is specifically 
listed as an exclusion.

NAMED PERILS EXPLICITLY COVERED (for reference):
1. Fire and Lightning
2. Windstorm and Hail (subject to percentage deductible)
3. Explosion
4. Aircraft and Vehicles
5. Smoke damage
6. Vandalism and Malicious Mischief
7. Sprinkler Leakage
8. Sinkhole Collapse
9. Volcanic Action
10. Theft (building and BPP)
11. Weight of Ice, Snow, or Sleet
12. Water damage from plumbing, heating, or air conditioning systems
13. Falling Objects (exterior damage only)
14. Building glass breakage

SECTION V — EXCLUSIONS
The following losses are EXCLUDED from coverage:

1. FLOOD AND WATER INTRUSION
Damage caused by: flood, surface water, waves, tidal water, tidal wave, 
overflow of any body of water, storm surge, spray from any of the above, 
mudslide or mudflow, water that backs up or overflows from a sewer, drain 
or sump UNLESS caused by a covered cause of loss (pipe burst), water 
underground, water that seeps through foundations or walls.
NOTE: Flood coverage available by separate endorsement or NFIP policy.

2. EARTHQUAKE AND EARTH MOVEMENT
Damage caused by: earthquake, volcanic eruption (other than volcanic 
action as defined), landslide, mine subsidence, earth sinking, rising 
or shifting, mudflow.
NOTE: Earthquake coverage available by endorsement, typically with 
2-10% deductible of insured value.

3. GOVERNMENTAL ACTION
Seizure or destruction of property by order of government authority.
NOTE: Actions taken to prevent the spread of a fire are covered.

4. NUCLEAR HAZARD
Any weapon employing atomic fission or fusion, or nuclear reaction or 
radiation.

5. UTILITY SERVICES FAILURE
Loss resulting from failure of power or other utility service supplied 
to the described premises. 
NOTE: Off-premises power failure endorsement available.

6. WAR AND MILITARY ACTION
War, including undeclared war, civil war, insurrection, rebellion, 
revolution, warlike action by a military force.

7. WEAR, TEAR, AND DETERIORATION
Wear and tear, deterioration, hidden or latent defect, gradual 
deterioration, rust, corrosion, decay, or smog damage.

8. MECHANICAL AND ELECTRICAL BREAKDOWN
Mechanical breakdown, including rupture or bursting caused by centrifugal 
force; electrical injury or disturbance to electrical devices, appliances 
or wiring. NOTE: Equipment Breakdown Coverage available by endorsement.

9. FAULTY DESIGN OR CONSTRUCTION
Loss or damage caused by or resulting from faulty, inadequate or 
defective planning, zoning, development, surveying, siting, design, 
specifications, workmanship, repair, construction, renovation, 
remodeling, grading, or compaction of property.

10. EMPLOYEE DISHONESTY AND THEFT BY EMPLOYEES
Dishonest or criminal acts by the insured, partners, members, managers, 
directors, trustees, or authorized representatives; employees, leased 
workers, or temporary workers.
NOTE: Employee Dishonesty coverage available through Crime Insurance.

11. MOLD, FUNGUS, AND WET ROT
Loss due to mold, fungus, wet rot or dry rot. Exception: If mold, 
fungus, wet rot or dry rot results from a covered cause of loss (e.g., 
burst pipe) and the loss is reported within 30 days, coverage applies 
subject to a $50,000 sublimit.

SECTION VI — ADDITIONAL CONDITIONS

COINSURANCE: If you do not maintain insurance at least equal to 80% of 
the replacement cost, we will pay only the proportion of any loss that 
our limit bears to 80% of the full replacement cost value.

VACANCY: If a building is vacant for more than 60 days before a loss:
- Vandalism losses are excluded entirely
- All other covered losses are paid at only 85% of what would otherwise 
  be payable

VALUATION: We will pay the cost to repair or replace with new materials 
of similar kind and quality (Replacement Cost Value) provided the 
property is actually repaired or replaced within 2 years of the loss.

INFLATION GUARD: Coverage increases automatically by 8% per year.

SECTION VII — POLICY CONDITIONS

DUTIES OF THE INSURED AFTER A LOSS:
In the event of loss or damage, the insured must:
1. Notify us as soon as practicable by telephone and confirm in writing
2. Notify the police if a law may have been broken (theft, vandalism)
3. Take all reasonable steps to protect the property from further damage
   (we will pay reasonable costs for this protection)
4. Keep accurate records of all expenses incurred to protect property
5. Cooperate fully with us in the investigation and settlement of claims
6. Permit us to inspect the property and your records
7. Send us a signed sworn Proof of Loss within 60 days after our request
8. Submit to examination under oath at our request
9. Authorize us to obtain records and documents related to the claim
10. Provide us with building plans and specifications if requested

PROOF OF LOSS: Must be sworn and notarized. Must include:
- Date and cause of loss
- Interest of insured and all others in the property
- Other insurance covering the property  
- List of all damaged property
- Amount of claimed loss or damage

CANCELLATION AND NONRENEWAL:
Non-payment of Premium: We may cancel by mailing 10 days written notice.
Other Cancellations: We may cancel by mailing 30 days written notice.
After 60 days: We may only cancel for: (1) non-payment of premium, 
(2) material misrepresentation, or (3) significant change in risk.
Nonrenewal: We will mail 60 days advance notice of nonrenewal.
Return Premium: Pro-rata if we cancel; short-rate if insured cancels.

APPRAISAL: If we and the insured disagree on the value of property or 
the amount of loss, either party may demand an appraisal of the loss. 
Each party will select a qualified appraiser within 20 days. The two 
appraisers will select an umpire. Agreement by any two of the three 
will set the amount of loss.

SUBROGATION: We will be entitled to the rights of the insured against 
others relating to the loss. The insured must not impair our rights.

SECTION VIII — ENDORSEMENTS ATTACHED:
- CP 04 17: Outdoor Signs Extension
- CP 04 05: Business Personal Property - Seasonal Increase (25%)
- CP 15 10: Builders Risk
- IL 09 85: Disclosure of Premium - Policyholder Notice

END OF POLICY
Policy Number: CP-2024-DEMO-001
Meridian Insurance Company, Dallas TX
Licensed in all 50 states and D.C.
"""

if __name__ == "__main__":
    Path("data/sample_policies").mkdir(parents=True, exist_ok=True)

    create_sample_pdf(
        "commercial_property_policy",
        "Commercial Property Policy CP-2024-DEMO-001",
        COMMERCIAL_PROPERTY_POLICY,
    )

    print("\n✅ Sample policy files created in data/sample_policies/")
    print("You can ingest these via the API: POST /api/ingest/text")
    print("Or use the frontend 'Load Sample Policy' buttons")
