"""
Comprehensive pytest suite for Pydantic validation of MIMIC Encounter data.

Tests cover:
- Model validation for valid and invalid data
- Field validators
- Model validators
- Helper methods
- Edge cases and error handling
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
import json

from Pydantic.mimic_encounter_models import (
    MimicEncounter,
    ProcessedEncounter,
    EncounterStatus,
    ActCode,
    PriorityCode,
    Coding,
    CodeableConcept,
    Reference,
    Period,
    EncounterClass,
    Location,
    Identifier,
    Hospitalization,
    Meta
)


class TestCoding:
    """Test Coding model validation"""
    
    def test_valid_coding(self):
        """Test valid coding creation"""
        coding = Coding(
            code="308335008",
            system="http://snomed.info/sct",
            display="Patient encounter procedure"
        )
        assert coding.code == "308335008"
        assert coding.system == "http://snomed.info/sct"
        assert coding.display == "Patient encounter procedure"
    
    def test_coding_minimal(self):
        """Test coding with only required field"""
        coding = Coding(code="12345")
        assert coding.code == "12345"
        assert coding.system is None
        assert coding.display is None


class TestCodeableConcept:
    """Test CodeableConcept model validation"""
    
    def test_valid_codeable_concept(self):
        """Test valid CodeableConcept creation"""
        concept = CodeableConcept(
            coding=[
                Coding(code="EM", system="http://terminology.hl7.org/CodeSystem/v3-ActPriority", display="emergency")
            ]
        )
        assert len(concept.coding) == 1
        assert concept.coding[0].code == "EM"
    
    def test_empty_coding_list_fails(self):
        """Test that empty coding list raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            CodeableConcept(coding=[])
        assert "CodeableConcept must have at least one coding" in str(exc_info.value)


class TestReference:
    """Test Reference model validation"""
    
    def test_valid_reference(self):
        """Test valid reference creation"""
        ref = Reference(reference="Patient/12345-abcde")
        assert ref.reference == "Patient/12345-abcde"
    
    def test_invalid_reference_format_fails(self):
        """Test that invalid reference format raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            Reference(reference="invalid")
        assert "Reference must be in format 'ResourceType/id'" in str(exc_info.value)
    
    def test_empty_reference_fails(self):
        """Test that empty reference raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            Reference(reference="")
        assert "Reference must be in format 'ResourceType/id'" in str(exc_info.value)


class TestPeriod:
    """Test Period model validation"""
    
    def test_valid_period(self):
        """Test valid period creation"""
        period = Period(
            start="2180-05-06T22:23:00-04:00",
            end="2180-05-07T17:15:00-04:00"
        )
        assert period.start == "2180-05-06T22:23:00-04:00"
        assert period.end == "2180-05-07T17:15:00-04:00"
    
    def test_period_only_start(self):
        """Test period with only start time"""
        period = Period(start="2180-05-06T22:23:00-04:00")
        assert period.start == "2180-05-06T22:23:00-04:00"
        assert period.end is None
    
    def test_invalid_datetime_format_fails(self):
        """Test that invalid datetime format raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            Period(start="not-a-date")
        assert "Invalid datetime format" in str(exc_info.value)
    
    def test_start_after_end_fails(self):
        """Test that start after end raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            Period(
                start="2180-05-07T17:15:00-04:00",
                end="2180-05-06T22:23:00-04:00"
            )
        assert "Period start must be before or equal to end" in str(exc_info.value)


class TestEncounterClass:
    """Test EncounterClass model validation"""
    
    def test_valid_encounter_class(self):
        """Test valid encounter class creation"""
        enc_class = EncounterClass(
            code=ActCode.EMER,
            system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
            display="emergency"
        )
        assert enc_class.code == ActCode.EMER
        assert enc_class.display == "emergency"
    
    def test_invalid_code_fails(self):
        """Test that invalid code raises validation error"""
        with pytest.raises(ValidationError):
            EncounterClass(
                code="INVALID",
                system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
                display="invalid"
            )


