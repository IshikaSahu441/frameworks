"""
Pydantic models for MIMIC-III Admission data validation.

These models provide comprehensive schema validation for patient admission records,
ensuring data quality and type safety across the Intelligent Real-Time Patient Flow
Optimization pipeline.

Validates:
- Patient and admission identifiers
- Temporal data (admit/discharge/death times)
- Admission metadata (type, location, insurance)
- Patient demographics
- Business rules and data integrity constraints
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class AdmissionType(str, Enum):
    """Valid admission types in MIMIC-III dataset."""
    EMERGENCY = "EMERGENCY"
    URGENT = "URGENT"
    ELECTIVE = "ELECTIVE"
    NEWBORN = "NEWBORN"


class InsuranceType(str, Enum):
    """Valid insurance types."""
    MEDICARE = "Medicare"
    MEDICAID = "Medicaid"
    PRIVATE = "Private"
    GOVERNMENT = "Government"
    SELF_PAY = "Self Pay"


class Language(str, Enum):
    """Common language codes."""
    ENGLISH = "ENGL"
    SPANISH = "SPAN"
    PORTUGUESE = "PORT"
    RUSSIAN = "RUSS"
    CHINESE = "CANT"
    UNKNOWN = ""


class AdmissionLocation(BaseModel):
    """
    Admission location information with validation.
    Represents where the patient was admitted from.
    """
    location: str = Field(..., description="Source location for admission")
    
    @field_validator('location')
    @classmethod
    def validate_location_not_empty(cls, v):
        """Ensure location is not empty."""
        if not v or not v.strip():
            raise ValueError("Admission location cannot be empty")
        return v.strip()


class DischargeLocation(BaseModel):
    """
    Discharge location information with validation.
    Represents where the patient was discharged to.
    """
    location: str = Field(..., description="Destination location for discharge")
    
    @field_validator('location')
    @classmethod
    def validate_location_not_empty(cls, v):
        """Ensure location is not empty."""
        if not v or not v.strip():
            raise ValueError("Discharge location cannot be empty")
        return v.strip()


class PatientDemographics(BaseModel):
    """
    Patient demographic information with validation.
    """
    marital_status: Optional[str] = Field(None, description="Patient marital status")
    ethnicity: str = Field(..., description="Patient ethnicity")
    language: Optional[str] = Field(None, description="Primary language")
    religion: Optional[str] = Field(None, description="Religious affiliation")
    
    @field_validator('ethnicity')
    @classmethod
    def validate_ethnicity_not_empty(cls, v):
        """Ensure ethnicity is provided."""
        if not v or not v.strip():
            raise ValueError("Ethnicity must be provided")
        return v.strip()


class AdmissionTiming(BaseModel):
    """
    Temporal information for admission with validation.
    Ensures temporal consistency across admission lifecycle.
    """
    admit_time: datetime = Field(..., description="Hospital admission timestamp")
    discharge_time: datetime = Field(..., description="Hospital discharge timestamp")
    death_time: Optional[datetime] = Field(None, description="Death timestamp if patient expired")
    ed_reg_time: Optional[datetime] = Field(None, description="Emergency department registration time")
    ed_out_time: Optional[datetime] = Field(None, description="Emergency department exit time")
    
    @model_validator(mode='after')
    def validate_temporal_consistency(self):
        """
        Validate temporal logic across all timestamps.
        
        Rules:
        1. discharge_time must be after admit_time
        2. death_time must be after admit_time (if present)
        3. death_time must be at or before discharge_time (if present)
        4. ed_out_time must be after ed_reg_time (if both present)
        5. ed_reg_time must be at or before admit_time (if present)
        """
        # Rule 1: Discharge after admission
        if self.discharge_time <= self.admit_time:
            raise ValueError(
                f"discharge_time ({self.discharge_time}) must be after admit_time ({self.admit_time})"
            )
        
        # Rule 2: Death after admission
        if self.death_time:
            if self.death_time < self.admit_time:
                raise ValueError(
                    f"death_time ({self.death_time}) cannot be before admit_time ({self.admit_time})"
                )
            
            # Rule 3: Death at or before discharge
            if self.death_time > self.discharge_time:
                raise ValueError(
                    f"death_time ({self.death_time}) cannot be after discharge_time ({self.discharge_time})"
                )
        
        # Rule 4: ED exit after ED registration
        if self.ed_reg_time and self.ed_out_time:
            if self.ed_out_time <= self.ed_reg_time:
                raise ValueError(
                    f"ed_out_time ({self.ed_out_time}) must be after ed_reg_time ({self.ed_reg_time})"
                )
        
        # Rule 5: ED registration before/at admission
        if self.ed_reg_time:
            if self.ed_reg_time > self.admit_time:
                raise ValueError(
                    f"ed_reg_time ({self.ed_reg_time}) cannot be after admit_time ({self.admit_time})"
                )
        
        return self
    
    def get_length_of_stay_hours(self) -> float:
        """Calculate length of stay in hours."""
        duration = self.discharge_time - self.admit_time
        return duration.total_seconds() / 3600
    
    def get_length_of_stay_days(self) -> float:
        """Calculate length of stay in days."""
        return self.get_length_of_stay_hours() / 24
    
    def get_ed_wait_time_hours(self) -> Optional[float]:
        """Calculate ED wait time in hours (if ED times present)."""
        if self.ed_reg_time and self.ed_out_time:
            duration = self.ed_out_time - self.ed_reg_time
            return duration.total_seconds() / 3600
        return None


class AdmissionRecord(BaseModel):
    """
    Complete MIMIC-III admission record with comprehensive validation.
    
    Represents a single patient hospital admission with all associated metadata,
    ensuring data quality for the Patient Flow Optimization System.
    """
    # Identifiers
    row_id: int = Field(..., description="Unique row identifier", ge=1)
    subject_id: int = Field(..., description="Patient identifier", ge=1)
    hadm_id: int = Field(..., description="Hospital admission identifier", ge=1)
    
    # Temporal data
    admit_time: datetime = Field(..., description="Hospital admission timestamp")
    discharge_time: datetime = Field(..., description="Hospital discharge timestamp")
    death_time: Optional[datetime] = Field(None, description="Death timestamp if patient expired")
    ed_reg_time: Optional[datetime] = Field(None, description="Emergency department registration time")
    ed_out_time: Optional[datetime] = Field(None, description="Emergency department exit time")
    
    # Admission metadata
    admission_type: str = Field(..., description="Type of admission")
    admission_location: str = Field(..., description="Admission source location")
    discharge_location: str = Field(..., description="Discharge destination")
    
    # Financial and administrative
    insurance: str = Field(..., description="Insurance type")
    diagnosis: Optional[str] = Field(None, description="Primary diagnosis")
    
    # Patient demographics
    language: Optional[str] = Field(None, description="Primary language")
    religion: Optional[str] = Field(None, description="Religious affiliation")
    marital_status: Optional[str] = Field(None, description="Marital status")
    ethnicity: str = Field(..., description="Patient ethnicity")
    
    # Clinical flags
    hospital_expire_flag: int = Field(..., description="1 if patient died, 0 otherwise", ge=0, le=1)
    has_chartevents_data: int = Field(..., description="1 if chart events exist, 0 otherwise", ge=0, le=1)
    
    class Config:
        extra = "forbid"  # Reject any extra fields not defined in schema
        str_strip_whitespace = True  # Strip whitespace from strings
    
    @field_validator('admission_type')
    @classmethod
    def validate_admission_type(cls, v):
        """Validate admission type against known values."""
        valid_types = ["EMERGENCY", "URGENT", "ELECTIVE", "NEWBORN"]
        if v not in valid_types:
            raise ValueError(
                f"admission_type must be one of {valid_types}, got: {v}"
            )
        return v
    
    @field_validator('insurance')
    @classmethod
    def validate_insurance(cls, v):
        """Validate insurance type."""
        valid_insurance = ["Medicare", "Medicaid", "Private", "Government", "Self Pay"]
        if v not in valid_insurance:
            raise ValueError(
                f"insurance must be one of {valid_insurance}, got: {v}"
            )
        return v
    
    @field_validator('admission_location', 'discharge_location')
    @classmethod
    def validate_location_not_empty(cls, v):
        """Ensure locations are not empty."""
        if not v or not v.strip():
            raise ValueError("Location fields cannot be empty")
        return v.strip()
    
    @field_validator('ethnicity')
    @classmethod
    def validate_ethnicity(cls, v):
        """Ensure ethnicity is provided."""
        if not v or not v.strip():
            raise ValueError("Ethnicity must be provided")
        return v.strip()
    
    @model_validator(mode='after')
    def validate_business_rules(self):
        """
        Validate business rules and data consistency.
        
        Rules:
        1. Temporal consistency (discharge after admission, etc.)
        2. Death flag consistency with death_time
        3. ED times consistency
        """
        # Rule 1: Temporal consistency
        if self.discharge_time <= self.admit_time:
            raise ValueError(
                f"discharge_time must be after admit_time"
            )
        
        # Rule 2: Death flag consistency
        if self.hospital_expire_flag == 1:
            if not self.death_time:
                raise ValueError(
                    "hospital_expire_flag is 1 but death_time is missing"
                )
        else:
            if self.death_time:
                raise ValueError(
                    "hospital_expire_flag is 0 but death_time is present"
                )
        
        # Additional temporal validations
        if self.death_time:
            if self.death_time < self.admit_time:
                raise ValueError("death_time cannot be before admit_time")
            if self.death_time > self.discharge_time:
                raise ValueError("death_time cannot be after discharge_time")
        
        if self.ed_reg_time and self.ed_out_time:
            if self.ed_out_time <= self.ed_reg_time:
                raise ValueError("ed_out_time must be after ed_reg_time")
        
        if self.ed_reg_time:
            if self.ed_reg_time > self.admit_time:
                raise ValueError("ed_reg_time cannot be after admit_time")
        
        return self
    
    # Helper methods for feature engineering
    def get_length_of_stay_hours(self) -> float:
        """Calculate length of stay in hours."""
        duration = self.discharge_time - self.admit_time
        return duration.total_seconds() / 3600
    
    def get_length_of_stay_days(self) -> float:
        """Calculate length of stay in days."""
        return self.get_length_of_stay_hours() / 24
    
    def is_emergency_admission(self) -> bool:
        """Check if admission is emergency type."""
        return self.admission_type == "EMERGENCY"
    
    def is_readmission_risk(self) -> bool:
        """
        Basic readmission risk indicator.
        Could be enhanced with ML model predictions.
        """
        # Simple heuristic: long stay or death
        return self.get_length_of_stay_days() > 7 or self.hospital_expire_flag == 1
    
    def get_ed_wait_time_hours(self) -> Optional[float]:
        """Calculate ED wait time in hours."""
        if self.ed_reg_time and self.ed_out_time:
            duration = self.ed_out_time - self.ed_reg_time
            return duration.total_seconds() / 3600
        return None
    
    def is_high_priority(self) -> bool:
        """Determine if admission is high priority (emergency or urgent)."""
        return self.admission_type in ["EMERGENCY", "URGENT"]
    
    def get_patient_outcome(self) -> str:
        """Get patient outcome classification."""
        if self.hospital_expire_flag == 1:
            return "DECEASED"
        elif "HOME" in self.discharge_location.upper():
            return "DISCHARGED_HOME"
        elif "REHAB" in self.discharge_location.upper():
            return "DISCHARGED_REHAB"
        elif "SNF" in self.discharge_location.upper() or "SKILLED" in self.discharge_location.upper():
            return "DISCHARGED_SNF"
        else:
            return "DISCHARGED_OTHER"


class ProcessedAdmission(BaseModel):
    """
    Flattened and enriched admission model for analytics and ML.
    
    This model represents the processed admission data with derived features,
    ready for downstream processing by Ray, Temporal, and Iceberg.
    """
    # Core identifiers
    row_id: int = Field(..., ge=1)
    subject_id: int = Field(..., ge=1)
    hadm_id: int = Field(..., ge=1)
    
    # Temporal features
    admit_time: datetime
    discharge_time: datetime
    death_time: Optional[datetime] = None
    length_of_stay_hours: float = Field(..., ge=0)
    length_of_stay_days: float = Field(..., ge=0)
    ed_wait_time_hours: Optional[float] = Field(None, ge=0)
    
    # Admission metadata
    admission_type: str
    admission_location: str
    discharge_location: str
    insurance: str
    diagnosis: Optional[str] = None
    
    # Demographics
    ethnicity: str
    marital_status: Optional[str] = None
    language: Optional[str] = None
    religion: Optional[str] = None
    
    # Clinical outcomes
    hospital_expire_flag: int = Field(..., ge=0, le=1)
    patient_outcome: str = Field(..., description="Classified patient outcome")
    
    # Derived features (for ML and analytics)
    is_emergency: bool = Field(..., description="True if emergency admission")
    is_high_priority: bool = Field(..., description="True if emergency or urgent")
    is_readmission_risk: bool = Field(..., description="Simple readmission risk flag")
    has_ed_visit: bool = Field(..., description="True if ED visit recorded")
    
    # Data quality flags
    has_chartevents_data: int = Field(..., ge=0, le=1)
    
    class Config:
        extra = "forbid"
    
    @field_validator('length_of_stay_hours', 'length_of_stay_days')
    @classmethod
    def validate_positive_duration(cls, v):
        """Ensure durations are positive."""
        if v < 0:
            raise ValueError(f"Duration cannot be negative: {v}")
        return v
    
    @field_validator('patient_outcome')
    @classmethod
    def validate_outcome(cls, v):
        """Validate patient outcome classification."""
        valid_outcomes = [
            "DECEASED", "DISCHARGED_HOME", "DISCHARGED_REHAB", 
            "DISCHARGED_SNF", "DISCHARGED_OTHER"
        ]
        if v not in valid_outcomes:
            raise ValueError(f"patient_outcome must be one of {valid_outcomes}, got: {v}")
        return v
    
    @model_validator(mode='after')
    def validate_consistency(self):
        """Validate internal consistency of processed record."""
        # Check LOS consistency
        calculated_los_hours = (self.discharge_time - self.admit_time).total_seconds() / 3600
        if abs(calculated_los_hours - self.length_of_stay_hours) > 0.1:  # Allow small floating point diff
            raise ValueError(
                f"length_of_stay_hours ({self.length_of_stay_hours}) doesn't match "
                f"calculated duration ({calculated_los_hours:.2f})"
            )
        
        # Check death flag and outcome consistency
        if self.hospital_expire_flag == 1 and self.patient_outcome != "DECEASED":
            raise ValueError(
                f"hospital_expire_flag is 1 but patient_outcome is {self.patient_outcome}"
            )
        
        if self.hospital_expire_flag == 0 and self.patient_outcome == "DECEASED":
            raise ValueError(
                "hospital_expire_flag is 0 but patient_outcome is DECEASED"
            )
        
        # Check ED flags consistency
        if self.has_ed_visit and self.ed_wait_time_hours is None:
            raise ValueError(
                "has_ed_visit is True but ed_wait_time_hours is None"
            )
        
        return self


class AdmissionBatch(BaseModel):
    """
    Batch of admission records for bulk validation.
    Useful for validating large datasets processed by Daft.
    """
    admissions: List[AdmissionRecord] = Field(..., description="List of admission records")
    batch_id: Optional[str] = Field(None, description="Batch identifier for tracking")
    validation_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When this batch was validated"
    )
    
    @field_validator('admissions')
    @classmethod
    def validate_not_empty(cls, v):
        """Ensure batch is not empty."""
        if not v:
            raise ValueError("Admission batch cannot be empty")
        return v
    
    def get_validation_summary(self) -> dict:
        """Get summary statistics for the validated batch."""
        return {
            "total_records": len(self.admissions),
            "emergency_count": sum(1 for a in self.admissions if a.is_emergency_admission()),
            "death_count": sum(1 for a in self.admissions if a.hospital_expire_flag == 1),
            "avg_length_of_stay_days": sum(a.get_length_of_stay_days() for a in self.admissions) / len(self.admissions),
            "validation_timestamp": self.validation_timestamp.isoformat()
        }
