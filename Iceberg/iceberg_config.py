"""
PyIceberg Configuration and Utilities

This module provides configuration management for Iceberg table catalog,
storage, and metadata management.
"""

import os
from typing import Dict, Any
from datetime import datetime


class IcebergConfig:
    """Iceberg catalog and storage configuration."""
    
    # Catalog configuration
    CATALOG_NAME = "admission_catalog"
    CATALOG_TYPE = "rest"  # or "hive", "hadoop", "glue"
    
    # Local Iceberg catalog path (for demo/development)
    WAREHOUSE_PATH = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "output",
        "iceberg_catalog"
    )
    
    # Table namespace
    NAMESPACE = "healthcare"
    
    # Table names
    ADMISSIONS_TABLE = "admissions"
    ADMISSIONS_ENRICHED_TABLE = "admissions_enriched"
    ADMISSIONS_AUDIT_TABLE = "admissions_audit"
    SCHEMA_EVOLUTION_TABLE = "schema_evolution_log"
    
    # Metadata configuration
    METADATA_DIR = os.path.join(WAREHOUSE_PATH, "metadata")
    
    # Partitioning strategy
    PARTITION_COLUMNS = ["admission_year", "admission_month"]
    
    # Snapshot retention
    SNAPSHOT_RETENTION_DAYS = 30
    
    @classmethod
    def get_catalog_config(cls) -> Dict[str, Any]:
        """
        Get Iceberg catalog configuration.
        
        Returns:
            Dictionary with catalog configuration
        """
        return {
            "name": cls.CATALOG_NAME,
            "type": "rest",
            "uri": f"file://{cls.WAREHOUSE_PATH}",
            "warehouse": cls.WAREHOUSE_PATH
        }
    
    @classmethod
    def get_table_identifier(cls, table_name: str) -> str:
        """
        Get fully qualified table identifier.
        
        Args:
            table_name: Table name
            
        Returns:
            Fully qualified table name (namespace.table_name)
        """
        return f"{cls.NAMESPACE}.{table_name}"
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist."""
        os.makedirs(cls.WAREHOUSE_PATH, exist_ok=True)
        os.makedirs(cls.METADATA_DIR, exist_ok=True)


class AuditRecord:
    """Schema for audit trail records."""
    
    OPERATION_INSERT = "INSERT"
    OPERATION_UPDATE = "UPDATE"
    OPERATION_DELETE = "DELETE"
    OPERATION_SCHEMA_CHANGE = "SCHEMA_CHANGE"
    OPERATION_SNAPSHOT = "SNAPSHOT"
    
    @staticmethod
    def create_audit_entry(
        operation: str,
        table_name: str,
        user: str = "system",
        record_count: int = 0,
        changes: Dict[str, Any] = None,
        timestamp: datetime = None
    ) -> Dict[str, Any]:
        """
        Create an audit trail entry.
        
        Args:
            operation: Type of operation (INSERT, UPDATE, DELETE, SCHEMA_CHANGE)
            table_name: Target table name
            user: User performing the operation
            record_count: Number of records affected
            changes: Dictionary of changes
            timestamp: Operation timestamp
            
        Returns:
            Audit record dictionary
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        return {
            "audit_id": f"{table_name}_{timestamp.timestamp()}",
            "operation": operation,
            "table_name": table_name,
            "user": user,
            "timestamp": timestamp.isoformat(),
            "record_count": record_count,
            "changes": changes or {},
            "snapshot_id": None  # Will be populated after write
        }
