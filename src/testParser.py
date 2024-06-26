"""
Test the parser on a CCDA.
"""

import parser

patient = parser.Parser(r"CCDAs\Sample CCDA 2.xml")

print(patient.name)
print("Height", patient.height)
print(patient.smoking_status)