class TestMimicEncounter:
    """Test MimicEncounter model validation"""
    
    @pytest.fixture
    def valid_encounter_data(self):
        """Fixture providing valid encounter data"""
        return {
            "id": "9c4ef2ae-dd61-5efe-885d-2a2f0816646f",
            "resourceType": "Encounter",
            "status": "finished",
            "class": {
                "code": "EMER",
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "display": "emergency"
            },
            "subject": {
                "reference": "Patient/0a8eebfd-a352-522e-89f0-1d4a13abdebc"
            },
            "period": {
                "start": "2180-05-06T22:23:00-04:00",
                "end": "2180-05-07T17:15:00-04:00"
            },
            "priority": {
                "coding": [{
                    "code": "EM",
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActPriority",
                    "display": "emergency"
                }]
            },
            "location": [
                {
                    "location": {"reference": "Location/501cd59a-cd8a-5f98-8298-2ca9c897d59f"},
                    "period": {"start": "2180-05-06T19:17:00-04:00", "end": "2180-05-06T23:30:00-04:00"}
                }
            ],
            "serviceType": {
                "coding": [{
                    "code": "MED",
                    "system": "http://mimic.mit.edu/fhir/mimic/CodeSystem/mimic-services"
                }]
            },
            "identifier": [{
                "value": "22595853",
                "system": "http://mimic.mit.edu/fhir/mimic/identifier/encounter-hosp"
            }],
            "hospitalization": {
                "admitSource": {
                    "coding": [{
                        "code": "EMERGENCY ROOM",
                        "system": "http://mimic.mit.edu/fhir/mimic/CodeSystem/mimic-admit-source"
                    }]
                },
                "dischargeDisposition": {
                    "coding": [{
                        "code": "HOME",
                        "system": "http://mimic.mit.edu/fhir/mimic/CodeSystem/mimic-discharge-disposition"
                    }]
                }
            }
        }
    
    def test_valid_encounter(self, valid_encounter_data):
        """Test valid encounter creation"""
        encounter = MimicEncounter(**valid_encounter_data)
        assert encounter.id == "9c4ef2ae-dd61-5efe-885d-2a2f0816646f"
        assert encounter.resourceType == "Encounter"
        assert encounter.status == EncounterStatus.FINISHED
        assert encounter.encounter_class.code == ActCode.EMER
    
    def test_invalid_resource_type_fails(self, valid_encounter_data):
        """Test that invalid resourceType raises validation error"""
        valid_encounter_data["resourceType"] = "Patient"
        with pytest.raises(ValidationError) as exc_info:
            MimicEncounter(**valid_encounter_data)
        assert "resourceType must be 'Encounter'" in str(exc_info.value)
    
    def test_missing_required_field_fails(self, valid_encounter_data):
        """Test that missing required field raises validation error"""
        del valid_encounter_data["id"]
        with pytest.raises(ValidationError):
            MimicEncounter(**valid_encounter_data)
    
    def test_finished_without_end_fails(self, valid_encounter_data):
        """Test that finished encounter without end time raises validation error"""
        valid_encounter_data["status"] = "finished"
        valid_encounter_data["period"]["end"] = None
        with pytest.raises(ValidationError) as exc_info:
            MimicEncounter(**valid_encounter_data)
        assert "Finished encounters must have a period end time" in str(exc_info.value)
    
    def test_location_without_period_fails(self, valid_encounter_data):
        """Test that location without period raises validation error"""
        valid_encounter_data["location"][0]["period"] = None
        with pytest.raises(ValidationError) as exc_info:
            MimicEncounter(**valid_encounter_data)
        assert "All locations must have a period" in str(exc_info.value)
    
    def test_get_patient_id(self, valid_encounter_data):
        """Test patient ID extraction"""
        encounter = MimicEncounter(**valid_encounter_data)
        patient_id = encounter.get_patient_id()
        assert patient_id == "0a8eebfd-a352-522e-89f0-1d4a13abdebc"
    
    def test_get_encounter_duration_hours(self, valid_encounter_data):
        """Test encounter duration calculation"""
        encounter = MimicEncounter(**valid_encounter_data)
        duration = encounter.get_encounter_duration_hours()
        assert duration is not None
        assert duration > 0
        # Duration should be approximately 18.87 hours
        assert 18 < duration < 19
    
    def test_get_encounter_duration_no_end(self, valid_encounter_data):
        """Test encounter duration with no end time"""
        valid_encounter_data["status"] = "in-progress"
        valid_encounter_data["period"]["end"] = None
        encounter = MimicEncounter(**valid_encounter_data)
        duration = encounter.get_encounter_duration_hours()
        assert duration is None
    
    def test_is_high_priority_emergency(self, valid_encounter_data):
        """Test high priority detection for emergency"""
        encounter = MimicEncounter(**valid_encounter_data)
        assert encounter.is_high_priority() is True
    
    def test_is_high_priority_urgent(self, valid_encounter_data):
        """Test high priority detection for urgent"""
        valid_encounter_data["priority"]["coding"][0]["code"] = "UR"
        encounter = MimicEncounter(**valid_encounter_data)
        assert encounter.is_high_priority() is True
    
    def test_is_not_high_priority(self, valid_encounter_data):
        """Test high priority detection for routine"""
        valid_encounter_data["priority"]["coding"][0]["code"] = "R"
        encounter = MimicEncounter(**valid_encounter_data)
        assert encounter.is_high_priority() is False
    
    def test_get_location_count(self, valid_encounter_data):
        """Test location count"""
        encounter = MimicEncounter(**valid_encounter_data)
        assert encounter.get_location_count() == 1
        
        # Add another location
        valid_encounter_data["location"].append({
            "location": {"reference": "Location/9152585d-31b9-50ca-9476-a4db49030917"},
            "period": {"start": "2180-05-06T23:30:00-04:00", "end": "2180-05-07T17:15:00-04:00"}
        })
        encounter2 = MimicEncounter(**valid_encounter_data)
        assert encounter2.get_location_count() == 2


