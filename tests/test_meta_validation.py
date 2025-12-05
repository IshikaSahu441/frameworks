"""
Unit tests for FHIR Meta element validation in MIMIC Encounter data.

Tests cover:
- Meta profile validation (present in MIMIC data)
- Optional version tracking fields validation
- Temporal consistency checks
- Integration with MimicEncounter and ProcessedEncounter models
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from Pydantic.mimic_encounter_models import (
    Meta,
    MimicEncounter,
    ProcessedEncounter,
    EncounterStatus
)


class TestMetaValidation:
    """Test FHIR Meta element validation."""
    
    def test_meta_with_profile_only(self):
        """Test valid meta with only profile (typical MIMIC data)."""
        meta = Meta(
            profile=["http://mimic.mit.edu/fhir/mimic/StructureDefinition/mimic-encounter"]
        )
        assert meta.profile is not None
        assert len(meta.profile) == 1
        assert meta.versionId is None
        assert meta.lastUpdated is None
    
    def test_meta_with_numeric_version(self):
        """Test valid meta with numeric version ID."""
        meta = Meta(
            profile=["http://mimic.mit.edu/fhir/mimic/StructureDefinition/mimic-encounter"],
            versionId="1",
            lastUpdated=datetime.now()
        )
        assert meta.versionId == "1"
        assert meta.lastUpdated is not None
    
    def test_meta_with_semantic_version(self):
        """Test valid meta with semantic version ID."""
        meta = Meta(
            versionId="1.0.0",
            lastUpdated=datetime.now()
        )
        assert meta.versionId == "1.0.0"
    
    def test_meta_invalid_version_format(self):
        """Test invalid version format raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Meta(
                versionId="invalid-version",
                lastUpdated=datetime.now()
            )
        assert "versionId must be numeric" in str(exc_info.value)
    
    def test_meta_future_last_updated(self):
        """Test lastUpdated in future raises error."""
        future_time = datetime.now() + timedelta(days=1)
        with pytest.raises(ValidationError) as exc_info:
            Meta(
                versionId="1",
                lastUpdated=future_time
            )
        assert "cannot be in the future" in str(exc_info.value)
    
    def test_meta_invalid_source_uri(self):
        """Test invalid source URI raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Meta(
                versionId="1",
                lastUpdated=datetime.now(),
                source="not-a-valid-uri"
            )
        assert "must be a valid URI" in str(exc_info.value)
    
    def test_meta_valid_http_source(self):
        """Test valid HTTP source URI."""
        meta = Meta(
            versionId="1",
            lastUpdated=datetime.now(),
            source="http://hospital.example.org/fhir"
        )
        assert meta.source == "http://hospital.example.org/fhir"
    
    def test_meta_valid_https_source(self):
        """Test valid HTTPS source URI."""
        meta = Meta(
            versionId="1",
            lastUpdated=datetime.now(),
            source="https://hospital.example.org/fhir"
        )
        assert meta.source == "https://hospital.example.org/fhir"
    
    def test_meta_valid_urn_source(self):
        """Test valid URN source."""
        meta = Meta(
            versionId="1",
            lastUpdated=datetime.now(),
            source="urn:uuid:53fefa32-fcbb-4ff8-8a92-55ee120877b7"
        )
        assert meta.source.startswith("urn:")
    
    def test_meta_version_without_timestamp(self):
        """Test versionId without lastUpdated raises warning."""
        with pytest.raises(ValidationError) as exc_info:
            Meta(
                versionId="1",
                lastUpdated=None
            )
        assert "lastUpdated should also be provided" in str(exc_info.value)
    
    def test_meta_empty_version_id(self):
        """Test empty versionId is allowed (treated as None)."""
        meta = Meta(
            versionId="",
            lastUpdated=None
        )
        # Empty string should be treated as no version
        assert meta.versionId == ""
    
    def test_meta_with_tags_and_security(self):
        """Test meta with additional tags and security labels."""
        meta = Meta(
            profile=["http://example.org/profile"],
            tag=[{"system": "http://example.org/tags", "code": "test"}],
            security=[{"system": "http://example.org/security", "code": "confidential"}]
        )
        assert meta.tag is not None
        assert meta.security is not None


class TestEncounterMetaIntegration:
    """Test Meta validation integrated with MimicEncounter."""
    
    def test_encounter_with_profile_only(self):
        """Test typical MIMIC encounter with profile in meta."""
        encounter_data = {
            "id": "test-001",
            "meta": {
                "profile": ["http://mimic.mit.edu/fhir/mimic/StructureDefinition/mimic-encounter"]
            },
            "resourceType": "Encounter",
            "status": "finished",
            "class": {
                "code": "AMB",
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "display": "ambulatory"
            },
            "subject": {"reference": "Patient/123"},
            "period": {
                "start": "2024-01-01T10:00:00-05:00",
                "end": "2024-01-01T12:00:00-05:00"
            }
        }
        encounter = MimicEncounter(**encounter_data)
        assert encounter.meta is not None
        assert encounter.meta.profile is not None
        assert encounter.meta.versionId is None
    
    def test_encounter_with_full_version_metadata(self):
        """Test encounter with complete version metadata."""
        encounter_data = {
            "id": "test-002",
            "meta": {
                "profile": ["http://mimic.mit.edu/fhir/mimic/StructureDefinition/mimic-encounter"],
                "versionId": "1",
                "lastUpdated": "2024-01-01T12:30:00Z",
                "source": "http://hospital.example.org/fhir"
            },
            "resourceType": "Encounter",
            "status": "finished",
            "class": {
                "code": "EMER",
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "display": "emergency"
            },
            "subject": {"reference": "Patient/456"},
            "period": {
                "start": "2024-01-01T10:00:00Z",
                "end": "2024-01-01T12:00:00Z"
            }
        }
        encounter = MimicEncounter(**encounter_data)
        assert encounter.meta.versionId == "1"
        assert encounter.meta.lastUpdated is not None
        assert encounter.meta.source == "http://hospital.example.org/fhir"
    
    def test_encounter_version_before_period_start(self):
        """Test encounter with version lastUpdated before period start raises error."""
        encounter_data = {
            "id": "test-003",
            "meta": {
                "versionId": "1",
                "lastUpdated": "2024-01-01T08:00:00Z"  # Before period start
            },
            "resourceType": "Encounter",
            "status": "finished",
            "class": {
                "code": "IMP",
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "display": "inpatient"
            },
            "subject": {"reference": "Patient/789"},
            "period": {
                "start": "2024-01-01T10:00:00Z",
                "end": "2024-01-01T12:00:00Z"
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            MimicEncounter(**encounter_data)
        assert "cannot be before period.start" in str(exc_info.value)
    
    def test_encounter_no_meta(self):
        """Test encounter without meta is valid."""
        encounter_data = {
            "id": "test-004",
            "resourceType": "Encounter",
            "status": "finished",
            "class": {
                "code": "AMB",
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "display": "ambulatory"
            },
            "subject": {"reference": "Patient/101"},
            "period": {
                "start": "2024-01-01T10:00:00Z",
                "end": "2024-01-01T12:00:00Z"
            }
        }
        encounter = MimicEncounter(**encounter_data)
        assert encounter.meta is None


class TestProcessedEncounterMetaValidation:
    """Test Meta field validation in ProcessedEncounter."""
    
    def test_processed_with_profile(self):
        """Test processed encounter with profile metadata."""
        processed = ProcessedEncounter(
            encounter_id="test-001",
            resourceType="Encounter",
            status=EncounterStatus.FINISHED,
            encounter_class="AMB",
            encounter_class_display="ambulatory",
            period_start="2024-01-01T10:00:00Z",
            period_end="2024-01-01T12:00:00Z",
            patient_reference="Patient/123",
            patient_id="123456789-abc",
            location_count=2,
            encounter_duration_hours=2.0,
            profile=["http://mimic.mit.edu/fhir/mimic/StructureDefinition/mimic-encounter"]
        )
        assert processed.profile is not None
        assert len(processed.profile) == 1
    
    def test_processed_with_version_metadata(self):
        """Test processed encounter with version tracking metadata."""
        processed = ProcessedEncounter(
            encounter_id="test-002",
            resourceType="Encounter",
            status=EncounterStatus.FINISHED,
            encounter_class="EMER",
            encounter_class_display="emergency",
            period_start="2024-01-01T10:00:00Z",
            period_end="2024-01-01T12:00:00Z",
            patient_reference="Patient/456",
            patient_id="456789012-def",
            location_count=3,
            encounter_duration_hours=5.5,
            version_id="1",
            last_updated=datetime(2024, 1, 1, 12, 30),
            source_system="http://hospital.example.org/fhir",
            profile=["http://mimic.mit.edu/fhir/mimic/StructureDefinition/mimic-encounter"]
        )
        assert processed.version_id == "1"
        assert processed.last_updated is not None
        assert processed.source_system == "http://hospital.example.org/fhir"
    
    def test_processed_version_without_timestamp(self):
        """Test processed encounter with version but no timestamp raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessedEncounter(
                encounter_id="test-003",
                resourceType="Encounter",
                status=EncounterStatus.FINISHED,
                encounter_class="IMP",
                encounter_class_display="inpatient",
                period_start="2024-01-01T10:00:00Z",
                period_end="2024-01-01T12:00:00Z",
                patient_reference="Patient/789",
                patient_id="789012345-ghi",
                location_count=1,
                version_id="1",
                last_updated=None  # Missing timestamp
            )
        assert "last_updated must also be present" in str(exc_info.value)
    
    def test_processed_last_updated_before_start(self):
        """Test last_updated before period_start raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessedEncounter(
                encounter_id="test-004",
                resourceType="Encounter",
                status=EncounterStatus.FINISHED,
                encounter_class="AMB",
                encounter_class_display="ambulatory",
                period_start="2024-01-01T10:00:00Z",
                period_end="2024-01-01T12:00:00Z",
                patient_reference="Patient/101",
                patient_id="101112131-jkl",
                location_count=1,
                version_id="1",
                last_updated=datetime(2024, 1, 1, 8, 0)  # Before period start
            )
        assert "cannot be before period_start" in str(exc_info.value)
    
    def test_processed_without_version_fields(self):
        """Test processed encounter without version fields is valid."""
        processed = ProcessedEncounter(
            encounter_id="test-005",
            resourceType="Encounter",
            status=EncounterStatus.FINISHED,
            encounter_class="OBSENC",
            encounter_class_display="observation encounter",
            period_start="2024-01-01T10:00:00Z",
            period_end="2024-01-01T18:00:00Z",
            patient_reference="Patient/202",
            patient_id="202223242-mno",
            location_count=4,
            encounter_duration_hours=8.0
        )
        assert processed.version_id is None
        assert processed.last_updated is None
        assert processed.source_system is None
        assert processed.profile is None


class TestMetaEdgeCases:
    """Test edge cases and boundary conditions for Meta validation."""
    
    def test_meta_with_whitespace_version(self):
        """Test version ID with whitespace."""
        meta = Meta(
            versionId="  ",
            lastUpdated=None
        )
        # Whitespace-only should be treated as empty
        assert meta.versionId == "  "
    
    def test_meta_very_old_last_updated(self):
        """Test very old lastUpdated timestamp."""
        old_time = datetime(1970, 1, 1, 0, 0, 0)
        meta = Meta(
            versionId="1",
            lastUpdated=old_time
        )
        assert meta.lastUpdated == old_time
    
    def test_meta_multiple_profiles(self):
        """Test meta with multiple FHIR profiles."""
        meta = Meta(
            profile=[
                "http://mimic.mit.edu/fhir/mimic/StructureDefinition/mimic-encounter",
                "http://hl7.org/fhir/StructureDefinition/Encounter"
            ]
        )
        assert len(meta.profile) == 2
    
    def test_encounter_with_version_after_period_end(self):
        """Test encounter with lastUpdated after period end (valid scenario)."""
        encounter_data = {
            "id": "test-006",
            "meta": {
                "versionId": "1",
                "lastUpdated": "2024-01-01T14:00:00Z"  # After period end
            },
            "resourceType": "Encounter",
            "status": "finished",
            "class": {
                "code": "AMB",
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "display": "ambulatory"
            },
            "subject": {"reference": "Patient/303"},
            "period": {
                "start": "2024-01-01T10:00:00Z",
                "end": "2024-01-01T12:00:00Z"
            }
        }
        # This should be valid - record updated after encounter ended
        encounter = MimicEncounter(**encounter_data)
        assert encounter.meta.lastUpdated is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
