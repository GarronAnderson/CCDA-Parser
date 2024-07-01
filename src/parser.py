"""
CCDA Parser
6/30/24
By Garron Anderson"""

from collections import namedtuple
import datetime
import sqlite3 as sqlite

import xmltodict

import iso639
from pint import UnitRegistry


class ParserException(Exception):
    """A class for when the parser raises an exception."""


class Parser:
    """The main class that handles the parsing of CCDA files.

    Generates name, address, etc."""

    def __init__(self, filename):
        """
        Start up parser given a filename.
        """
        self._filename = filename
        with open(self._filename, encoding="utf8") as ccda:  # load file
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

        # connect to db
        self.db_conn = sqlite.connect("codeDatabase.db")
        self.db_cursor = self.db_conn.cursor()

        self.ucum_registry = UnitRegistry(system="UCUM")

        self.height_factory = namedtuple("Height", "feet inches")

    # INTERNAL FUNCTIONS

    def _connect_db(self):
        return sqlite.connect("codeDatabase.db")

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
        try:
            return out[0][0]
        except IndexError:
            return ""

    def get_data(self, obj, field="@code", codesystem=None):
        """
        Get the data from an object with a field.

        Can autodetect codesystem or take a codesystem name (as table name in SQLite database) to work with.

        """
        if field not in list(obj.keys()):
            return "no info"

        if codesystem is None:  # autodetect
            codesys_raw = obj.get("@codeSystem", None)

            if codesys_raw is None:  # no info, can't autodetect
                raise ParserException("must provide codesystem") from None

            r = list(
                self.db_cursor.execute(
                    "select codesystem_name from codesystems where codesystem_id = ?",
                    (codesys_raw,),
                )
            )
            codesystem = None

            if r:
                codesystem = r[0][0]

            if codesystem is None:
                raise ParserException("must provide codesystem") from None

        # grab code
        code = obj.get(field, None)
        # and look up
        data = self.lookup_code(code, codesystem)

        return data

    def _get_vital_codes(self, vital):
        """
        Helper method to get the LOINC codes for a given vital sign.
        """
        possible_codes = {
            "Height": ["Height", "Body height"],
            "Weight": ["Weight", "Body weight"],
            "BMI": ["Body mass index"],
            # Add other vitals as needed
        }

        descriptions = possible_codes.get(vital, [])
        codes = []

        with self._connect_db() as conn:
            cursor = conn.cursor()
            for description in descriptions:
                cursor.execute(
                    "SELECT code FROM loinc WHERE description = ?", (description,)
                )
                codes.extend([row[0] for row in cursor.fetchall()])

        return codes

    def get_component(self, name=None, index=None):
        """
        Get one of the components. Handles a variable number of components and different titles.

        Uses lookup_code to access database and a dict to handle multiple names.

        Returns `None` if component not found.
        """

        # multiple possibilites
        components_possible = {
            "Vital Signs": [
                "Vital signs",
                "Vital signs, weight, height, head circumference, oxygen saturation & BMI panel",
            ]
        }

        if name is None:  # use index
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
            code = self.lookup_code(name, codesystem="reverse_loinc")
            if code not in self.component_list:  # non existent component
                return None
            else:
                return self.get_component(index=self.component_list.index(code))

    def get_latest_vital(self, vital):
        """
        Get the latest entry for a given vital sign.
        Returns a tuple of `(value, unit)`
        """

        vital_entries = self.get_component(name="Vital Signs")["section"]["entry"]
        vital_codes = self._get_vital_codes(vital)

        if not vital_codes:  # bad vital or no entry in db
            raise ParserException(f"Invalid vital {vital}")

        vital_signs = None
        try:  # for only 1 set of stuff
            vital_signs = vital_entries["organizer"]["component"]
        except TypeError:
            pass  # ignore and search through

        if vital_signs is None:  # search through
            code_found = False
            effective_times = [0] * len(vital_entries)
            obs_indexes = [0] * len(vital_entries)
            for i, entry in enumerate(vital_entries):  # for each entry
                vital_obs = entry["organizer"]["component"]
                for j, obs in enumerate(vital_obs):  # pull each observation
                    observation = obs["observation"]
                    obs_code = observation["code"]["@code"]
                    if obs_code in vital_codes:  # if the code matches
                        try:  # and the effectiveTime exists
                            effectiveTime = observation["effectiveTime"]["@value"]
                        except KeyError:  # couldn't find it, ignore
                            continue
                        # then update list of times and indexes (and mark code as found)
                        effective_times[i] = int(effectiveTime)
                        obs_indexes[i] = j
                        code_found = True

            if code_found:  # the observation existed
                # now find the max effective time
                newest_index = effective_times.index(max(effective_times))
                # and pull the observation
                obs = vital_entries[newest_index]["organizer"]["component"]
                obs_index = obs_indexes[newest_index]

                obs_value = obs[obs_index]["observation"]["value"]["@value"]
                obs_unit = obs[obs_index]["observation"]["value"]["@unit"]
                return obs_value, obs_unit

            else:  # observation didn't exist
                return "no info", "no info"

        else:  # 1 set of observations
            for obs in vital_signs:
                observation = obs["observation"]
                obs_code = observation["code"]["@code"]
                if obs_code in vital_codes:  # found it
                    # grab value
                    obs_value = observation["value"]["@value"]
                    obs_unit = observation["value"]["@unit"]
                    return obs_value, obs_unit

    # parser methods

    def _parse_addr(self, addr):
        """
        Parse an addr into a human-readable string.
        """
        try:
            addrLines = addr["streetAddressLine"]
            if isinstance(addrLines, list):
                addrLine = "\n".join(addrLines)
            else:
                addrLine = addrLines
            addrCity = addr["city"]
            addrState = addr["state"]
            addrZIP = addr["postalCode"]
            if "country" in addr:
                addrCountry = addr["country"]
            else:
                addrCountry = "US"

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

    @staticmethod
    def _parse_date(date_str):
        """
        Parse a YYYYMMDD date to MM/DD/YYYY.
        """
        try:
            return datetime.datetime.strptime(date_str[:8], "%Y%m%d").strftime(
                "%m/%d/%Y"
            )
        except ValueError:
            return "no info"

    def _parse_name(self, raw_name):
        """
        Parse a name into a string.
        """
        # set defaults
        given_name, family_name = "no info", ""

        if isinstance(raw_name, str):  # return the raw name
            return raw_name

        if isinstance(raw_name, list):  # return the first name of multiple
            given_name = raw_name[0]["given"]
            family_name = raw_name[0]["family"]
        else:
            given_name = raw_name["given"]
            family_name = raw_name["family"]

        if isinstance(given_name, dict):
            given_name = given_name.get("#text", "no info")
        if isinstance(family_name, dict):
            family_name = family_name.get("#text", "no info")

        return f"{given_name} {family_name}"

    def _parse_telecoms(self, telecom):
        """
        Parse telecoms to human-readable formats.
        """

        if isinstance(telecom, list):  # multiple telecoms
            telecoms = []
            for t in telecom:
                telecoms.append(self._parse_telecoms(t))

        telRaw = self.patientRole["telecom"]["@value"]
        if telRaw.startswith("tel:"):
            tel = telRaw[4:]
        elif telRaw.startswith("mailTo:"):
            tel = telRaw[7:]
        else:
            tel = telRaw

        telType = self.get_data(
            self.patientRole["telecom"], field="@use", codesystem="hl7_address_use"
        )

        return [tel, telType]

    def _get_lang_and_pref(self, entry):
        """
        Extract a language and associated preference code from `entry`.
        """

        langCode = entry["languageCode"].get("@code", None)

        if langCode is not None:
            lang = iso639.Lang(langCode).name
        else:
            lang = "no info"

        try:
            preferred = {"true": "yes", "false": "no"}[entry["preferenceInd"]["@value"]]
        except KeyError:
            preferred = "no info"

        return lang, preferred

    def _parse_smoking_data(self, entry):
        """
        Parse a smoking status observation.
        """

        entry = entry["observation"]
        status = "no info"
        date = "no info"
        good = False

        code = entry["code"]["@code"]
        if code in ["72166-2", "ASSERTION"]:
            good = True
            status = self.get_data(entry["value"])
            date = (
                entry["effectiveTime"]
                .get("low", entry["effectiveTime"])
                .get("@value", "no info")
            )
            if date != "no info":
                date = self._parse_date(date)

        return status, date, good

    # PATIENT DATA FUNCTIONS

    @property
    def name(self):
        """
        Retrieve the patient's name.
        """
        raw_name = self.patient["name"]

        name = self._parse_name(raw_name)

        return name

    @property
    def gender(self):
        """
        Retrieve the patient's gender.
        """

        return self.get_data(self.patient["administrativeGenderCode"])

    @property
    def dob(self):
        """
        Get the patient's date of birth, formatted as MM/DD/YYYY.
        """

        dob_raw = self.patient.get("birthTime", {}).get("@value", "no info")
        return self._parse_date(dob_raw)

    @property
    def race_ethnicity(self):
        """
        Retrieve the patient's race and ethnicity (as a tuple, `(race, ethnicity)`).
        """
        patientRace = self.get_data(self.patient["raceCode"])
        patientEthnicity = self.get_data(self.patient["ethnicGroupCode"])

        return patientRace, patientEthnicity

    @property
    def languages(self):
        """
        Return the patient's languages and preferences.

        Returns two lists. The first is a list of human-readable language names, and the second is a list of yes/no preferences.
        """

        langs, prefs = [], []

        if isinstance(self.patient["languageCommunication"], dict):
            lang, pref = self._get_lang_and_pref(self.patient["languageCommunication"])
            return [lang], [pref]
        else:
            for entry in self.patient["languageCommunication"]:
                lang, pref = self._get_lang_and_pref(entry)
                langs.extend([lang])
                prefs.extend([pref])
            return langs, prefs

    @property
    def address(self):
        """
        Retrieve the patient's address.
        Returns a string suitable for printing.
        """
        addr_raw = self.patientRole["addr"]
        print(addr_raw)
        addr = self._parse_addr(addr_raw)

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
        """
        Retrieve the patient's smoking status and date.
        """

        social_comp = self.get_component("Social history")
        smoking_entries = social_comp["section"]["entry"]

        smoking_status = "no info"
        smoking_date = "no info"
        good = False

        if isinstance(smoking_entries, dict):
            smoking_status, smoking_date, good = self._parse_smoking_data(
                smoking_entries
            )
        else:
            for entry in smoking_entries:
                smoking_status, smoking_date, good = self._parse_smoking_data(entry)
                if good:
                    break

        return smoking_status, smoking_date

    @property
    def height(self):
        """
        Get the patient's latest height as a namedtuple with `feet` and `inches` fields.
        """
        raw_height, unit = self.get_latest_vital("Height")
        if raw_height == "no info" or unit == "no info":
            return self.height_factory("no info", "no info")

        height = (
            float(raw_height)
            * self.ucum_registry.parse_expression(unit).to("inches").magnitude
        )
        feet, inches = divmod(height, 12)

        height = self.height_factory(int(feet), round(inches))

        return height

    @property
    def weight(self):
        """
        Get the patient's latest weight in pounds.
        """
        raw_weight, unit = self.get_latest_vital("Weight")
        if raw_weight == "no info" or unit == "no info":
            return "no info"

        weight = (
            float(raw_weight)
            * self.ucum_registry.parse_expression(unit).to("pounds").magnitude
        )
        return round(weight)

    @property
    def bmi(self):
        """
        Get the patient's latest BMI.
        """

        raw_bmi, _ = self.get_latest_vital("BMI")
        if raw_bmi == "no info":
            return "no info"

        return round(float(raw_bmi))

    def insurance(self):
        insurance_comp = self.get_component("Payment sources")["section"]
        if insurance_comp is None:
            return "no info"

        coverage_acty = insurance_comp["entry"]["act"]
        policy_acty = coverage_acty["entryRelationship"]["act"]

        performer_oids = [
            performer["templateId"]["@root"] for performer in policy_acty["performer"]
        ]

        if (
            "2.16.840.1.113883.10.20.22.4.87" not in performer_oids
        ):  # no insurance company info
            return "no info"

        if "2.16.840.1.113883.10.20.22.4.88" not in performer_oids:  # no gurantor info
            return "no info"

        company_info = performer_oids.index("2.16.840.1.113883.10.20.22.4.87")
        gurantor_info = performer_oids.index("2.16.840.1.113883.10.20.22.4.88")

        company_name = self._parse_name(
            policy_acty["performer"][company_info]["assignedEntity"][
                "representedOrganization"
            ]["name"]
        )
        company_telecom = self._parse_telecoms(
            policy_acty["performer"][company_info]["assignedEntity"][
                "representedOrganization"
            ]["telecom"]
        )
        company_addr = self._parse_addr(
            policy_acty["performer"][company_info]["assignedEntity"][
                "representedOrganization"
            ]["addr"]
        )
        print(
            policy_acty["performer"][company_info]["assignedEntity"][
                "representedOrganization"
            ]["addr"]
        )

        gurantor_name = self._parse_name(
            policy_acty["performer"][gurantor_info]["assignedEntity"]["assignedPerson"][
                "name"
            ]
        )
        gurantor_telecom = self._parse_telecoms(
            policy_acty["performer"][gurantor_info]["assignedEntity"]["telecom"]
        )
        gurantor_addr = self._parse_addr(
            policy_acty["performer"][gurantor_info]["assignedEntity"]["addr"]
        )

        participant_oids = [
            participant["templateId"]["@root"]
            for participant in policy_acty["participant"]
        ]

        if (
            "2.16.840.1.113883.10.20.22.4.90" not in participant_oids
        ):  # no policy holder info
            return "no info"

        subscriber_info = participant_oids.index("2.16.840.1.113883.10.20.22.4.90")

        subscriber_id = policy_acty["participant"][subscriber_info]["participantRole"][
            "id"
        ]["@extension"]

        company_data = {
            "name": company_name,
            "addr": company_addr,
            "telecom": company_telecom,
        }
        gurantor_data = {
            "name": gurantor_name,
            "addr": gurantor_addr,
            "telecom": gurantor_telecom,
        }

        out = {
            "company": company_data,
            "gurantor": gurantor_data,
            "sub_id": subscriber_id,
        }
        return out
