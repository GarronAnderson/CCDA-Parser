"""
CCDA Parser

By Garron Anderson"""

import sqlite3 as sqlite
import datetime

import xmltodict

class ParserException(Exception):
    """A class for when the parser raises an exception."""
    pass

class Parser:
    """Parse CCDA files."""
    def __init__(self, filename):
        with open(filename) as ccda:
            ccda_text = ccda.read()
            self.ccda_data = xmltodict.parse(ccda_text)

        self.patientRole = self.ccda_data["ClinicalDocument"]["recordTarget"]["patientRole"]
        self.patient = self.patientRole["patient"]

        self.components = self.ccda_data["ClinicalDocument"]["component"]["structuredBody"]["component"]
        self.component_list = []
        for i in range(len(self.components)):
            self.component_list.append(self.components[i]["section"]["code"]["@code"])

        self.db_conn = sqlite.connect("codeDatabase.db")
        self.db_cursor = self.db_conn.cursor()

    def name(self):
        """
        Retrieve the patient's name.
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
        Retrieve the patient's date of birth.
        """

        try:
            patientDOBRaw = self.patient["birthTime"]["@value"][:8]
            patientDOB = datetime.datetime.strptime(patientDOBRaw, "%Y%m%d").strftime(
                "%m/%d/%Y"
            )
        except KeyError:
            patientDOB = "no info"

        return patientDOB

    def race_ethnicity(self):
        """
        Retrieve the patient's race and ethnicity (as a tuple).
        """
        patientRace = self.patient["raceCode"].get("@displayName", "no info")
        patientEthnicity = self.patient["ethnicGroupCode"].get(
            "@displayName", "no info"
        )

        return patientRace, patientEthnicity

    def address(self):
        """
        Retrieve the patient's address.
        Returns a 3 line string suitable for printing.
        """
        try:
            patientAddrLine = self.patientRole["addr"]["streetAddressLine"]
            patientAddrCity = self.patientRole["addr"]["city"]
            patientAddrState = self.patientRole["addr"]["state"]
            patientAddrZIP = self.patientRole["addr"]["postalCode"]
            patientAddrCountry = self.patientRole["addr"]["country"]

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
    
    def lookup_code(self, code, codesystem):
        """
        Lookup a code in the SQLite database by codesystem.
        
        To perform a reverse lookup, prefix 'codesystem' with 'reverse_'.
        """
        if code is None:
            return 'no info'
        
        query_params = {'code':code}
        
        if codesystem.startswith("reverse_"):
            codesystem = codesystem[8:]
            out = self.db_cursor.execute(f"SELECT code FROM {codesystem} WHERE description = :code", query_params)
        else:
            out = self.db_cursor.execute(f"SELECT description FROM {codesystem} WHERE code = :code", query_params)
        
        return out[0][0]
    
    def get_data(self, obj, field, codesystem=None):
        """
        Get the data from an object with a field.
        
        Does not yet support auto-detecting codesystem -
        so codesystem must be provided as an argument.
        """
        
        if codesystem is None:
            raise ParserExcepetion("must provide codesystem")
        
        code = obj.get(field, None)
        
        data = self.lookup_code(code, codesystem)
        
        return data
        
    def get_component(self, name=None, index=None):
        """
        Get one of the components. Handles a variable number of components and different titles.
        
        Uses lookup_code to access database.
        """
        
        if name is None:
            return(self.components[index])
        else:
            return self.get_component(index=
                self.component_list.index(
                self.lookup_code(name, codesystem='reverse_loinc')))
                