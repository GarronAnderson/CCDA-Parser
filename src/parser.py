"""
CCDA Parser

By Garron Anderson"""

import datetime
import sqlite3 as sqlite

import xmltodict

import iso639
from ucumvert import PintUcumRegistry


class ParserException(Exception):
    """A class for when the parser raises an exception."""


class Parser:
    """The main class that handles the parsing of CCDA files.

    Generates name, address, etc."""

    def __init__(self, filename):
        with open(filename) as ccda:
            ccda_text = ccda.read()
            self.ccda_data = xmltodict.parse(ccda_text)

        self.patientRole = self.ccda_data["ClinicalDocument"]["recordTarget"][
            "patientRole"
        ]
        self.patient = self.patientRole["patient"]

        self.components = self.ccda_data["ClinicalDocument"]["component"][
            "structuredBody"
        ]["component"]
        self.component_list = []
        for i in range(len(self.components)):
            self.component_list.append(self.components[i]["section"]["code"]["@code"])

        self.db_conn = sqlite.connect("codeDatabase.db")
        self.db_cursor = self.db_conn.cursor()

        self.ucumureg = PintUcumRegistry()

    # INTERNAL FUNCTIONS

    def lookup_code(self, code, codesystem):
        """
        Lookup a code in the SQLite database by codesystem.

        To perform a reverse lookup, prefix 'codesystem' with 'reverse_'.

        Will return 'no info' if no code provided.
        """
        if code is None:
            return "no info"

        query_params = {"code": code}

        if codesystem.startswith("reverse_"):
            codesystem = codesystem[8:]
            out = self.db_cursor.execute(
                f"SELECT code FROM {codesystem} WHERE description = :code", query_params
            )
        else:
            out = self.db_cursor.execute(
                f"SELECT description FROM {codesystem} WHERE code = :code", query_params
            )

        out = list(out)

        return out[0][0]

    def get_data(self, obj, field="@code", codesystem=None):
        """
        Get the data from an object with a field.

        Can autodedect codesystem or take a codesystem name (as table name in SQLite database) to work with.

        """
        if field not in list(obj.keys()):
            return "no info"

        if codesystem is None:
            codesys_raw = obj.get("@codeSystem", None)

            if codesys_raw is None:
                raise ParserException("must provide codesystem")

            r = list(
                self.db_cursor.execute(
                    "select codesystem_name from codesystems where codesystem_id = ?",
                    (codesys_raw,),
                )
            )

            codesystem = r[0][0]

            if codesystem is None:
                raise ParserException("must provide codesystem")

        code = obj.get(field, None)

        data = self.lookup_code(code, codesystem)

        return data

    def get_component(self, name=None, index=None):
        """
        Get one of the components. Handles a variable number of components and different titles.

        Uses lookup_code to access database and a dict to handle multiple names.
        """

        components_possible = {
            "Vital Signs": [
                "Vital signs",
                "Vital signs, weight, height, head circumference, oxygen saturation & BMI panel",
            ]
        }

        if name is None:
            return self.components[index]

        if name in components_possible:
            # ok, multiple possibilities
            for new_name in components_possible[name]:
                # run through each
                try:
                    return self.get_component(name=new_name)
                except IndexError:
                    pass  # couldn't find it
        else:
            return self.get_component(
                index=self.component_list.index(
                    self.lookup_code(name, codesystem="reverse_loinc")
                )
            )

    # DATA FUNCTIONS

    @property
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

    @property
    def gender(self):
        """
        Retrieve the patient's gender.
        """

        return self.get_data(self.patient["administrativeGenderCode"])

    @property
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

    @property
    def race_ethnicity(self):
        """
        Retrieve the patient's race and ethnicity (as a tuple).
        """
        patientRace = self.get_data(self.patient["raceCode"])
        patientEthnicity = self.get_data(self.patient["ethnicGroupCode"])

        return patientRace, patientEthnicity

    @property
    def language(self):
        """
        Return the patient's language and preference as a tuple.
        """

        langCode = self.patient["languageCommunication"]["languageCode"].get(
            "@code", None
        )

        if langCode is not None:
            lang = iso639.Lang(langCode).name
        else:
            lang = "no info"

        try:
            preferred = {"true": "yes", "false": "no"}[
                self.patient["languageCommunication"]["preferenceInd"]["@value"]
            ]
        except KeyError:
            preferred = "no info"

        return lang, preferred

    @property
    def address(self):
        """
        Retrieve the patient's address.
        Returns a 3 line string suitable for printing.
        """
        try:
            addrLine = self.patientRole["addr"]["streetAddressLine"]
            addrCity = self.patientRole["addr"]["city"]
            addrState = self.patientRole["addr"]["state"]
            addrZIP = self.patientRole["addr"]["postalCode"]
            addrCountry = self.patientRole["addr"]["country"]

            addr = (
                addrLine
                + "\n"
                + addrCity
                + ", "
                + addrState
                + " "
                + addrZIP
                + "\n"
                + addrCountry
            )

        except KeyError:
            addr = "no info"

        return addr

    @property
    def phone(self):
        """
        Get the patient's phone and phone type as a tuple.
        """
        phoneNumber = self.patientRole["telecom"]["@value"][4:]
        phoneType = self.get_data(
            self.patientRole["telecom"], field="@use", codesystem="hl7_address_use"
        )

        return phoneNumber, phoneType

    @property
    def smoking_status(self):
        social_comp = self.get_component("Social history")
        smoking_status = self.get_data(
            social_comp["section"]["entry"]["observation"]["value"]
        )
        smoking_date = social_comp["section"]["entry"]["observation"]["effectiveTime"][
            "low"
        ].get("@value", "no info")

        if smoking_date != "no info":
            smoking_date = datetime.datetime.strptime(
                smoking_date[:8], "%Y%m%d"
            ).strftime("%m/%d/%Y")

        return smoking_status, smoking_date

    def get_latest_vital(self, vital):
        vital_entries = self.get_component(name="Vital Signs")["section"]["entry"]

        possible_codes = {
            "Height": ["Height", "Body height"],
            "Weight": ["Weight", "Body weight"],
            "BMI": ["Body mass index"],
        }

        if vital in list(possible_codes.keys()):
            codes = []
            for code in possible_codes[vital]:
                codes.extend(
                    [
                        a[0]
                        for a in list(
                            self.db_cursor.execute(
                                "select code from loinc where description = ?", (code,)
                            )
                        )
                    ]
                )
        else:
            codes = [
                a[0]
                for a in list(
                    self.db_cursor.execute(
                        "select code from loinc where description = ?", (vital,)
                    )
                )
            ]

        if codes == []:
            raise ParserException(f"Invalid vital {vital}")

        vital_signs = None
        try:  # for only 1 set of stuff
            vital_signs = vital_entries["organizer"]["component"]
        except TypeError:
            pass  # ignore and search through

        if vital_signs is None:
            code_found = False
            effective_times = [0] * len(vital_entries)
            obs_indexes = [0] * len(vital_entries)
            for i, entry in enumerate(vital_entries):
                vital_obs = entry["organizer"]["component"]
                for j, obs in enumerate(vital_obs):
                    observation = obs["observation"]
                    obs_code = observation["code"]["@code"]
                    if obs_code in codes:
                        try:
                            effectiveTime = observation["effectiveTime"]["@value"]
                        except KeyError:  # couldn't find it, ignore
                            continue

                        # ok, now update list of times and indexes (and mark code as found)
                        effective_times[i] = int(effectiveTime)
                        obs_indexes[i] = j
                        code_found = True

            if code_found:
                # now find the max effective time
                newest_index = effective_times.index(max(effective_times))
                # and pull the observation
                obs = vital_entries[newest_index]["organizer"]["component"]
                obs_index = obs_indexes[newest_index]

                obs_value = obs[obs_index]["observation"]["value"]["@value"]
                obs_unit = obs[obs_index]["observation"]["value"]["@unit"]
                return obs_value, obs_unit

            else:
                return "no info", "no info"

        else:
            for obs in vital_signs:
                observation = obs["observation"]
                obs_code = observation["code"]["@code"]
                if obs_code in codes:  # found it
                    # grab value
                    obs_value = observation["value"]["@value"]
                    obs_unit = observation["value"]["@unit"]
                    return obs_value, obs_unit

    @property
    def height(self):
        raw_height, unit = self.get_latest_vital("Height")

        height = raw_height * self.ucumureg.from_ucum(unit)

        return height
