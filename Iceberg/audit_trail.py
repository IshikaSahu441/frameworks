"""
Audit Trail and Data Lineage Tracking

Comprehensive audit logging for tracking all data modifications,
user actions, and data lineage across the admission system.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class Operation(str, Enum):
    """Types of database operations."""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    READ = "READ"
    SCHEMA_CHANGE = "SCHEMA_CHANGE"
    SNAPSHOT = "SNAPSHOT"
    DATA_EXPORT = "DATA_EXPORT"


class AuditTrailManager:
    """Manages comprehensive audit trails for admission data operations."""
    
    def __init__(self, ingestor=None):
        """
        Initialize audit trail manager.
        
        Args:
            ingestor: IcebergIngestor instance for table operations
        """
        self.ingestor = ingestor
        self.audit_records: List[Dict[str, Any]] = []
        self.lineage_graph: Dict[str, List[str]] = {}
    
    def log_operation(
        self,
        operation: Operation,
        table_name: str,
        user: str = "system",
        record_count: int = 0,
        details: Dict[str, Any] = None,
        affected_records: List[str] = None,
        source_tables: List[str] = None
    ) -> Dict[str, Any]:
        """
        Log a data operation to audit trail.
        
        Args:
            operation: Type of operation
            table_name: Target table
            user: User performing operation
            record_count: Number of affected records
            details: Additional operation details
            affected_records: List of affected record IDs
            source_tables: Tables this operation reads from (for lineage)
            
        Returns:
            Audit record dictionary
        """
        audit_record = {
            "audit_id": f"{table_name}_{operation.value}_{datetime.utcnow().timestamp()}",
            "operation": operation.value,
            "table_name": table_name,
            "user": user,
            "timestamp": datetime.utcnow().isoformat(),
            "record_count": record_count,
            "details": details or {},
            "affected_records_count": len(affected_records) if affected_records else 0,
            "source_tables": source_tables or [],
            "status": "LOGGED"
        }
        
        # Track lineage
        if source_tables:
            for source in source_tables:
                if source not in self.lineage_graph:
                    self.lineage_graph[source] = []
                self.lineage_graph[source].append(table_name)
            
            if table_name not in self.lineage_graph:
                self.lineage_graph[table_name] = []
        
        # Try to persist to Iceberg audit table
        if self.ingestor and self.ingestor.catalog:
            try:
                self._write_to_audit_table(audit_record)
                audit_record["status"] = "PERSISTED"
            except Exception as e:
                audit_record["status"] = "LOGGED_ONLY"
                audit_record["persistence_error"] = str(e)
        
        self.audit_records.append(audit_record)
        return audit_record
    
    def log_insert(
        self,
        table_name: str,
        record_count: int,
        user: str = "system",
        details: Dict[str, Any] = None,
        source_tables: List[str] = None
    ) -> Dict[str, Any]:
        """
        Log an INSERT operation.
        
        Args:
            table_name: Target table
            record_count: Number of records inserted
            user: User performing operation
            details: Additional details
            source_tables: Source tables for lineage
            
        Returns:
            Audit record
        """
        return self.log_operation(
            Operation.INSERT,
            table_name,
            user=user,
            record_count=record_count,
            details={**(details or {}), "operation_type": "bulk_insert"},
            source_tables=source_tables
        )
    
    def log_update(
        self,
        table_name: str,
        record_count: int,
        changes: Dict[str, Any],
        user: str = "system",
        where_clause: str = None
    ) -> Dict[str, Any]:
        """
        Log an UPDATE operation.
        
        Args:
            table_name: Target table
            record_count: Number of records updated
            changes: Dictionary of changes made
            user: User performing operation
            where_clause: UPDATE WHERE clause for reference
            
        Returns:
            Audit record
        """
        return self.log_operation(
            Operation.UPDATE,
            table_name,
            user=user,
            record_count=record_count,
            details={
                "changes": changes,
                "where_clause": where_clause
            }
        )
    
    def log_schema_change(
        self,
        table_name: str,
        change_description: str,
        user: str = "system",
        change_details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Log a schema change operation.
        
        Args:
            table_name: Target table
            change_description: Description of schema change
            user: User performing operation
            change_details: Detailed change information
            
        Returns:
            Audit record
        """
        return self.log_operation(
            Operation.SCHEMA_CHANGE,
            table_name,
            user=user,
            details={
                "change_description": change_description,
                **(change_details or {})
            }
        )
    
    def log_snapshot(
        self,
        table_name: str,
        user: str = "system",
        snapshot_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Log a table snapshot operation.
        
        Args:
            table_name: Table snapshotted
            user: User performing operation
            snapshot_metadata: Snapshot metadata
            
        Returns:
            Audit record
        """
        return self.log_operation(
            Operation.SNAPSHOT,
            table_name,
            user=user,
            details=snapshot_metadata or {}
        )
    
    def log_data_export(
        self,
        table_name: str,
        record_count: int,
        export_format: str,
        destination: str,
        user: str = "system"
    ) -> Dict[str, Any]:
        """
        Log a data export operation.
        
        Args:
            table_name: Source table
            record_count: Number of records exported
            export_format: Export format (parquet, csv, etc.)
            destination: Export destination
            user: User performing operation
            
        Returns:
            Audit record
        """
        return self.log_operation(
            Operation.DATA_EXPORT,
            table_name,
            user=user,
            record_count=record_count,
            details={
                "export_format": export_format,
                "destination": destination
            }
        )
    
    def get_table_audit_history(
        self,
        table_name: str,
        operation_filter: Optional[Operation] = None
    ) -> List[Dict[str, Any]]:
        """
        Get audit history for a specific table.
        
        Args:
            table_name: Table name
            operation_filter: Optional operation type filter
            
        Returns:
            List of audit records
        """
        records = [r for r in self.audit_records if r["table_name"] == table_name]
        
        if operation_filter:
            records = [r for r in records if r["operation"] == operation_filter.value]
        
        return sorted(records, key=lambda r: r["timestamp"], reverse=True)
    
    def get_user_operations(
        self,
        user: str,
        operation_filter: Optional[Operation] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all operations performed by a specific user.
        
        Args:
            user: Username
            operation_filter: Optional operation type filter
            
        Returns:
            List of audit records
        """
        records = [r for r in self.audit_records if r["user"] == user]
        
        if operation_filter:
            records = [r for r in records if r["operation"] == operation_filter.value]
        
        return sorted(records, key=lambda r: r["timestamp"], reverse=True)
    
    def get_operations_in_timerange(
        self,
        start_time: datetime,
        end_time: datetime,
        table_name: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get operations within a time range.
        
        Args:
            start_time: Start time
            end_time: End time
            table_name: Optional table filter
            
        Returns:
            List of audit records
        """
        records = []
        for r in self.audit_records:
            timestamp = datetime.fromisoformat(r["timestamp"])
            if start_time <= timestamp <= end_time:
                if table_name is None or r["table_name"] == table_name:
                    records.append(r)
        
        return sorted(records, key=lambda r: r["timestamp"])
    
    def get_data_lineage(self, table_name: str) -> Dict[str, Any]:
        """
        Get data lineage for a table.
        
        Args:
            table_name: Table name
            
        Returns:
            Lineage information
        """
        return {
            "table": table_name,
            "derived_from": self._get_ancestors(table_name),
            "feeds_into": self.lineage_graph.get(table_name, []),
            "lineage_graph": self.lineage_graph
        }
    
    def _get_ancestors(self, table_name: str, visited=None) -> List[str]:
        """
        Get ancestor tables in lineage.
        
        Args:
            table_name: Starting table
            visited: Set of visited tables to avoid cycles
            
        Returns:
            List of ancestor tables
        """
        if visited is None:
            visited = set()
        
        ancestors = []
        for table, descendants in self.lineage_graph.items():
            if table_name in descendants and table not in visited:
                visited.add(table)
                ancestors.append(table)
                ancestors.extend(self._get_ancestors(table, visited))
        
        return ancestors
    
    def _write_to_audit_table(self, audit_record: Dict[str, Any]) -> bool:
        """
        Persist audit record to Iceberg audit table.
        
        Args:
            audit_record: Audit record to persist
            
        Returns:
            True if successful
        """
        try:
            from pyiceberg.types import Schema, NestedField, StringType, LongType, TimestampType
            
            # This is a placeholder for actual implementation
            # In production, this would write to the Iceberg audit table
            return True
        except Exception as e:
            raise Exception(f"Failed to write audit record: {e}")
    
    def export_audit_log(self, output_path: str, format: str = "json") -> bool:
        """
        Export audit log to file.
        
        Args:
            output_path: Output file path
            format: Export format (json, csv)
            
        Returns:
            True if successful
        """
        try:
            if format == "json":
                with open(output_path, 'w') as f:
                    json.dump(self.audit_records, f, indent=2)
            elif format == "csv":
                import csv
                if not self.audit_records:
                    return True
                
                keys = self.audit_records[0].keys()
                with open(output_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(self.audit_records)
            
            print(f"✓ Exported audit log to {output_path}")
            return True
        except Exception as e:
            print(f"✗ Error exporting audit log: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get audit trail summary.
        
        Returns:
            Summary dictionary
        """
        summary = {
            "total_operations": len(self.audit_records),
            "tables_affected": len(set(r["table_name"] for r in self.audit_records)),
            "users": list(set(r["user"] for r in self.audit_records)),
            "operations_by_type": {},
            "total_records_modified": 0
        }
        
        for record in self.audit_records:
            op = record["operation"]
            summary["operations_by_type"][op] = (
                summary["operations_by_type"].get(op, 0) + 1
            )
            summary["total_records_modified"] += record.get("record_count", 0)
        
        return summary
