"""
Raw data (as dicts) of the codes and mappings.

Currently being replaced by a SQLite database.
"""

loinc_codes = {
    "48765-2": "Allergies, Adverse Reactions, Alerts",
    "51847-2": "Assessment and Plan",
    "46239-0": "Chief Complaint and Reason For Visit",
    "46240-8": "History of Encounters",
    "11369-6": "History of Immunizations",
    "69730-0": "Instructions",
    "10160-0": "History of Medication Use",
    "11450-4": "Problem List",
    "47519-4": "Procedures",
    "30954-2": "Results",
    "29762-2": "Social History",
    "8716-3": "Vital Signs",
    "48765-2": "Allergies, Adverse Reactions, Alerts",
    "9279-1": "Respiratory Rate",
    "8867-4": "Heart Rate",
    "8480-6": "Systolic BP",
    "8462-4": "Diastolic BP",
    "8302-2": "Height",
    "8287-5": "Head Circumference",
    "3141-9": "Weight",
    "39156-5": "BMI",
}

reverse_loinc_codes = {
    "Allergies, Adverse Reactions, Alerts": "48765-2",
    "Assessment and Plan": "51847-2",
    "BMI": "39156-5",
    "Chief Complaint and Reason For Visit": "46239-0",
    "Diastolic BP": "8462-4",
    "Head Circumference": "8287-5",
    "Heart Rate": "8867-4",
    "Height": "8302-2",
    "History of Encounters": "46240-8",
    "History of Immunizations": "11369-6",
    "History of Medication Use": "10160-0",
    "Instructions": "69730-0",
    "Problem List": "11450-4",
    "Procedures": "47519-4",
    "Respiratory Rate": "9279-1",
    "Results": "30954-2",
    "Social History": "29762-2",
    "Systolic BP": "8480-6",
    "Vital Signs": "8716-3",
    "Weight": "3141-9",
}

snomed_codes = {
    "266919005": "Never smoker",
    "266927001": "Unknown if ever smoked",
    "428041000124106": "Current some day smoker",
    "428061000124105": "Current Light tobacco smoker",
    "428071000124103": "Current Heavy tobacco smoker",
    "449868002": "Current every day smoker",
    "77176002": "Smoker, current status unknown",
    "8517006": "Former smoker",
    "no info": "no info",
}

reverse_snomed_codes = {
    "Current Heavy tobacco smoker": "428071000124103",
    "Current Light tobacco smoker": "428061000124105",
    "Current every day smoker": "449868002",
    "Current some day smoker": "428041000124106",
    "Former smoker": "8517006",
    "Never smoker": "266919005",
    "Smoker, current status unknown": "77176002",
    "Unknown if ever smoked": "266927001",
}


hl7_phone_codes = {
    "AS": "answering service",
    "BAD": "bad address",
    "DIR": "direct",
    "EC": "emergency contact",
    "H": "home address",
    "HP": "primary home",
    "HV": "vacation home",
    "MC": "mobile contact",
    "PG": "pager",
    "PUB": "public",
    "TMP": "temporary address",
    "WP": "work place",
}
