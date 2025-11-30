"""
Pydantic models for MIMIC-IV FHIR Encounter data validation.

These models provide comprehensive data validation for FHIR Encounter resources
following the MIMIC-IV structure, ensuring data quality and type safety
throughout the processing pipeline.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class EncounterStatus(str, Enum):
    """Valid FHIR encounter status values"""
    PLANNED = "planned"
    ARRIVED = "arrived"
    TRIAGED = "triaged"
    IN_PROGRESS = "in-progress"
    ONLEAVE = "onleave"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class ActCode(str, Enum):
    """Valid encounter class codes"""
    AMB = "AMB"  # ambulatory
    EMER = "EMER"  # emergency
    OBSENC = "OBSENC"  # observation encounter
    SS = "SS"  # short stay
    IMP = "IMP"  # inpatient encounter


class PriorityCode(str, Enum):
    """Valid priority codes"""
    EM = "EM"  # emergency
    UR = "UR"  # urgent
    R = "R"  # routine
    S = "S"  # stat


class Coding(BaseModel):
    """FHIR Coding data type"""
    code: str = Field(..., description="Symbol in syntax defined by the system")
    system: Optional[str] = Field(None, description="Identity of the terminology system")
    display: Optional[str] = Field(None, description="Representation defined by the system")

    class Config:
        extra = "allow"


class CodeableConcept(BaseModel):
    """FHIR CodeableConcept data type"""
    coding: List[Coding] = Field(default_factory=list, description="Code defined by a terminology system")
    text: Optional[str] = Field(None, description="Plain text representation")

    @field_validator('coding')
    @classmethod
    def validate_coding_not_empty(cls, v):
        if not v:
            raise ValueError("CodeableConcept must have at least one coding")
        return v


class Reference(BaseModel):
    """FHIR Reference data type"""
    reference: str = Field(..., description="Literal reference, Relative, internal or absolute URL")
    display: Optional[str] = Field(None, description="Text alternative for the resource")

    @field_validator('reference')
    @classmethod
    def validate_reference_format(cls, v):
        if not v or '/' not in v:
            raise ValueError("Reference must be in format 'ResourceType/id'")
        return v


class Period(BaseModel):
    """FHIR Period data type"""
    start: str = Field(..., description="Starting time with inclusive boundary (ISO 8601 format)")
    end: Optional[str] = Field(None, description="End time with inclusive boundary (ISO 8601 format)")

    @field_validator('start', 'end')
    @classmethod
    def validate_datetime_format(cls, v):
        if v is None:
            return v
        # Validate ISO 8601 datetime format
        try:
            # Try to parse the datetime string
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid datetime format: {v}. Expected ISO 8601 format")
        return v

    @model_validator(mode='after')
    def validate_period_order(self):
        """Ensure start is before or equal to end"""
        if self.start and self.end:
            try:
                start_dt = datetime.fromisoformat(self.start.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(self.end.replace('Z', '+00:00'))
                if start_dt > end_dt:
                    raise ValueError("Period start must be before or equal to end")
            except ValueError as e:
                if "Period start" in str(e):
                    raise
                # If parsing fails, just skip the validation
                pass
        return self


class EncounterClass(BaseModel):
    """Encounter classification"""
    code: ActCode = Field(..., description="Encounter class code")
    system: str = Field(..., description="Identity of the terminology system")
    display: str = Field(..., description="Display name for the class")


class Meta(BaseModel):
    """FHIR Meta data type"""
    profile: Optional[List[str]] = Field(None, description="Profiles this resource claims to conform to")

    class Config:
        extra = "allow"


class Identifier(BaseModel):
    """FHIR Identifier data type"""
    use: Optional[str] = Field(None, description="usual | official | temp | secondary")
    value: str = Field(..., description="The value that is unique")
    system: Optional[str] = Field(None, description="The namespace for the identifier value")
    assigner: Optional[Reference] = Field(None, description="Organization that issued id")

    class Config:
        extra = "allow"


class Location(BaseModel):
    """Encounter location information"""
    location: Reference = Field(..., description="Location the encounter takes place")
    period: Optional[Period] = Field(None, description="Time period during which the patient was at the location")

    class Config:
        extra = "allow"


class Hospitalization(BaseModel):
    """Details about an admission to a hospital"""
    admitSource: Optional[CodeableConcept] = Field(None, description="From where patient was admitted")
    dischargeDisposition: Optional[CodeableConcept] = Field(None, description="Category or kind of location after discharge")

    class Config:
        extra = "allow"


class MimicEncounter(BaseModel):
    """
    MIMIC-IV FHIR Encounter resource model.
    
    Represents a patient encounter with comprehensive validation
    following FHIR standards and MIMIC-IV specifications.
    """
    resourceType: str = Field(..., description="Must be 'Encounter'")
    id: str = Field(..., description="Logical id of this artifact", min_length=1)
    meta: Optional[Meta] = Field(None, description="Metadata about the resource")
    status: EncounterStatus = Field(..., description="Status of the encounter")
    
    # Use dict for class field to avoid Python keyword conflict
    encounter_class: EncounterClass = Field(..., alias="class", description="Classification of patient encounter")
    
    type: Optional[List[CodeableConcept]] = Field(None, description="Specific type of encounter")
    priority: Optional[CodeableConcept] = Field(None, description="Indicates the urgency of the encounter")
    subject: Reference = Field(..., description="The patient present at the encounter")
    period: Optional[Period] = Field(None, description="The start and end time of the encounter")
    location: Optional[List[Location]] = Field(default_factory=list, description="List of locations where the patient has been")
    serviceType: Optional[CodeableConcept] = Field(None, description="Specific type of service")
    identifier: Optional[List[Identifier]] = Field(None, description="Identifier(s) by which this encounter is known")
    hospitalization: Optional[Hospitalization] = Field(None, description="Details about the admission to a healthcare service")
    serviceProvider: Optional[Reference] = Field(None, description="The organization responsible for this encounter")

    class Config:
        extra = "allow"
        populate_by_name = True

    @field_validator('resourceType')
    @classmethod
    def validate_resource_type(cls, v):
        if v != "Encounter":
            raise ValueError(f"resourceType must be 'Encounter', got '{v}'")
        return v

    @model_validator(mode='after')
    def validate_encounter_data(self):
        """Additional business logic validation"""
        # If status is finished, period end should be present
        if self.status == EncounterStatus.FINISHED and self.period and not self.period.end:
            raise ValueError("Finished encounters must have a period end time")
        
        # Validate that locations have periods
        if self.location:
            for loc in self.location:
                if not loc.period:
                    raise ValueError("All locations must have a period")
        
        return self

    def get_patient_id(self) -> str:
        """Extract patient ID from subject reference"""
        return self.subject.reference.split('/')[-1]

    def get_encounter_duration_hours(self) -> Optional[float]:
        """Calculate encounter duration in hours"""
        if not self.period or not self.period.start or not self.period.end:
            return None
        
        try:
            start = datetime.fromisoformat(self.period.start.replace('Z', '+00:00'))
            end = datetime.fromisoformat(self.period.end.replace('Z', '+00:00'))
            duration = (end - start).total_seconds() / 3600
            return round(duration, 2)
        except ValueError:
            return None

    def is_high_priority(self) -> bool:
        """Check if encounter is high priority (emergency or urgent)"""
        if not self.priority or not self.priority.coding:
            return False
        
        priority_code = self.priority.coding[0].code
        return priority_code in [PriorityCode.EM.value, PriorityCode.UR.value]

    def get_location_count(self) -> int:
        """Get number of locations for this encounter"""
        return len(self.location) if self.location else 0


class ProcessedEncounter(BaseModel):
    """
    Flattened and processed encounter model for downstream analytics.
    
    This model represents the extracted and validated data after
    processing the raw FHIR encounter data.
    """
    encounter_id: str = Field(..., description="Unique encounter identifier")
    resourceType: str = Field(..., description="Resource type (Encounter)")
    status: EncounterStatus = Field(..., description="Encounter status")
    encounter_class: str = Field(..., description="Encounter class code")
    encounter_class_display: str = Field(..., description="Encounter class display name")
    period_start: str = Field(..., description="Encounter start time")
    period_end: Optional[str] = Field(None, description="Encounter end time")
    patient_reference: str = Field(..., description="Patient reference")
    patient_id: str = Field(..., description="Extracted patient ID")
    priority_code: Optional[str] = Field(None, description="Priority code")
    priority_display: Optional[str] = Field(None, description="Priority display name")
    service_type: Optional[str] = Field(None, description="Service type code")
    admit_source: Optional[str] = Field(None, description="Admission source code")
    discharge_disposition: Optional[str] = Field(None, description="Discharge disposition code")
    encounter_identifier: Optional[str] = Field(None, description="Primary encounter identifier value")
    location_count: int = Field(..., description="Number of locations", ge=0)
    encounter_duration_hours: Optional[float] = Field(None, description="Encounter duration in hours", ge=0)

    class Config:
        extra = "forbid"

    @field_validator('patient_id')
    @classmethod
    def validate_patient_id_format(cls, v):
        """Ensure patient ID is a valid UUID or identifier"""
        if not v or len(v) < 10:
            raise ValueError("Patient ID must be a valid identifier")
        return v
