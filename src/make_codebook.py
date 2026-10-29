"""
Build a codebook: one row per code in a downloaded Eurostat dataset.

It reads the raw JSON saved by ingest_eurostat.py, so the official labels come straight
from Eurostat. A plain-English note and the project question each code helps answer are
added from NOTES below; codes marked "check" are best guesses, so confirm against the
official label.

Run it from the project folder (after ingest_eurostat.py):
    python src/make_codebook.py              # default dataset
    python src/make_codebook.py isoc_eb_ain2 # another dataset
"""

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
OUT_DIR = PROJECT_DIR / "docs"

# code -> (plain-English note, project question it helps answer)
NOTES = {
    # size_emp
    "0_1": ("0 to 1 person employed", "UK comparison"),
    "0-9": ("Micro firms, 0 to 9 people", "UK comparison"),
    "2-9": ("2 to 9 people", "UK comparison"),
    "10-49": ("SMALL firms", "All"),
    "50-249": ("MEDIUM firms", "All"),
    "GE250": ("LARGE firms, 250 or more", "All"),
    "10-249": ("Small and medium together (SMEs)", "Context"),
    "GE10": ("All firms with 10 or more people (the total)", "Context"),
    # unit
    "PC_ENT": ("% of ALL firms in the group", "Q1, Q2"),
    "PC_ENT_IUSE": ("% of firms whose staff have internet access", "Rarely needed"),
    "PC_ENT_AI_EC": ("% of non-users that ever CONSIDERED AI", "Q3 reasons"),
    "PC_ENT_AI_TANY": ("% of firms that USE AI", "Q4 purposes"),
    "PC_ENT_AI_TX": ("% of firms that do NOT use AI", "Q3"),
    "PC_ENT_AI_PDI": ("% of firms processing personal data with AI", "Rarely needed"),
    # indic_is: AI technologies
    "E_AI_TTM": ("Uses AI for text mining (analysing written text)", "Q4 technology"),
    "E_AI_TSR": ("Uses speech recognition", "Q4 technology"),
    "E_AI_TNLG": ("Uses AI to generate text, speech or code (e.g. chatbots)", "Q4 technology"),
    "E_AI_TIR": ("Uses image recognition", "Q4 technology"),
    "E_AI_TML": ("Uses machine learning for data analysis", "Q4 technology"),
    "E_AI_TPA": ("Uses AI to automate workflows or support decisions", "Q4 technology"),
    "E_AI_TAR": ("Uses autonomous robots, vehicles or drones", "Q4 technology"),
    "E_AI_TPVSG": ("Uses AI to generate pictures, video or sound", "Q4 technology"),
    "E_AI_TANY": ("Uses AT LEAST ONE AI technology (main adoption measure)", "Q1, Q2"),
    "E_AI_TX": ("Uses NO AI technology", "Q1"),
    "E_AI_TGE2": ("Uses 2 or more AI technologies (depth of use)", "Q1 depth"),
    "E_AI_TGE3": ("Uses 3 or more AI technologies (depth of use)", "Q1 depth"),
    # indic_is: purposes
    "E_AI_PMS": ("AI for marketing or sales", "Q4 purpose"),
    "E_AI_PPP": ("AI for production processes", "Q4 purpose"),
    "E_AI_PBA": ("AI for business administration (older wording)", "Q4 purpose"),
    "E_AI_PME": ("AI for management (older wording)", "Q4 purpose"),
    "E_AI_PBAM": ("AI for business administration and management", "Q4 purpose"),
    "E_AI_PLOG": ("AI for logistics", "Q4 purpose"),
    "E_AI_PITS": ("AI for ICT security", "Q4 purpose"),
    "E_AI_PHR": ("AI for HR or recruitment", "Q4 purpose"),
    "E_AI_PFIN": ("AI for accounting or finance (check)", "Q4 purpose"),
    "E_AI_PRDI": ("AI for R&D or innovation (check)", "Q4 purpose"),
    "E_AI_P1ANY": ("Uses AI for at least one listed purpose (check)", "Q4 purpose"),
    "E_AI_P1GE2": ("Uses AI for 2 or more purposes (check)", "Q4 purpose"),
    "E_AI_P1GE3": ("Uses AI for 3 or more purposes (check)", "Q4 purpose"),
    # indic_is: how AI was obtained
    "E_AI_ADOWN": ("AI built by the firm's own staff", "Q4 / why"),
    "E_AI_AMOWN": ("Bought AI software modified by own staff", "Q4 / why"),
    "E_AI_AOS": ("Open-source AI modified by own staff", "Q4 / why"),
    "E_AI_ARDY": ("Ready-to-use commercial AI product", "Q4 / why"),
    "E_AI_AEXT": ("AI built or modified by an external provider", "Q4 / why"),
    # indic_is: considered and reasons for not using
    "E_AI_EC": ("Non-user that has EVER CONSIDERED using AI", "Q3"),
    "E_AI_BCST": ("Reason: costs seem too high", "Q3 reason"),
    "E_AI_BLE": ("Reason: lack of relevant expertise", "Q3 reason"),
    "E_AI_BINC": ("Reason: incompatible with existing systems", "Q3 reason"),
    "E_AI_BDDT": ("Reason: data not available or poor quality", "Q3 reason"),
    "E_AI_BCDP": ("Reason: data protection and privacy concerns", "Q3 reason"),
    "E_AI_BLEG": ("Reason: unclear legal consequences", "Q3 reason"),
    "E_AI_BEC": ("Reason: ethical concerns", "Q3 reason"),
    "E_AI_BNU": ("Reason: AI not useful for the firm", "Q3 reason"),
    # indic_is: digital foundations (AIX = no AI, ...X = not)
    "E_AI_DA": ("Uses AI and data analytics (check)", "Why: foundations"),
    "E_AI_CC": ("Uses AI and cloud computing (check)", "Why: foundations"),
    "E_AI_CC1SI_DA": ("AI + cloud + data analytics (check)", "Why: foundations"),
    "E_AIX_CC1SI_DA": ("No AI, but cloud + data analytics (check)", "Why: foundations"),
    "E_AI_CC1SIX_DA": ("AI + data analytics, no cloud (check)", "Why: foundations"),
    "E_AI_CC1SI_DAX": ("AI + cloud, no data analytics (check)", "Why: foundations"),
    "E_AIX_CC1SI_DAX": ("Cloud only (check)", "Why: foundations"),
    "E_AI_CC1SIX_DAX": ("AI only, no cloud or data analytics (check)", "Why: foundations"),
    "E_AIX_CC1SIX_DA": ("Data analytics only (check)", "Why: foundations"),
    "E_AI_CC1SI_DASANY": ("AI + cloud + any data analytics source (check)", "Why: foundations"),
    "E_AI_CC1SI_DASGE3": ("AI + cloud + 3 or more data analytics sources (check)", "Why: foundations"),
    "E_AI_CC1SI_DASANY2": ("AI + cloud + data analytics, variant (check)", "Why: foundations"),
    "E_AI_CC1SI_DA_ANY": ("AI, cloud or data analytics, any of them (check)", "Why: foundations"),
    "E_DI3_VLO_AI_TANY": ("Uses AI, VERY LOW digital intensity firm", "Why: foundations"),
    "E_DI3_LO_AI_TANY": ("Uses AI, LOW digital intensity firm", "Why: foundations"),
    "E_DI3_HI_AI_TANY": ("Uses AI, HIGH digital intensity firm", "Why: foundations"),
    "E_DI3_VHI_AI_TANY": ("Uses AI, VERY HIGH digital intensity firm", "Why: foundations"),
    # indic_is: other
    "E_AI_PDI": ("Processes data on individuals with AI", "Rarely needed"),
    "E_AI_BIAS": ("Measures against AI bias (check)", "Rarely needed"),
    "E_AI_BIAS_ADOWN": ("Bias measures, AI built in-house (check)", "Rarely needed"),
    "E_AI_BIAS_AMOWN": ("Bias measures, bought AI modified in-house (check)", "Rarely needed"),
    "E_AI_BIAS_AOS": ("Bias measures, open-source AI (check)", "Rarely needed"),
    "E_AI_BIAS_ARDY": ("Bias measures, ready-to-use AI (check)", "Rarely needed"),
    "E_AI_BIAS_AEXT": ("Bias measures, AI from external provider (check)", "Rarely needed"),
    # geo totals
    "EU27_2020": ("EU total, 27 countries", "Benchmark"),
    "EA": ("Euro area total", "Benchmark"),
}


def build_codebook(code: str) -> pd.DataFrame:
    data = json.loads((RAW_DIR / f"{code}.json").read_text(encoding="utf-8"))
    rows = []
    for dim_id in data["id"]:
        for item, label in data["dimension"][dim_id]["category"]["label"].items():
            note, question = NOTES.get(item, ("", ""))
            rows.append({
                "dataset": code,
                "column": dim_id,
                "code": item,
                "official_label": label,
                "plain_english": note,
                "used_for": question,
            })
    return pd.DataFrame(rows)


def main() -> None:
    code = sys.argv[1] if len(sys.argv) > 1 else "isoc_eb_ai"
    codebook = build_codebook(code)
    OUT_DIR.mkdir(exist_ok=True)
    csv_path = OUT_DIR / f"codebook_{code}.csv"
    codebook.to_csv(csv_path, index=False)
    print(f"{len(codebook)} codes written to {csv_path}")


if __name__ == "__main__":
    main()
