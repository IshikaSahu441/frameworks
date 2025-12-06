"""
Unit tests for admission Pydantic models.

Tests comprehensive validation logic for patient admission records,
ensuring data quality for the Patient Flow Optimization System.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from Pydantic.admission_models import (
    AdmissionRecord,
    ProcessedAdmission,
    AdmissionTiming,
    AdmissionBatch
)


class TestAdmissionTiming:
    """Test temporal validation logic."""
    
    def test_valid_timing(self):
        """Test valid admission timing."""
        timing = AdmissionTiming(
            admit_time=datetime(2024, 1, 1, 10, 0),
            discharge_time=datetime(2024, 1, 3, 14, 0),
            death_time=None,
            ed_reg_time=datetime(2024, 1, 1, 8, 0),
            ed_out_time=datetime(2024, 1, 1, 9, 30)
        )
        assert timing.get_length_of_stay_hours() == 52.0
        assert timing.get_length_of_stay_days() == pytest.approx(2.17, rel=0.01)
        assert timing.get_ed_wait_time_hours() == 1.5
    
    def test_discharge_before_admit_fails(self):
        """Test that discharge before admission raises error."""
        with pytest.raises(ValidationError) as exc_info:
            AdmissionTiming(
                admit_time=datetime(2024, 1, 3, 10, 0),
                discharge_time=datetime(2024, 1, 1, 10, 0),  # Before admission
                death_time=None
            )
        assert "must be after admit_time" in str(exc_info.value)
    
    def test_death_before_admit_fails(self):
        """Test that death before admission raises error."""
        with pytest.raises(ValidationError) as exc_info:
            AdmissionTiming(
                admit_time=datetime(2024, 1, 2, 10, 0),
                discharge_time=datetime(2024, 1, 3, 10, 0),
                death_time=datetime(2024, 1, 1, 10, 0)  # Before admission
            )
        assert "cannot be before admit_time" in str(exc_info.value)
    
    def test_death_after_discharge_fails(self):
        """Test that death after discharge raises error."""
        with pytest.raises(ValidationError) as exc_info:
            AdmissionTiming(
                admit_time=datetime(2024, 1, 1, 10, 0),
                discharge_time=datetime(2024, 1, 2, 10, 0),
                death_time=datetime(2024, 1, 3, 10, 0)  # After discharge
            )
        assert "cannot be after discharge_time" in str(exc_info.value)
    
    def test_ed_out_before_ed_reg_fails(self):
        """Test that ED exit before registration raises error."""
        with pytest.raises(ValidationError) as exc_info:
            AdmissionTiming(
                admit_time=datetime(2024, 1, 1, 10, 0),
                discharge_time=datetime(2024, 1, 2, 10, 0),
                ed_reg_time=datetime(2024, 1, 1, 9, 0),
                ed_out_time=datetime(2024, 1, 1, 8, 0)  # Before registration
            )
        assert "must be after ed_reg_time" in str(exc_info.value)
    
    def test_ed_reg_after_admit_fails(self):
        """Test that ED registration after admission raises error."""
        with pytest.raises(ValidationError) as exc_info:
            AdmissionTiming(
                admit_time=datetime(2024, 1, 1, 10, 0),
                discharge_time=datetime(2024, 1, 2, 10, 0),
                ed_reg_time=datetime(2024, 1, 1, 11, 0)  # After admission
            )
        assert "cannot be after admit_time" in str(exc_info.value)


class TestAdmissionRecord:
    """Test complete admission record validation."""
    
    def create_valid_admission(self) -> dict:
        """Helper to create valid admission data."""
        return {
            "row_id": 1,
            "subject_id": 100,
            "hadm_id": 1000,
            "admit_time": datetime(2024, 1, 1, 10, 0),
            "discharge_time": datetime(2024, 1, 3, 14, 0),
            "death_time": None,
            "ed_reg_time": None,
            "ed_out_time": None,
            "admission_type": "EMERGENCY",
            "admission_location": "EMERGENCY ROOM ADMIT",
            "discharge_location": "HOME",
            "insurance": "Medicare",
            "diagnosis": "CHEST PAIN",
            "language": "ENGL",
            "religion": "CATHOLIC",
            "marital_status": "MARRIED",
            "ethnicity": "WHITE",
            "hospital_expire_flag": 0,
            "has_chartevents_data": 1
        }
    
    def test_valid_admission(self):
        """Test valid admission record."""
        data = self.create_valid_admission()
        admission = AdmissionRecord(**data)
        
        assert admission.subject_id == 100
        assert admission.hadm_id == 1000
        assert admission.is_emergency_admission() is True
        assert admission.is_high_priority() is True
        assert admission.get_length_of_stay_days() == pytest.approx(2.17, rel=0.01)
    
    def test_invalid_admission_type_fails(self):
        """Test invalid admission type raises error."""
        data = self.create_valid_admission()
        data["admission_type"] = "INVALID_TYPE"
        
        with pytest.raises(ValidationError) as exc_info:
            AdmissionRecord(**data)
        assert "admission_type" in str(exc_info.value)
    
    def test_invalid_insurance_fails(self):
        """Test invalid insurance type raises error."""
        data = self.create_valid_admission()
        data["insurance"] = "InvalidInsurance"
        
        with pytest.raises(ValidationError) as exc_info:
            AdmissionRecord(**data)
        assert "insurance" in str(exc_info.value)
    
    def test_empty_ethnicity_fails(self):
        """Test empty ethnicity raises error."""
        data = self.create_valid_admission()
        data["ethnicity"] = ""
        
        with pytest.raises(ValidationError) as exc_info:
            AdmissionRecord(**data)
        assert "Ethnicity must be provided" in str(exc_info.value)
    
    def test_death_flag_without_death_time_fails(self):
        """Test death flag without death time raises error."""
        data = self.create_valid_admission()
        data["hospital_expire_flag"] = 1
        data["death_time"] = None  # Missing death time
        
        with pytest.raises(ValidationError) as exc_info:
            AdmissionRecord(**data)
        assert "death_time is missing" in str(exc_info.value)
    
    def test_death_time_without_flag_fails(self):
        """Test death time without flag raises error."""
        data = self.create_valid_admission()
        data["hospital_expire_flag"] = 0
        data["death_time"] = datetime(2024, 1, 2, 10, 0)  # Has death time
        
        with pytest.raises(ValidationError) as exc_info:
            AdmissionRecord(**data)
        assert "death_time is present" in str(exc_info.value)
    
    def test_valid_death_record(self):
        """Test valid death record."""
        data = self.create_valid_admission()
        data["hospital_expire_flag"] = 1
        data["death_time"] = datetime(2024, 1, 2, 12, 0)
        data["discharge_location"] = "DEAD/EXPIRED"
        
        admission = AdmissionRecord(**data)
        assert admission.hospital_expire_flag == 1
        assert admission.death_time is not None
        assert admission.get_patient_outcome() == "DECEASED"
    
    def test_negative_ids_fail(self):
        """Test negative IDs raise error."""
        data = self.create_valid_admission()
        data["subject_id"] = -1
        
        with pytest.raises(ValidationError) as exc_info:
            AdmissionRecord(**data)
        assert "greater than or equal to 1" in str(exc_info.value).lower()
    
    def test_invalid_expire_flag_fails(self):
        """Test invalid expire flag raises error."""
        data = self.create_valid_admission()
        data["hospital_expire_flag"] = 2  # Must be 0 or 1
        
        with pytest.raises(ValidationError) as exc_info:
            AdmissionRecord(**data)
        assert "less than or equal to 1" in str(exc_info.value).lower()
    
    def test_get_ed_wait_time(self):
        """Test ED wait time calculation."""
        data = self.create_valid_admission()
        data["ed_reg_time"] = datetime(2024, 1, 1, 8, 0)
        data["ed_out_time"] = datetime(2024, 1, 1, 9, 30)
        
        admission = AdmissionRecord(**data)
        assert admission.get_ed_wait_time_hours() == 1.5
    
    def test_get_ed_wait_time_none_when_missing(self):
        """Test ED wait time returns None when times missing."""
        data = self.create_valid_admission()
        admission = AdmissionRecord(**data)
        assert admission.get_ed_wait_time_hours() is None
    
    def test_readmission_risk_long_stay(self):
        """Test readmission risk for long stays."""
        data = self.create_valid_admission()
        data["discharge_time"] = datetime(2024, 1, 10, 10, 0)  # 9 days
        
        admission = AdmissionRecord(**data)
        assert admission.is_readmission_risk() is True
    
    def test_readmission_risk_death(self):
        """Test readmission risk for deceased patients."""
        data = self.create_valid_admission()
        data["hospital_expire_flag"] = 1
        data["death_time"] = datetime(2024, 1, 2, 10, 0)
        
        admission = AdmissionRecord(**data)
        assert admission.is_readmission_risk() is True
    
    def test_elective_admission(self):
        """Test elective admission."""
        data = self.create_valid_admission()
        data["admission_type"] = "ELECTIVE"
        
        admission = AdmissionRecord(**data)
        assert admission.is_emergency_admission() is False
        assert admission.is_high_priority() is False
    
    def test_urgent_admission_is_high_priority(self):
        """Test urgent admission is high priority."""
        data = self.create_valid_admission()
        data["admission_type"] = "URGENT"
        
        admission = AdmissionRecord(**data)
        assert admission.is_high_priority() is True
    
    def test_patient_outcome_home(self):
        """Test patient outcome for home discharge."""
        data = self.create_valid_admission()
        data["discharge_location"] = "HOME HEALTH CARE"
        
        admission = AdmissionRecord(**data)
        assert admission.get_patient_outcome() == "DISCHARGED_HOME"
    
    def test_patient_outcome_rehab(self):
        """Test patient outcome for rehab."""
        data = self.create_valid_admission()
        data["discharge_location"] = "REHAB/DISTINCT PART HOSP"
        
        admission = AdmissionRecord(**data)
        assert admission.get_patient_outcome() == "DISCHARGED_REHAB"
    
    def test_patient_outcome_snf(self):
        """Test patient outcome for SNF."""
        data = self.create_valid_admission()
        data["discharge_location"] = "SKILLED NURSING FACILITY"
        
        admission = AdmissionRecord(**data)
        assert admission.get_patient_outcome() == "DISCHARGED_SNF"


class TestProcessedAdmission:
    """Test processed admission model."""
    
    def create_valid_processed(self) -> dict:
        """Helper to create valid processed admission."""
        admit_time = datetime(2024, 1, 1, 10, 0)
        discharge_time = datetime(2024, 1, 3, 14, 0)
        los_hours = (discharge_time - admit_time).total_seconds() / 3600
        
        return {
            "row_id": 1,
            "subject_id": 100,
            "hadm_id": 1000,
            "admit_time": admit_time,
            "discharge_time": discharge_time,
            "death_time": None,
            "length_of_stay_hours": los_hours,
            "length_of_stay_days": los_hours / 24,
            "ed_wait_time_hours": None,
            "admission_type": "EMERGENCY",
            "admission_location": "EMERGENCY ROOM ADMIT",
            "discharge_location": "HOME",
            "insurance": "Medicare",
            "diagnosis": "CHEST PAIN",
            "ethnicity": "WHITE",
            "marital_status": "MARRIED",
            "language": "ENGL",
            "religion": "CATHOLIC",
            "hospital_expire_flag": 0,
            "patient_outcome": "DISCHARGED_HOME",
            "is_emergency": True,
            "is_high_priority": True,
            "is_readmission_risk": False,
            "has_ed_visit": False,
            "has_chartevents_data": 1
        }
    
    def test_valid_processed(self):
        """Test valid processed admission."""
        data = self.create_valid_processed()
        processed = ProcessedAdmission(**data)
        
        assert processed.subject_id == 100
        assert processed.is_emergency is True
        assert processed.patient_outcome == "DISCHARGED_HOME"
    
    def test_negative_duration_fails(self):
        """Test negative duration raises error."""
        data = self.create_valid_processed()
        data["length_of_stay_hours"] = -5.0
        
        with pytest.raises(ValidationError) as exc_info:
            ProcessedAdmission(**data)
        assert "greater than or equal to 0" in str(exc_info.value)
    
    def test_invalid_outcome_fails(self):
        """Test invalid patient outcome raises error."""
        data = self.create_valid_processed()
        data["patient_outcome"] = "INVALID_OUTCOME"
        
        with pytest.raises(ValidationError) as exc_info:
            ProcessedAdmission(**data)
        assert "patient_outcome" in str(exc_info.value)
    
    def test_los_inconsistency_fails(self):
        """Test length of stay inconsistency raises error."""
        data = self.create_valid_processed()
        data["length_of_stay_hours"] = 100.0  # Doesn't match admit/discharge times
        
        with pytest.raises(ValidationError) as exc_info:
            ProcessedAdmission(**data)
        assert "doesn't match calculated duration" in str(exc_info.value)
    
    def test_death_flag_outcome_inconsistency_fails(self):
        """Test death flag and outcome inconsistency raises error."""
        data = self.create_valid_processed()
        data["hospital_expire_flag"] = 1
        data["patient_outcome"] = "DISCHARGED_HOME"  # Inconsistent
        
        with pytest.raises(ValidationError) as exc_info:
            ProcessedAdmission(**data)
        assert "patient_outcome" in str(exc_info.value)
    
    def test_ed_visit_without_wait_time_fails(self):
        """Test ED visit flag without wait time raises error."""
        data = self.create_valid_processed()
        data["has_ed_visit"] = True
        data["ed_wait_time_hours"] = None  # Missing
        
        with pytest.raises(ValidationError) as exc_info:
            ProcessedAdmission(**data)
        assert "ed_wait_time_hours is None" in str(exc_info.value)
    
    def test_valid_deceased_patient(self):
        """Test valid deceased patient record."""
        data = self.create_valid_processed()
        data["death_time"] = datetime(2024, 1, 2, 12, 0)
        data["hospital_expire_flag"] = 1
        data["patient_outcome"] = "DECEASED"
        
        processed = ProcessedAdmission(**data)
        assert processed.hospital_expire_flag == 1
        assert processed.patient_outcome == "DECEASED"


class TestAdmissionBatch:
    """Test batch validation."""
    
    def create_valid_admission(self) -> AdmissionRecord:
        """Helper to create valid admission record."""
        return AdmissionRecord(
            row_id=1,
            subject_id=100,
            hadm_id=1000,
            admit_time=datetime(2024, 1, 1, 10, 0),
            discharge_time=datetime(2024, 1, 3, 14, 0),
            death_time=None,
            ed_reg_time=None,
            ed_out_time=None,
            admission_type="EMERGENCY",
            admission_location="EMERGENCY ROOM ADMIT",
            discharge_location="HOME",
            insurance="Medicare",
            diagnosis="CHEST PAIN",
            language="ENGL",
            religion="CATHOLIC",
            marital_status="MARRIED",
            ethnicity="WHITE",
            hospital_expire_flag=0,
            has_chartevents_data=1
        )
    
    def test_valid_batch(self):
        """Test valid admission batch."""
        admissions = [self.create_valid_admission() for _ in range(5)]
        batch = AdmissionBatch(
            admissions=admissions,
            batch_id="test_batch",
            validation_timestamp=datetime.now()
        )
        
        assert len(batch.admissions) == 5
        assert batch.batch_id == "test_batch"
        
        summary = batch.get_validation_summary()
        assert summary["total_records"] == 5
        assert summary["emergency_count"] == 5
    
    def test_empty_batch_fails(self):
        """Test empty batch raises error."""
        with pytest.raises(ValidationError) as exc_info:
            AdmissionBatch(
                admissions=[],
                batch_id="empty_batch"
            )
        assert "cannot be empty" in str(exc_info.value)
    
    def test_batch_summary_statistics(self):
        """Test batch summary statistics."""
        # Create mixed batch
        admissions = []
        for i in range(10):
            adm = self.create_valid_admission()
            adm.row_id = i + 1
            adm.hadm_id = 1000 + i
            
            # Make some deaths
            if i < 2:
                adm.hospital_expire_flag = 1
                adm.death_time = datetime(2024, 1, 2, 10, 0)
            
            # Make some non-emergency
            if i >= 5:
                adm.admission_type = "ELECTIVE"
            
            admissions.append(adm)
        
        batch = AdmissionBatch(admissions=admissions)
        summary = batch.get_validation_summary()
        
        assert summary["total_records"] == 10
        assert summary["emergency_count"] == 5  # First 5 are emergency
        assert summary["death_count"] == 2
        assert "avg_length_of_stay_days" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
