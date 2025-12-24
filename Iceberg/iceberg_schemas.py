"""
Iceberg Table Schema Definitions

Defines comprehensive schemas for admission data tables with
column types, constraints, and partitioning strategy.
"""

from pyiceberg.schema import Schema
from pyiceberg.types import (
    NestedField,
    StringType,
    IntegerType,
    LongType,
    DoubleType,
    BooleanType,
    TimestampType,
    TimestamptzType,
    DateType,
    StructType,
    MapType,
    ListType
)


class AdmissionsSchema:
    """Schema for primary admissions table."""
    
    @staticmethod
    def get_schema() -> Schema:
        """
        Get the Iceberg schema for admissions table.
        
        Returns:
            PyIceberg Schema object
        """
        return Schema(
            NestedField(1, "row_id", LongType(), required=True),
            NestedField(2, "subject_id", LongType(), required=True),
            NestedField(3, "hadm_id", LongType(), required=True),
            NestedField(4, "admit_time", TimestampType(), required=True),
            NestedField(5, "discharge_time", TimestampType(), required=True),
            NestedField(6, "death_time", TimestampType(), required=False),
            NestedField(7, "admission_type", StringType(), required=True),
            NestedField(8, "admission_location", StringType(), required=True),
            NestedField(9, "discharge_location", StringType(), required=True),
            NestedField(10, "insurance", StringType(), required=True),
            NestedField(11, "language", StringType(), required=False),
            NestedField(12, "religion", StringType(), required=False),
            NestedField(13, "marital_status", StringType(), required=False),
            NestedField(14, "ethnicity", StringType(), required=True),
            NestedField(15, "ed_reg_time", TimestampType(), required=False),
            NestedField(16, "ed_out_time", TimestampType(), required=False),
            NestedField(17, "diagnosis", StringType(), required=False),
            NestedField(18, "hospital_expire_flag", IntegerType(), required=True),
            NestedField(19, "has_chartevents_data", IntegerType(), required=True),
            NestedField(20, "admission_year", IntegerType(), required=True),
            NestedField(21, "admission_month", IntegerType(), required=True),
        )


class EnrichedAdmissionsSchema:
    """Schema for enriched admissions table with derived features."""
    
    @staticmethod
    def get_schema() -> Schema:
        """
        Get the Iceberg schema for enriched admissions table.
        
        Returns:
            PyIceberg Schema object
        """
        return Schema(
            NestedField(1, "row_id", LongType(), required=True),
            NestedField(2, "subject_id", LongType(), required=True),
            NestedField(3, "hadm_id", LongType(), required=True),
            NestedField(4, "admit_time", TimestampType(), required=True),
            NestedField(5, "discharge_time", TimestampType(), required=True),
            NestedField(6, "death_time", TimestampType(), required=False),
            NestedField(7, "admission_type", StringType(), required=True),
            NestedField(8, "admission_location", StringType(), required=True),
            NestedField(9, "discharge_location", StringType(), required=True),
            NestedField(10, "insurance", StringType(), required=True),
            NestedField(11, "language", StringType(), required=False),
            NestedField(12, "religion", StringType(), required=False),
            NestedField(13, "marital_status", StringType(), required=False),
            NestedField(14, "ethnicity", StringType(), required=True),
            NestedField(15, "ed_reg_time", TimestampType(), required=False),
            NestedField(16, "ed_out_time", TimestampType(), required=False),
            NestedField(17, "diagnosis", StringType(), required=False),
            NestedField(18, "hospital_expire_flag", IntegerType(), required=True),
            NestedField(19, "has_chartevents_data", IntegerType(), required=True),
            # Derived/enriched fields
            NestedField(20, "length_of_stay_hours", DoubleType(), required=True),
            NestedField(21, "length_of_stay_days", DoubleType(), required=True),
            NestedField(22, "ed_wait_time_hours", DoubleType(), required=False),
            NestedField(23, "is_emergency", BooleanType(), required=True),
            NestedField(24, "is_elective", BooleanType(), required=True),
            NestedField(25, "is_newborn", BooleanType(), required=True),
            NestedField(26, "is_urgent", BooleanType(), required=True),
            NestedField(27, "patient_outcome", StringType(), required=True),
            NestedField(28, "is_high_priority", BooleanType(), required=True),
            NestedField(29, "has_ed_visit", BooleanType(), required=True),
            NestedField(30, "admission_year", IntegerType(), required=True),
            NestedField(31, "admission_month", IntegerType(), required=True),
            NestedField(32, "iceberg_insert_timestamp", TimestampType(), required=True),
        )


class AuditTrailSchema:
    """Schema for audit trail table tracking all data changes."""
    
    @staticmethod
    def get_schema() -> Schema:
        """
        Get the Iceberg schema for audit trail table.
        
        Returns:
            PyIceberg Schema object
        """
        return Schema(
            NestedField(1, "audit_id", StringType(), required=True),
            NestedField(2, "operation", StringType(), required=True),
            NestedField(3, "table_name", StringType(), required=True),
            NestedField(4, "user", StringType(), required=True),
            NestedField(5, "timestamp", TimestampType(), required=True),
            NestedField(6, "record_count", LongType(), required=True),
            NestedField(7, "changes", StringType(), required=False),  # JSON
            NestedField(8, "snapshot_id", LongType(), required=False),
            NestedField(9, "audit_year", IntegerType(), required=True),
            NestedField(10, "audit_month", IntegerType(), required=True),
        )


class SchemaEvolutionLogSchema:
    """Schema for tracking schema evolution and column changes."""
    
    @staticmethod
    def get_schema() -> Schema:
        """
        Get the Iceberg schema for schema evolution log table.
        
        Returns:
            PyIceberg Schema object
        """
        return Schema(
            NestedField(1, "evolution_id", StringType(), required=True),
            NestedField(2, "table_name", StringType(), required=True),
            NestedField(3, "change_type", StringType(), required=True),  # ADD_COLUMN, RENAME, TYPE_CHANGE
            NestedField(4, "column_name", StringType(), required=True),
            NestedField(5, "old_type", StringType(), required=False),
            NestedField(6, "new_type", StringType(), required=False),
            NestedField(7, "description", StringType(), required=False),
            NestedField(8, "change_timestamp", TimestampType(), required=True),
            NestedField(9, "applied_by", StringType(), required=True),
            NestedField(10, "schema_version", LongType(), required=True),
        )


class PartitioningStrategy:
    """Partitioning strategies for Iceberg tables."""
    
    # Partition admissions by year and month for better performance
    ADMISSIONS_PARTITIONS = [
        "admission_year",
        "admission_month"
    ]
    
    # Partition audit logs by year and month
    AUDIT_PARTITIONS = [
        "audit_year",
        "audit_month"
    ]
    
    @staticmethod
    def get_admission_year_month(timestamp_str: str) -> tuple:
        """
        Extract year and month from admission timestamp.
        
        Args:
            timestamp_str: ISO format timestamp string
            
        Returns:
            Tuple of (year, month)
        """
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp_str)
        return dt.year, dt.month