class TestProcessedEncounter:
    """Test ProcessedEncounter model validation"""
    
    @pytest.fixture
    def valid_processed_data(self):
        """Fixture providing valid processed encounter data"""
        return {
            "encounter_id": "9c4ef2ae-dd61-5efe-885d-2a2f0816646f",
            "resourceType": "Encounter",
            "status": "finished",
            "encounter_class": "EMER",
            "encounter_class_display": "emergency",
            "period_start": "2180-05-06T22:23:00-04:00",
            "period_end": "2180-05-07T17:15:00-04:00",
            "patient_reference": "Patient/0a8eebfd-a352-522e-89f0-1d4a13abdebc",
            "patient_id": "0a8eebfd-a352-522e-89f0-1d4a13abdebc",
            "priority_code": "EM",
            "priority_display": "emergency",
            "service_type": "MED",
            "admit_source": "EMERGENCY ROOM",
            "discharge_disposition": "HOME",
            "encounter_identifier": "22595853",
            "location_count": 2,
            "encounter_duration_hours": 18.87
        }
    
    def test_valid_processed_encounter(self, valid_processed_data):
        """Test valid processed encounter creation"""
        processed = ProcessedEncounter(**valid_processed_data)
        assert processed.encounter_id == "9c4ef2ae-dd61-5efe-885d-2a2f0816646f"
        assert processed.patient_id == "0a8eebfd-a352-522e-89f0-1d4a13abdebc"
        assert processed.location_count == 2
    
    def test_negative_location_count_fails(self, valid_processed_data):
        """Test that negative location count raises validation error"""
        valid_processed_data["location_count"] = -1
        with pytest.raises(ValidationError):
            ProcessedEncounter(**valid_processed_data)
    
    def test_negative_duration_fails(self, valid_processed_data):
        """Test that negative duration raises validation error"""
        valid_processed_data["encounter_duration_hours"] = -5.0
        with pytest.raises(ValidationError):
            ProcessedEncounter(**valid_processed_data)
    
    def test_invalid_patient_id_fails(self, valid_processed_data):
        """Test that invalid patient ID raises validation error"""
        valid_processed_data["patient_id"] = "abc"
        with pytest.raises(ValidationError) as exc_info:
            ProcessedEncounter(**valid_processed_data)
        assert "Patient ID must be a valid identifier" in str(exc_info.value)
    
    def test_extra_fields_forbidden(self, valid_processed_data):
        """Test that extra fields raise validation error"""
        valid_processed_data["extra_field"] = "not allowed"
        with pytest.raises(ValidationError):
            ProcessedEncounter(**valid_processed_data)


