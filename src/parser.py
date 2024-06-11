"""
CCDA Parser

By Garron Anderson"""

import sqlite3 as sqlite

import xmltodict


class Parser:
    def __init__(self, filename):
        with open(filename) as ccda:
            ccda_text = ccda.read()
            self.ccda_data = xmltodict.parse(ccda_text)

        self.patientRole = ccda_data["ClinicalDocument"]["recordTarget"]["patientRole"]
        self.patient = patientRole["patient"]

        self.components = ccda_data["ClinicalDocument"]["component"]["structuredBody"][
            "component"
        ]

        self.db_conn = sqlite.connect("codeData.db")
        self.db_cursor = self.db_conn.cursor()

        def name(self):
            """
            Retrieve the patients name.
            """
            try:
                patientGivenName = self.patient["name"]["given"]["#text"]
                patientFamilyName = self.patient["name"]["family"]["#text"]
            except TypeError:
                patientGivenName = self.patient["name"]["given"]
                patientFamilyName = self.patient["name"]["family"]

            return patientGivenName + " " + patientFamilyName

        def gender(self):
            """
            Retrieve the patient's gender.
            """

            return self.patient["administrativeGenderCode"].get(
                "@displayName", "no info"
            )

        def DOB(self):
            """
            Retrieve the patients date of birth.
            """

            try:
                patientDOBRaw = self.patient["birthTime"]["@value"][:8]
                patientDOB = datetime.strptime(patientDOBRaw, "%Y%m%d").strftime(
                    "%m/%d/%Y"
                )
            except KeyError:
                patientDOB = "no info"

            return patientDOB

        def race_ethnicity(self):
            patientRace = self.patient["raceCode"].get("@displayName", "no info")
            patientEthnicity = self.patient["ethnicGroupCode"].get(
                "@displayName", "no info"
            )

            return patientRace, patientEthnicity

        def address(self):
            try:
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
                
            except KeyError:
                patientAddr = 'no info'
            
            return patientAddr