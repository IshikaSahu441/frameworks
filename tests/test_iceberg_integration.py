"""
Unit Tests for Iceberg Integration

Tests for schema management, data ingestion, schema evolution,
and audit trail functionality.
"""

import pytest
import os
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from Iceberg.iceberg_config import IcebergConfig, AuditRecord
from Iceberg.iceberg_ingestor import IcebergIngestor
from Iceberg.schema_evolution import SchemaEvolutionManager, ChangeType
from Iceberg.audit_trail import AuditTrailManager, Operation


class TestIcebergConfig:
    """Test Iceberg configuration."""
    
    def test_config_paths(self):
        """Test that configuration creates valid paths."""
        config = IcebergConfig()
        assert config.WAREHOUSE_PATH is not None
        assert config.NAMESPACE == "healthcare"
    
    def test_get_table_identifier(self):
        """Test fully qualified table naming."""
        config = IcebergConfig()
        table_id = config.get_table_identifier("admissions")
        assert table_id == "healthcare.admissions"
    
    def test_get_catalog_config(self):
        """Test catalog configuration dictionary."""
        config = IcebergConfig()
        catalog_config = config.get_catalog_config()
        assert "name" in catalog_config
        assert "warehouse" in catalog_config
        assert catalog_config["name"] == "admission_catalog"
    
    def test_ensure_directories(self):
        """Test directory creation."""
        config = IcebergConfig()
        config.ensure_directories()
        assert os.path.exists(config.WAREHOUSE_PATH)