class TestRealDataValidation:
    """Test validation against real MIMIC dataset samples"""
    
    def test_validate_sample_record_1(self):
        """Test validation of first sample record from dataset"""
        data = {
            "id": "9c4ef2ae-dd61-5efe-885d-2a2f0816646f",
            "meta": {"profile": ["http://mimic.mit.edu/fhir/mimic/StructureDefinition/mimic-encounter"]},
            "type": [{"coding": [{"code": "308335008", "system": "http://snomed.info/sct", "display": "Patient encounter procedure"}]}],
            "class": {"code": "AMB", "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "display": "ambulatory"},
            "period": {"end": "2180-05-07T17:15:00-04:00", "start": "2180-05-06T22:23:00-04:00"},
            "status": "finished",
            "subject": {"reference": "Patient/0a8eebfd-a352-522e-89f0-1d4a13abdebc"},
            "location": [
                {"period": {"end": "2180-05-06T23:30:00-04:00", "start": "2180-05-06T19:17:00-04:00"}, "location": {"reference": "Location/501cd59a-cd8a-5f98-8298-2ca9c897d59f"}},
                {"period": {"end": "2180-05-07T17:21:27-04:00", "start": "2180-05-06T23:30:00-04:00"}, "location": {"reference": "Location/9152585d-31b9-50ca-9476-a4db49030917"}}
            ],
            "priority": {"coding": [{"code": "UR", "system": "http://terminology.hl7.org/CodeSystem/v3-ActPriority", "display": "urgent"}]},
            "identifier": [{"use": "usual", "value": "22595853", "system": "http://mimic.mit.edu/fhir/mimic/identifier/encounter-hosp", "assigner": {"reference": "Organization/ee172322-118b-5716-abbc-18e4c5437e15"}}],
            "serviceType": {"coding": [{"code": "MED", "system": "http://mimic.mit.edu/fhir/mimic/CodeSystem/mimic-services"}]},
            "resourceType": "Encounter",
            "hospitalization": {
                "admitSource": {"coding": [{"code": "TRANSFER FROM HOSPITAL", "system": "http://mimic.mit.edu/fhir/mimic/CodeSystem/mimic-admit-source"}]},
                "dischargeDisposition": {"coding": [{"code": "HOME", "system": "http://mimic.mit.edu/fhir/mimic/CodeSystem/mimic-discharge-disposition"}]}
            },
            "serviceProvider": {"reference": "Organization/ee172322-118b-5716-abbc-18e4c5437e15"}
        }
        
        encounter = MimicEncounter(**data)
        assert encounter.id == "9c4ef2ae-dd61-5efe-885d-2a2f0816646f"
        assert encounter.status == EncounterStatus.FINISHED
        assert encounter.get_patient_id() == "0a8eebfd-a352-522e-89f0-1d4a13abdebc"
        assert encounter.get_location_count() == 2
        assert encounter.is_high_priority() is True
    
    def test_validate_multiple_locations(self):
        """Test validation of encounter with multiple locations"""
        data = {
            "id": "8a5be724-d9d4-5a47-8a39-4a274662f766",
            "resourceType": "Encounter",
            "status": "finished",
            "class": {"code": "EMER", "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "display": "emergency"},
            "period": {"end": "2180-07-25T17:55:00-04:00", "start": "2180-07-23T12:35:00-04:00"},
            "subject": {"reference": "Patient/0a8eebfd-a352-522e-89f0-1d4a13abdebc"},
            "location": [
                {"period": {"end": "2180-07-23T05:54:00-04:00", "start": "2180-07-22T16:24:00-04:00"}, "location": {"reference": "Location/501cd59a"}},
                {"period": {"end": "2180-07-23T14:00:00-04:00", "start": "2180-07-23T05:54:00-04:00"}, "location": {"reference": "Location/501cd59a"}},
                {"period": {"end": "2180-07-23T23:50:47-04:00", "start": "2180-07-23T14:00:00-04:00"}, "location": {"reference": "Location/77b3f959"}},
                {"period": {"end": "2180-07-24T19:52:58-04:00", "start": "2180-07-23T23:50:47-04:00"}, "location": {"reference": "Location/9152585d"}},
                {"period": {"end": "2180-07-25T17:55:43-04:00", "start": "2180-07-24T19:52:58-04:00"}, "location": {"reference": "Location/9152585d"}}
            ],
            "priority": {"coding": [{"code": "EM", "system": "http://terminology.hl7.org/CodeSystem/v3-ActPriority", "display": "emergency"}]},
            "identifier": [{"value": "29079034"}]
        }
        
        encounter = MimicEncounter(**data)
        assert encounter.get_location_count() == 5
        assert encounter.is_high_priority() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
