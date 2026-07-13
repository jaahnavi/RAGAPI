# Generates samples/employer-plan-summary-sample.pdf
# Run: pip install fpdf2 && python scripts/generate_sample_pdf.py

import os
from fpdf import FPDF

OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "samples",
    "employer-plan-summary-sample.pdf",
)


class PlanPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Acme Corp Health Plan — Summary of Benefits", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, "Plan Year: January 1 – December 31  |  Synthetic Educational Document", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}  |  This is a synthetic educational document, not a real insurance filing.", align="C")

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 12)
        self.set_fill_color(220, 230, 240)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(2)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def two_col_row(self, label: str, value: str):
        self.set_font("Helvetica", "B", 10)
        self.cell(90, 7, label)
        self.set_font("Helvetica", "", 10)
        self.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")

    def table_header(self, col1: str, col2: str, col3: str):
        self.set_font("Helvetica", "B", 10)
        self.set_fill_color(200, 215, 235)
        self.cell(70, 7, col1, border=1, fill=True)
        self.cell(60, 7, col2, border=1, fill=True)
        self.cell(60, 7, col3, border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

    def table_row(self, col1: str, col2: str, col3: str, fill: bool = False):
        self.set_font("Helvetica", "", 9)
        if fill:
            self.set_fill_color(240, 245, 250)
        self.cell(70, 6, col1, border=1, fill=fill)
        self.cell(60, 6, col2, border=1, fill=fill)
        self.cell(60, 6, col3, border=1, fill=fill, new_x="LMARGIN", new_y="NEXT")


def generate():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    pdf = PlanPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # --- Section 1: Plan Overview ---
    pdf.section_title("Section 1: Plan Overview")
    pdf.body_text(
        "This document summarizes the key benefits and cost-sharing features of the Acme Corp "
        "Preferred Provider Organization (PPO) health plan. It is provided for educational purposes "
        "only and does not constitute a legally binding Summary Plan Description (SPD). "
        "Always consult your official plan documents for complete details.\n\n"
        "Disclaimer: This is a synthetic educational document. It does not provide medical, legal, "
        "or enrollment advice. Do not use this document for actual coverage decisions."
    )

    # --- Section 2: Deductibles & Out-of-Pocket Maximum ---
    pdf.section_title("Section 2: Deductibles and Out-of-Pocket Maximum")
    pdf.body_text(
        "The deductible is the amount you pay for covered health care services before your insurance "
        "plan starts to pay. After you meet your deductible, you usually pay only a copayment or "
        "coinsurance for covered services, and your insurance company pays the rest up to the "
        "allowed amount."
    )

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Annual Deductible", new_x="LMARGIN", new_y="NEXT")
    pdf.two_col_row("In-Network (Individual):", "$1,500 / calendar year")
    pdf.two_col_row("In-Network (Family):", "$3,000 / calendar year")
    pdf.two_col_row("Out-of-Network (Individual):", "$3,000 / calendar year")
    pdf.two_col_row("Out-of-Network (Family):", "$6,000 / calendar year")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Out-of-Pocket Maximum", new_x="LMARGIN", new_y="NEXT")
    pdf.body_text(
        "The out-of-pocket maximum is the most you have to pay for covered services in a plan year. "
        "After you spend this amount on deductibles, copayments, and coinsurance, your health plan "
        "pays 100% of the costs of covered benefits."
    )
    pdf.two_col_row("In-Network (Individual):", "$6,500 / calendar year")
    pdf.two_col_row("In-Network (Family):", "$13,000 / calendar year")
    pdf.two_col_row("Out-of-Network (Individual):", "$12,000 / calendar year")
    pdf.two_col_row("Out-of-Network (Family):", "$24,000 / calendar year")
    pdf.ln(4)

    # --- Section 3: Cost-Sharing Schedule ---
    pdf.section_title("Section 3: Cost-Sharing Schedule")
    pdf.body_text(
        "The following table summarizes your cost-sharing responsibilities for common services. "
        "All amounts listed assume you are using in-network providers unless otherwise noted. "
        "Cost-sharing applies after the deductible is met unless the service is marked as "
        "deductible-exempt."
    )

    pdf.table_header("Service", "In-Network", "Out-of-Network")
    rows = [
        ("Primary Care Visit", "$20 copay (deductible-exempt)", "30% after deductible"),
        ("Specialist Visit", "$40 copay (deductible-exempt)", "40% after deductible"),
        ("Preventive Care", "$0 (no cost sharing)", "Not covered"),
        ("Urgent Care", "$75 copay", "40% after deductible"),
        ("Emergency Room", "$300 copay + 20%", "$300 copay + 20%"),
        ("Inpatient Hospital", "20% after deductible", "40% after deductible"),
        ("Outpatient Surgery", "20% after deductible", "40% after deductible"),
        ("Lab / Pathology", "10% after deductible", "30% after deductible"),
        ("Imaging (X-ray)", "10% after deductible", "30% after deductible"),
        ("MRI / CT / PET Scan", "20% after deductible", "40% after deductible"),
        ("Physical Therapy (max 30/yr)", "$40 copay", "40% after deductible"),
        ("Mental Health - Outpatient", "$20 copay", "30% after deductible"),
        ("Mental Health - Inpatient", "20% after deductible", "40% after deductible"),
    ]
    for i, (s, inn, oon) in enumerate(rows):
        pdf.table_row(s, inn, oon, fill=(i % 2 == 0))
    pdf.ln(4)

    # --- Section 4: Telehealth ---
    pdf.section_title("Section 4: Telehealth Benefits")
    pdf.body_text(
        "This plan covers telehealth visits for eligible members. Telehealth services allow you to "
        "consult with a licensed health care provider via video or phone from the convenience of "
        "your home or any location with an internet connection.\n\n"
        "Telehealth services must be provided through an approved telehealth platform designated by "
        "the plan administrator. Using non-approved platforms may result in the visit being processed "
        "as an out-of-network service or denied entirely."
    )
    pdf.two_col_row("Telehealth (General / Primary Care):", "$25 copay per visit via approved platform")
    pdf.two_col_row("Telehealth (Behavioral Health):", "$20 copay per visit via approved platform")
    pdf.two_col_row("Approved Platform:", "Acme Health Virtual Care Portal")
    pdf.two_col_row("Availability:", "24 hours a day, 7 days a week")
    pdf.two_col_row("Prescription fulfillment:", "Available for eligible medications during visit")
    pdf.ln(4)
    pdf.body_text(
        "Note: Telehealth services are subject to applicable deductibles and out-of-pocket maximums "
        "unless the copay is deductible-exempt as noted above."
    )

    # --- Section 5: Prescription Drug Coverage ---
    pdf.add_page()
    pdf.section_title("Section 5: Prescription Drug Coverage")
    pdf.body_text(
        "This plan uses a four-tier drug formulary. The formulary is the list of prescription drugs "
        "covered by the plan. Drugs not on the formulary may require a prior authorization request or "
        "may not be covered. You can access the current formulary through the member portal or by "
        "contacting member services."
    )

    pdf.table_header("Tier", "Drug Type", "Member Cost (30-day supply)")
    drug_rows = [
        ("Tier 1", "Generic drugs", "$10 copay"),
        ("Tier 2", "Preferred brand-name drugs", "$35 copay"),
        ("Tier 3", "Non-preferred brand-name drugs", "$70 copay"),
        ("Tier 4", "Specialty drugs", "25% coinsurance (max $250/fill)"),
    ]
    for i, row in enumerate(drug_rows):
        pdf.table_row(*row, fill=(i % 2 == 0))
    pdf.ln(4)
    pdf.body_text(
        "90-day supply (mail order): Tiers 1–3 are available at 2.5x the 30-day copay via mail order. "
        "Specialty drugs (Tier 4) must be dispensed through the plan's specialty pharmacy network."
    )

    # --- Section 6: Prior Authorization ---
    pdf.section_title("Section 6: Prior Authorization Requirements")
    pdf.body_text(
        "Prior authorization (PA) is a requirement by the health plan to obtain approval for certain "
        "services, procedures, or medications before they are provided. Failure to obtain required "
        "prior authorization may result in denial of the claim or reduced benefits.\n\n"
        "The following services require prior authorization before they are performed or initiated. "
        "Your in-network provider is responsible for submitting the prior authorization request to the "
        "plan on your behalf, but you should confirm that authorization has been obtained before "
        "receiving services."
    )

    pa_services = [
        "Inpatient hospital admissions (except emergency)",
        "MRI, CT, and PET scans",
        "Specialty tier prescription drugs on the plan formulary",
        "Bariatric surgery",
        "Home health care exceeding 10 visits",
    ]

    pdf.set_font("Helvetica", "", 10)
    for item in pa_services:
        pdf.cell(8, 6, chr(149))  # bullet character
        pdf.cell(0, 6, item, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.body_text(
        "Emergency services do not require prior authorization. However, you should notify the plan "
        "within 48 hours of an emergency admission or as soon as reasonably possible.\n\n"
        "To initiate a prior authorization request, contact Member Services at 1-800-555-ACME "
        "(1-800-555-2263) or submit via the member portal. Decisions are typically rendered within "
        "3 business days for non-urgent requests and within 24 hours for urgent/expedited requests."
    )

    # --- Section 7: Exclusions and Limitations ---
    pdf.section_title("Section 7: Exclusions and Limitations")
    pdf.body_text(
        "The following services and items are generally NOT covered under this plan. This list is "
        "not exhaustive. Refer to your full Summary Plan Description for a complete list of exclusions."
    )

    exclusions = [
        "Routine dental care (exams, cleanings, fillings, orthodontia) — covered under separate dental plan",
        "Routine vision care (eye exams, eyeglasses, contact lenses) — covered under separate vision plan",
        "Cosmetic surgery or procedures not medically necessary",
        "Weight loss programs (unless medically necessary and prior authorized)",
        "Experimental, investigational, or unproven treatments",
        "Services received outside the United States (except emergencies)",
        "Long-term custodial care",
    ]

    pdf.set_font("Helvetica", "", 10)
    for item in exclusions:
        pdf.cell(8, 6, chr(149))
        pdf.cell(0, 6, item, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # --- Section 8: How to Use Your Benefits ---
    pdf.section_title("Section 8: How to Use Your Benefits")
    pdf.body_text(
        "1. Choose an in-network provider: Using in-network providers saves you money. You can search "
        "for in-network providers using the online provider directory at acmehealthplan.example.com/find-a-doctor.\n\n"
        "2. Present your insurance card: Show your Acme Corp health plan ID card at every visit.\n\n"
        "3. Pay your share: You are responsible for any applicable copay at the time of service.\n\n"
        "4. Review your Explanation of Benefits (EOB): After each claim is processed, you will receive "
        "an EOB showing what the plan paid and what you owe.\n\n"
        "5. Appeal a denied claim: If a claim is denied, you have the right to appeal. Contact Member "
        "Services within 180 days of receiving the denial notice."
    )

    # --- Footer disclaimer ---
    pdf.add_page()
    pdf.section_title("Important Notices")
    pdf.body_text(
        "DISCLAIMER: This document is a synthetic educational sample created for training and "
        "demonstration purposes only. It does not represent a real insurance plan, real coverage "
        "terms, or real benefit amounts. Any resemblance to actual plan documents is coincidental.\n\n"
        "This document should NOT be used to make actual insurance or health care decisions. "
        "Do not upload documents containing Protected Health Information (PHI), including real "
        "Social Security Numbers, member IDs, or personal health records.\n\n"
        "Summary of Key Benefits (for quick reference):\n"
        "  - In-network individual deductible: $1,500 / calendar year\n"
        "  - In-network individual out-of-pocket maximum: $6,500 / calendar year\n"
        "  - Telehealth: Covered at $25 copay per visit via approved platform\n"
        "  - Prior authorization: Required for inpatient, MRI/CT/PET, specialty drugs, "
        "bariatric surgery, extended home health care"
    )

    pdf.output(OUTPUT_PATH)
    print(f"Generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    generate()
