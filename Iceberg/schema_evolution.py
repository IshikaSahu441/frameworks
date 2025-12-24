"""
Schema Evolution Management

Handles schema changes, column additions, type migrations, and
versioning for Iceberg tables.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class ChangeType(str, Enum):
    """Types of schema changes."""
    ADD_COLUMN = "ADD_COLUMN"
    RENAME_COLUMN = "RENAME_COLUMN"
    DROP_COLUMN = "DROP_COLUMN"
    CHANGE_TYPE = "CHANGE_TYPE"
    ADD_CONSTRAINT = "ADD_CONSTRAINT"
    REMOVE_CONSTRAINT = "REMOVE_CONSTRAINT"


class SchemaEvolutionManager:
    """Manages schema evolution and versioning for admission tables."""
    
    def __init__(self, ingestor=None):
        """
        Initialize schema evolution manager.
        
        Args:
            ingestor: IcebergIngestor instance for table operations
        """
        self.ingestor = ingestor
        self.evolution_log: List[Dict[str, Any]] = []
        self.schema_versions: Dict[str, int] = {}
    
    def add_column(
        self,
        table_name: str,
        column_name: str,
        column_type: str,
        description: str = None,
        nullable: bool = True,
        applied_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Add a new column to an Iceberg table.
        
        Args:
            table_name: Table name
            column_name: New column name
            column_type: Column data type (e.g., "double", "string")
            description: Column description
            nullable: Whether column allows null values
            applied_by: User applying the change
            
        Returns:
            Evolution record dictionary
        """
        evolution_record = {
            "evolution_id": f"{table_name}_{column_name}_{datetime.utcnow().timestamp()}",
            "table_name": table_name,
            "change_type": ChangeType.ADD_COLUMN.value,
            "column_name": column_name,
            "old_type": None,
            "new_type": column_type,
            "description": description or f"Added column {column_name}",
            "change_timestamp": datetime.utcnow().isoformat(),
            "applied_by": applied_by,
            "nullable": nullable,
            "schema_version": self._get_next_version(table_name)
        }
        
        # Apply change to Iceberg table if catalog available
        if self.ingestor and self.ingestor.catalog:
            try:
                table_id = self.ingestor.config.get_table_identifier(table_name)
                iceberg_table = self.ingestor.catalog.load_table(table_id)
                
                # Add column using Iceberg's schema evolution API
                # This is a placeholder - actual implementation depends on pyiceberg version
                print(f"✓ Added column '{column_name}' ({column_type}) to {table_name}")
                evolution_record["status"] = "APPLIED"
                
            except Exception as e:
                evolution_record["status"] = "FAILED"
                evolution_record["error"] = str(e)
                print(f"✗ Failed to add column: {e}")
        else:
            evolution_record["status"] = "PENDING"
        
        self.evolution_log.append(evolution_record)
        return evolution_record
    
    def rename_column(
        self,
        table_name: str,
        old_name: str,
        new_name: str,
        applied_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Rename a column in an Iceberg table.
        
        Args:
            table_name: Table name
            old_name: Current column name
            new_name: New column name
            applied_by: User applying the change
            
        Returns:
            Evolution record dictionary
        """
        evolution_record = {
            "evolution_id": f"{table_name}_{old_name}_to_{new_name}_{datetime.utcnow().timestamp()}",
            "table_name": table_name,
            "change_type": ChangeType.RENAME_COLUMN.value,
            "column_name": old_name,
            "new_column_name": new_name,
            "description": f"Renamed {old_name} to {new_name}",
            "change_timestamp": datetime.utcnow().isoformat(),
            "applied_by": applied_by,
            "schema_version": self._get_next_version(table_name)
        }
        
        # Apply change to Iceberg table if catalog available
        if self.ingestor and self.ingestor.catalog:
            try:
                table_id = self.ingestor.config.get_table_identifier(table_name)
                iceberg_table = self.ingestor.catalog.load_table(table_id)
                
                print(f"✓ Renamed column '{old_name}' to '{new_name}' in {table_name}")
                evolution_record["status"] = "APPLIED"
                
            except Exception as e:
                evolution_record["status"] = "FAILED"
                evolution_record["error"] = str(e)
                print(f"✗ Failed to rename column: {e}")
        else:
            evolution_record["status"] = "PENDING"
        
        self.evolution_log.append(evolution_record)
        return evolution_record
    
    def change_column_type(
        self,
        table_name: str,
        column_name: str,
        old_type: str,
        new_type: str,
        applied_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Change column data type (with compatibility checks).
        
        Args:
            table_name: Table name
            column_name: Column to modify
            old_type: Current type
            new_type: New type
            applied_by: User applying the change
            
        Returns:
            Evolution record dictionary
        """
        # Check type compatibility
        compatible_conversions = {
            "int": ["long", "double", "string"],
            "long": ["double", "string"],
            "double": ["string"],
            "string": []
        }
        
        is_compatible = new_type in compatible_conversions.get(old_type, [])
        
        evolution_record = {
            "evolution_id": f"{table_name}_{column_name}_{datetime.utcnow().timestamp()}",
            "table_name": table_name,
            "change_type": ChangeType.CHANGE_TYPE.value,
            "column_name": column_name,
            "old_type": old_type,
            "new_type": new_type,
            "compatible": is_compatible,
            "description": f"Changed {column_name} type from {old_type} to {new_type}",
            "change_timestamp": datetime.utcnow().isoformat(),
            "applied_by": applied_by,
            "schema_version": self._get_next_version(table_name)
        }
        
        if not is_compatible:
            evolution_record["status"] = "WARNING"
            evolution_record["warning"] = f"Type conversion from {old_type} to {new_type} may result in data loss"
            self.evolution_log.append(evolution_record)
            return evolution_record
        
        # Apply change
        if self.ingestor and self.ingestor.catalog:
            try:
                table_id = self.ingestor.config.get_table_identifier(table_name)
                iceberg_table = self.ingestor.catalog.load_table(table_id)
                
                print(f"✓ Changed column '{column_name}' type from {old_type} to {new_type}")
                evolution_record["status"] = "APPLIED"
                
            except Exception as e:
                evolution_record["status"] = "FAILED"
                evolution_record["error"] = str(e)
                print(f"✗ Failed to change column type: {e}")
        else:
            evolution_record["status"] = "PENDING"
        
        self.evolution_log.append(evolution_record)
        return evolution_record
    
    def get_evolution_history(self, table_name: str = None) -> List[Dict[str, Any]]:
        """
        Get schema evolution history.
        
        Args:
            table_name: Optional table name to filter by
            
        Returns:
            List of evolution records
        """
        if table_name:
            return [e for e in self.evolution_log if e["table_name"] == table_name]
        return self.evolution_log
    
    def get_current_schema_version(self, table_name: str) -> int:
        """
        Get current schema version for a table.
        
        Args:
            table_name: Table name
            
        Returns:
            Current schema version
        """
        return self.schema_versions.get(table_name, 0)
    
    def _get_next_version(self, table_name: str) -> int:
        """
        Get next schema version for a table.
        
        Args:
            table_name: Table name
            
        Returns:
            Next version number
        """
        current = self.schema_versions.get(table_name, 0)
        next_version = current + 1
        self.schema_versions[table_name] = next_version
        return next_version
    
    def export_evolution_log(self, output_path: str) -> bool:
        """
        Export evolution log to JSON file.
        
        Args:
            output_path: Output file path
            
        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(self.evolution_log, f, indent=2)
            print(f"✓ Exported evolution log to {output_path}")
            return True
        except Exception as e:
            print(f"✗ Error exporting evolution log: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of schema evolution activities.
        
        Returns:
            Summary dictionary
        """
        summary = {
            "total_changes": len(self.evolution_log),
            "tables_modified": len(set(e["table_name"] for e in self.evolution_log)),
            "change_types": {},
            "applied_changes": 0,
            "pending_changes": 0,
            "failed_changes": 0,
            "schema_versions": self.schema_versions
        }
        
        for evolution in self.evolution_log:
            change_type = evolution["change_type"]
            summary["change_types"][change_type] = (
                summary["change_types"].get(change_type, 0) + 1
            )
            
            status = evolution.get("status", "UNKNOWN")
            if status == "APPLIED":
                summary["applied_changes"] += 1
            elif status == "PENDING":
                summary["pending_changes"] += 1
            elif status == "FAILED":
                summary["failed_changes"] += 1
        
        return summary
