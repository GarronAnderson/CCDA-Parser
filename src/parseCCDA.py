"""
Old (but working) version of a CCDA parser.

Will be removed and replaced with the OOP parser.

Was just meant to be a test area.
"""

import pprint
import xmltodict
from datetime import datetime
from iso639 import Lang
from codeData import *

ccda_filename = "Patient-28.xml"

with open(ccda_filename) as ccda:
    ccda_text = ccda.read()
    ccda_data = xmltodict.parse(ccda_text)

patientRole = ccda_data["ClinicalDocument"]["recordTarget"]["patientRole"]
patient = patientRole["patient"]

try:
    patientGivenName = patient["name"]["given"]["#text"]
except TypeError:
    patientGivenName = patient["name"]["given"]

try:
    patientFamilyName = patient["name"]["family"]["#text"]
except TypeError:
    patientFamilyName = patient["name"]["family"]

patientGender = patient["administrativeGenderCode"].get("@displayName", "no info")


patientDOBRaw = patient["birthTime"]["@value"][:8]
patientDOB = datetime.strptime(patientDOBRaw, "%Y%m%d").strftime("%m/%d/%Y")

patientRace = patient["raceCode"].get("@displayName", "no info")
patientEthnicity = patient["ethnicGroupCode"].get("@displayName", "no info")

patientLanguageCode = patient["languageCommunication"]["languageCode"].get(
    "@code", "no info"
)
try:
    patientLanguagePreferred = {"true": "yes", "false": "no"}[
        patient["languageCommunication"]["preferenceInd"]["@value"]
    ]
except KeyError:
    patientLanguagePreferred = "N/A"

patientAddrLine = patientRole["addr"]["streetAddressLine"]
patientAddrCity = patientRole["addr"]["city"]
patientAddrState = patientRole["addr"]["state"]
patientAddrZIP = patientRole["addr"]["postalCode"]
patientAddrCountry = patientRole["addr"]["country"]

patientAddr = (
    patientAddrLine
    + "\n"
    + patientAddrCity
    + ", "
    + patientAddrState
    + " "
    + patientAddrZIP
    + "\n"
    + patientAddrCountry
)

patientPhoneType = hl7_phone_codes[patientRole["telecom"]["@use"]]
patientPhoneNumber = patientRole["telecom"]["@value"][4:]

components = ccda_data["ClinicalDocument"]["component"]["structuredBody"]["component"]
component_list = []
for i in range(len(components)):
    component_list.append(components[i]["section"]["code"]["@code"])

vital_signs_index = component_list.index(reverse_loinc_codes["Vital Signs"])
vital_signs = components[vital_signs_index]["section"]["entry"]["organizer"][
    "component"
]

vital_signs_list = []
for i in range(len(vital_signs)):
    vital_signs_list.append(vital_signs[i]["observation"]["code"]["@code"])

height_index = vital_signs_list.index(reverse_loinc_codes["Height"])
weight_index = vital_signs_list.index(reverse_loinc_codes["Weight"])
bmi_index = vital_signs_list.index(reverse_loinc_codes["BMI"])

height_val = vital_signs[height_index]["observation"]["value"]["@value"]
height_unit = vital_signs[height_index]["observation"]["value"]["@unit"]

weight_val = vital_signs[weight_index]["observation"]["value"]["@value"]
weight_unit = vital_signs[weight_index]["observation"]["value"]["@unit"]

bmi = vital_signs[bmi_index]["observation"]["value"]["@value"]
bmi_unit = vital_signs[bmi_index]["observation"]["value"].get("@unit", "")

smoking_index = component_list.index(reverse_loinc_codes["Social History"])

smoking_status = snomed_codes[
    components[smoking_index]["section"]["entry"]["observation"]["value"].get(
        "@code", "no info"
    )
]
smoking_date = components[smoking_index]["section"]["entry"]["observation"][
    "effectiveTime"
]["low"].get("@value", "N/A")

print("Name: ", patientFamilyName, ", ", patientGivenName, sep="")
print()
print("Gender:", patientGender)
print("DOB:", patientDOB)
print()
print("Address:\n", patientAddr, sep="")
print(patientPhoneType, ": ", patientPhoneNumber, sep="")
print()
print("Race:", patientRace)
print("Ethnicity:", patientEthnicity)
if patientLanguageCode != "no info":
    print(
        "Language: ",
        Lang(patientLanguageCode).name,
        ", preferred: ",
        patientLanguagePreferred,
        sep="",
    )
else:
    print(
        "Language: ",
        patientLanguageCode,
        ", preferred: ",
        patientLanguagePreferred,
        sep="",
    )
print()
print("Height:", height_val, height_unit)
print("Weight:", weight_val, weight_unit)
print("BMI: ", bmi, bmi_unit)
print()
print("Smoking Status:", smoking_status, "<as of", smoking_date, "\b>")