class TestSchemaEvolutionManager:
    """Test schema evolution capabilities."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.manager = SchemaEvolutionManager()
    
    def test_add_column(self):
        """Test adding a column to schema."""
        result = self.manager.add_column(
            table_name="test_table",
            column_name="new_feature",
            column_type="double",
            description="Test feature"
        )
        
        assert result["change_type"] == ChangeType.ADD_COLUMN.value
        assert result["column_name"] == "new_feature"
        assert result["new_type"] == "double"
        assert result["table_name"] == "test_table"
        assert "evolution_id" in result
    
    def test_rename_column(self):
        """Test renaming a column."""
        result = self.manager.rename_column(
            table_name="test_table",
            old_name="old_col",
            new_name="new_col"
        )
        
        assert result["change_type"] == ChangeType.RENAME_COLUMN.value
        assert result["column_name"] == "old_col"
        assert result["new_column_name"] == "new_col"
    
    def test_change_column_type_compatible(self):
        """Test compatible type change."""
        result = self.manager.change_column_type(
            table_name="test_table",
            column_name="amount",
            old_type="int",
            new_type="long"
        )
        
        assert result["change_type"] == ChangeType.CHANGE_TYPE.value
        assert result["compatible"] == True
        assert result["old_type"] == "int"
        assert result["new_type"] == "long"
    
    def test_change_column_type_incompatible(self):
        """Test incompatible type change warning."""
        result = self.manager.change_column_type(
            table_name="test_table",
            column_name="amount",
            old_type="string",
            new_type="int"
        )
        
        assert result["compatible"] == False
        assert result["status"] == "WARNING"
        assert "warning" in result
    
    def test_schema_versioning(self):
        """Test schema version tracking."""
        self.manager.add_column("table1", "col1", "string")
        self.manager.add_column("table1", "col2", "int")
        self.manager.add_column("table2", "col1", "double")
        
        assert self.manager.get_current_schema_version("table1") == 2
        assert self.manager.get_current_schema_version("table2") == 1
    
    def test_get_evolution_history(self):
        """Test evolution history retrieval."""
        self.manager.add_column("table1", "col1", "string")
        self.manager.add_column("table1", "col2", "int")
        self.manager.add_column("table2", "col1", "double")
        
        history_table1 = self.manager.get_evolution_history("table1")
        assert len(history_table1) == 2
        assert all(e["table_name"] == "table1" for e in history_table1)
        
        history_all = self.manager.get_evolution_history()
        assert len(history_all) == 3
    
    def test_get_summary(self):
        """Test evolution summary."""
        self.manager.add_column("table1", "col1", "string")
        self.manager.rename_column("table1", "col1", "col1_renamed")
        self.manager.change_column_type("table2", "col1", "int", "long")
        
        summary = self.manager.get_summary()
        assert summary["total_changes"] == 3
        assert summary["tables_modified"] == 2
        assert ChangeType.ADD_COLUMN.value in summary["change_types"]
        assert ChangeType.RENAME_COLUMN.value in summary["change_types"]
    
    def test_export_evolution_log(self):
        """Test exporting evolution log to file."""
        self.manager.add_column("table1", "col1", "string")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            result = self.manager.export_evolution_log(temp_path)
            assert result == True
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r') as f:
                data = json.load(f)
                assert len(data) == 1
                assert data[0]["table_name"] == "table1"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestAuditTrailManager:
    """Test audit trail functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.manager = AuditTrailManager()
    
    def test_log_insert(self):
        """Test logging INSERT operation."""
        result = self.manager.log_insert(
            table_name="admissions",
            record_count=100,
            user="test_user"
        )
        
        assert result["operation"] == Operation.INSERT.value
        assert result["table_name"] == "admissions"
        assert result["record_count"] == 100
        assert result["user"] == "test_user"
        assert "audit_id" in result
        assert "timestamp" in result
    
    def test_log_update(self):
        """Test logging UPDATE operation."""
        changes = {"column1": "new_value", "column2": 123}
        result = self.manager.log_update(
            table_name="admissions",
            record_count=50,
            changes=changes,
            user="test_user",
            where_clause="id > 1000"
        )
        
        assert result["operation"] == Operation.UPDATE.value
        assert result["details"]["changes"] == changes
        assert result["details"]["where_clause"] == "id > 1000"
    
    def test_log_schema_change(self):
        """Test logging schema change operation."""
        result = self.manager.log_schema_change(
            table_name="admissions",
            change_description="Added mortality prediction column",
            user="data_scientist"
        )
        
        assert result["operation"] == Operation.SCHEMA_CHANGE.value
        assert "mortality prediction" in result["details"]["change_description"]
    
    def test_log_snapshot(self):
        """Test logging snapshot operation."""
        metadata = {
            "snapshot_id": "snap_001",
            "reason": "Backup before migration"
        }
        result = self.manager.log_snapshot(
            table_name="admissions",
            snapshot_metadata=metadata
        )
        
        assert result["operation"] == Operation.SNAPSHOT.value
        assert result["details"]["snapshot_id"] == "snap_001"
    
    def test_log_data_export(self):
        """Test logging data export operation."""
        result = self.manager.log_data_export(
            table_name="admissions",
            record_count=58976,
            export_format="parquet",
            destination="s3://bucket/admissions/",
            user="analyst"
        )
        
        assert result["operation"] == Operation.DATA_EXPORT.value
        assert result["details"]["export_format"] == "parquet"
        assert result["details"]["destination"] == "s3://bucket/admissions/"
    
    def test_get_table_audit_history(self):
        """Test retrieving audit history for a table."""
        self.manager.log_insert("table1", 100, "user1")
        self.manager.log_update("table1", 50, {}, "user1")
        self.manager.log_insert("table2", 200, "user2")
        
        history = self.manager.get_table_audit_history("table1")
        assert len(history) == 2
        assert all(r["table_name"] == "table1" for r in history)
    
    def test_get_table_audit_history_with_filter(self):
        """Test audit history with operation filter."""
        self.manager.log_insert("table1", 100)
        self.manager.log_insert("table1", 50)
        self.manager.log_update("table1", 25, {})
        
        insert_history = self.manager.get_table_audit_history(
            "table1",
            operation_filter=Operation.INSERT
        )
        assert len(insert_history) == 2
        assert all(r["operation"] == Operation.INSERT.value for r in insert_history)
    
    def test_get_user_operations(self):
        """Test retrieving operations by user."""
        self.manager.log_insert("table1", 100, "alice")
        self.manager.log_insert("table2", 200, "alice")
        self.manager.log_insert("table1", 150, "bob")
        
        alice_ops = self.manager.get_user_operations("alice")
        assert len(alice_ops) == 2
        assert all(r["user"] == "alice" for r in alice_ops)
        
        bob_ops = self.manager.get_user_operations("bob")
        assert len(bob_ops) == 1
    
    def test_get_operations_in_timerange(self):
        """Test retrieving operations within time range."""
        now = datetime.utcnow()
        
        # Create operations at different times
        self.manager.audit_records.append({
            "audit_id": "1",
            "operation": "INSERT",
            "table_name": "table1",
            "timestamp": (now - timedelta(hours=2)).isoformat(),
            "user": "user1",
            "record_count": 0,
            "details": {}
        })
        self.manager.audit_records.append({
            "audit_id": "2",
            "operation": "INSERT",
            "table_name": "table1",
            "timestamp": now.isoformat(),
            "user": "user1",
            "record_count": 0,
            "details": {}
        })
        self.manager.audit_records.append({
            "audit_id": "3",
            "operation": "INSERT",
            "table_name": "table1",
            "timestamp": (now + timedelta(hours=2)).isoformat(),
            "user": "user1",
            "record_count": 0,
            "details": {}
        })
        
        # Query within 1 hour of now
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)
        results = self.manager.get_operations_in_timerange(start, end)
        assert len(results) == 1
        assert results[0]["audit_id"] == "2"
    
    def test_get_data_lineage(self):
        """Test data lineage tracking."""
        self.manager.log_insert("table1", 100, source_tables=["source_table1"])
        self.manager.log_insert("table2", 200, source_tables=["table1"])
        
        lineage = self.manager.get_data_lineage("table2")
        assert lineage["table"] == "table2"
        assert "table1" in lineage["derived_from"]
    
    def test_get_summary(self):
        """Test audit trail summary."""
        self.manager.log_insert("table1", 100, "user1")
        self.manager.log_insert("table1", 50, "user1")
        self.manager.log_update("table1", 25, {}, "user2")
        self.manager.log_schema_change("table1", "test change")
        
        summary = self.manager.get_summary()
        assert summary["total_operations"] == 4
        assert summary["total_records_modified"] == 175
        assert "user1" in summary["users"]
        assert "user2" in summary["users"]
        assert Operation.INSERT.value in summary["operations_by_type"]
    
    def test_export_audit_log_json(self):
        """Test exporting audit log as JSON."""
        self.manager.log_insert("table1", 100)
        self.manager.log_update("table1", 50, {})
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            result = self.manager.export_audit_log(temp_path, format="json")
            assert result == True
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r') as f:
                data = json.load(f)
                assert len(data) == 2
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestAuditRecord:
    """Test audit record creation."""
    
    def test_create_audit_entry(self):
        """Test creating an audit entry."""
        entry = AuditRecord.create_audit_entry(
            operation=AuditRecord.OPERATION_INSERT,
            table_name="admissions",
            user="test_user",
            record_count=100
        )
        
        assert entry["operation"] == "INSERT"
        assert entry["table_name"] == "admissions"
        assert entry["user"] == "test_user"
        assert entry["record_count"] == 100
        assert "audit_id" in entry
        assert "timestamp" in entry
    
    def test_create_audit_entry_with_custom_timestamp(self):
        """Test creating audit entry with custom timestamp."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        entry = AuditRecord.create_audit_entry(
            operation=AuditRecord.OPERATION_DELETE,
            table_name="test_table",
            timestamp=custom_time
        )
        
        assert entry["timestamp"] == custom_time.isoformat()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
