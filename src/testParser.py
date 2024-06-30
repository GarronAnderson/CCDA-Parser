"""
Test the parser on CCDAs.
"""

import parser

patient1 = parser.Parser(r"CCDAs\OFFICIAL Sample CCDA 1.xml")
patient2 = parser.Parser(r"CCDAs\OFFICIAL Sample CCDA 2.xml")
patient3 = parser.Parser(r'CCDAs\Patient-28.xml')
patients = [patient1, patient2, patient3]


for patient in patients:
    print(patient._filename)
    print("Name   ", patient.name)
    langs, prefs = patient.languages
    printme = list(zip(langs, prefs))
    print("Langs  ", *printme)
    print("Height  ", patient.height.feet,"' ", patient.height.inches, '"', sep='')
    print("Weight ", patient.weight)
    print("BMI    ", patient.bmi)
    print("DOB    ", patient.dob)
    print("Smoking Status ", patient.smoking_status)
    print("Address:\n", patient.address, sep='')
    print()


