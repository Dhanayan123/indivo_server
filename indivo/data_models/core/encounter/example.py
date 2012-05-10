from indivo.models import Encounter
from indivo.lib.iso8601 import parse_utc_date as date

encounter_fact = Encounter(
    startDate=date("2009-05-16T12:00:00Z"),
    endDate=date("2009-05-16T16:00:00Z"),
    facility_name="Wonder Hospital",
    facility_adr_country="Australia",
    facility_adr_city="WonderCity",
    facility_adr_postalcode="5555",
    facility_adr_street="111 Lake Drive", 
    provider_dea_number="325555555",
    provider_npi_number="5235235",
    provider_email="joshua.mandel@fake.emailserver.com",
    provider_name_given="Josuha",
    provider_name_family="Mandel",
    provider_tel_1_type="w",
    provider_tel_1_number="1-235-947-3452",
    provider_tel_1_preferred_p=True,
    encounterType_title="Ambulatory encounter",
    encounterType_system="http://smartplatforms.org/terms/codes/EncounterType#",
    encounterType_identifier="ambulatory",
    )
