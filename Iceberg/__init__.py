"""
PyIceberg Integration Module

Comprehensive Iceberg table management, schema evolution, and audit trail
functionality for the Intelligent Real-Time Patient Flow Optimization System.
"""

from .iceberg_config import IcebergConfig, AuditRecord
from .iceberg_ingestor import IcebergIngestor
from .schema_evolution import SchemaEvolutionManager, ChangeType
from .audit_trail import AuditTrailManager, Operation

__version__ = "1.0.0"
__all__ = [
    "IcebergConfig",
    "AuditRecord",
    "IcebergIngestor",
    "SchemaEvolutionManager",
    "ChangeType",
    "AuditTrailManager",
    "Operation"
]
