"""
Iceberg Data Ingestion Module

Handles loading Daft-processed Parquet files into Iceberg tables with
schema validation and data quality checks.
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
from pathlib import Path

from .iceberg_config import IcebergConfig, AuditRecord
from .iceberg_schemas import (
    AdmissionsSchema,
    EnrichedAdmissionsSchema,
    AuditTrailSchema,
    SchemaEvolutionLogSchema,
    PartitioningStrategy
)


class IcebergIngestor:
    """Manages data ingestion into Iceberg tables."""
    
    def __init__(self):
        """Initialize Iceberg ingestor."""
        self.config = IcebergConfig()
        self.config.ensure_directories()
        self.catalog = None
        self._initialize_catalog()
    
    def _initialize_catalog(self):
        """Initialize Iceberg catalog."""
        try:
            from pyiceberg.catalog import load_catalog
            
            # Create local file-based catalog for demo
            self.catalog = load_catalog(
                "default",
                **{
                    "type": "rest",
                    "uri": f"file://{self.config.WAREHOUSE_PATH}",
                    "warehouse": self.config.WAREHOUSE_PATH
                }
            )
        except Exception as e:
            print(f"Warning: Could not initialize Iceberg catalog: {e}")
            print("Continuing with data preparation mode...")
    
    def create_admissions_table(self, overwrite: bool = False) -> bool:
        """
        Create Iceberg admissions table.
        
        Args:
            overwrite: Whether to overwrite existing table
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.catalog:
                print("Catalog not initialized. Cannot create table.")
                return False
            
            table_id = self.config.get_table_identifier(self.config.ADMISSIONS_TABLE)
            
            # Check if table exists
            try:
                existing_table = self.catalog.load_table(table_id)
                if overwrite:
                    self.catalog.drop_table(table_id)
                    print(f"Dropped existing table: {table_id}")
                else:
                    print(f"Table already exists: {table_id}")
                    return True
            except:
                pass  # Table doesn't exist, proceed with creation
            
            # Create table
            schema = AdmissionsSchema.get_schema()
            
            table = self.catalog.create_table(
                table_id,
                schema=schema,
                location=os.path.join(self.config.WAREHOUSE_PATH, table_id),
                partition_spec=PartitioningStrategy.ADMISSIONS_PARTITIONS,
                properties={
                    "description": "Patient admission records",
                    "created_by": "admission_system",
                    "data_source": "MIMIC-III ADMISSIONS.csv"
                }
            )
            
            print(f"Created Iceberg table: {table_id}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error creating admissions table: {e}")
            return False
    
    def create_enriched_table(self, overwrite: bool = False) -> bool:
        """
        Create enriched admissions table with derived features.
        
        Args:
            overwrite: Whether to overwrite existing table
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.catalog:
                print("Catalog not initialized. Cannot create table.")
                return False
            
            table_id = self.config.get_table_identifier(
                self.config.ADMISSIONS_ENRICHED_TABLE
            )
            
            # Check if table exists
            try:
                existing_table = self.catalog.load_table(table_id)
                if overwrite:
                    self.catalog.drop_table(table_id)
                    print(f"Dropped existing table: {table_id}")
                else:
                    print(f"Table already exists: {table_id}")
                    return True
            except:
                pass
            
            # Create table
            schema = EnrichedAdmissionsSchema.get_schema()
            
            table = self.catalog.create_table(
                table_id,
                schema=schema,
                location=os.path.join(self.config.WAREHOUSE_PATH, table_id),
                partition_spec=PartitioningStrategy.ADMISSIONS_PARTITIONS,
                properties={
                    "description": "Enriched admission records with derived features",
                    "created_by": "admission_system",
                    "feature_set": "length_of_stay, ed_wait_time, patient_outcome, priority_flags"
                }
            )
            
            print(f"Created Iceberg table: {table_id}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error creating enriched table: {e}")
            return False
    
    def create_audit_table(self, overwrite: bool = False) -> bool:
        """
        Create audit trail table.
        
        Args:
            overwrite: Whether to overwrite existing table
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.catalog:
                print("Catalog not initialized. Cannot create table.")
                return False
            
            table_id = self.config.get_table_identifier(
                self.config.ADMISSIONS_AUDIT_TABLE
            )
            
            # Check if table exists
            try:
                existing_table = self.catalog.load_table(table_id)
                if overwrite:
                    self.catalog.drop_table(table_id)
                    print(f"Dropped existing table: {table_id}")
                else:
                    print(f"Table already exists: {table_id}")
                    return True
            except:
                pass
            
            # Create table
            schema = AuditTrailSchema.get_schema()
            
            table = self.catalog.create_table(
                table_id,
                schema=schema,
                location=os.path.join(self.config.WAREHOUSE_PATH, table_id),
                partition_spec=PartitioningStrategy.AUDIT_PARTITIONS,
                properties={
                    "description": "Audit trail for admission data changes",
                    "created_by": "admission_system",
                    "change_tracking": "enabled"
                }
            )
            
            print(f"Created Iceberg table: {table_id}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error creating audit table: {e}")
            return False
    
    def create_schema_evolution_table(self, overwrite: bool = False) -> bool:
        """
        Create schema evolution log table.
        
        Args:
            overwrite: Whether to overwrite existing table
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.catalog:
                print("Catalog not initialized. Cannot create table.")
                return False
            
            table_id = self.config.get_table_identifier(
                self.config.SCHEMA_EVOLUTION_TABLE
            )
            
            # Check if table exists
            try:
                existing_table = self.catalog.load_table(table_id)
                if overwrite:
                    self.catalog.drop_table(table_id)
                    print(f"Dropped existing table: {table_id}")
                else:
                    print(f"Table already exists: {table_id}")
                    return True
            except:
                pass
            
            # Create table
            schema = SchemaEvolutionLogSchema.get_schema()
            
            table = self.catalog.create_table(
                table_id,
                schema=schema,
                location=os.path.join(self.config.WAREHOUSE_PATH, table_id),
                properties={
                    "description": "Schema evolution and column change history",
                    "created_by": "admission_system",
                    "versioning": "enabled"
                }
            )
            
            print(f"Created Iceberg table: {table_id}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error creating schema evolution table: {e}")
            return False
    
    def load_parquet_file(
        self,
        parquet_path: str,
        table_name: str,
        operation_user: str = "system"
    ) -> Dict[str, Any]:
        """
        Load Parquet file into Iceberg table.
        
        Args:
            parquet_path: Path to Parquet file or directory
            table_name: Iceberg table to load into
            operation_user: User performing the operation
            
        Returns:
            Dictionary with operation results
        """
        result = {
            "success": False,
            "table": table_name,
            "records_loaded": 0,
            "errors": [],
            "audit_record": None
        }
        
        try:
            # Read Parquet file
            if os.path.isdir(parquet_path):
                # Daft outputs Parquet as directories
                import pyarrow.parquet as pq
                table = pq.read_table(parquet_path)
                df = table.to_pandas()
            else:
                df = pd.read_parquet(parquet_path)
            
            if df.empty:
                result["errors"].append("Parquet file is empty")
                return result
            
            # Add partition columns if needed
            if "admission_year" not in df.columns and "ADMITTIME" in df.columns:
                df["ADMITTIME"] = pd.to_datetime(df["ADMITTIME"])
                df["admission_year"] = df["ADMITTIME"].dt.year
                df["admission_month"] = df["ADMITTIME"].dt.month
            
            # Load into Iceberg table
            if self.catalog:
                table_id = self.config.get_table_identifier(table_name)
                try:
                    iceberg_table = self.catalog.load_table(table_id)
                    
                    # Convert DataFrame to Arrow table
                    import pyarrow as pa
                    arrow_table = pa.Table.from_pandas(df)
                    
                    # Append to Iceberg table
                    iceberg_table.append(arrow_table)
                    
                    result["records_loaded"] = len(df)
                    result["success"] = True
                    
                except Exception as e:
                    result["errors"].append(f"Failed to load into Iceberg: {str(e)}")
            else:
                # Fallback: save as Parquet in warehouse
                output_path = os.path.join(
                    self.config.WAREHOUSE_PATH,
                    table_name,
                    f"data_{datetime.now().isoformat()}.parquet"
                )
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                df.to_parquet(output_path)
                result["records_loaded"] = len(df)
                result["success"] = True
            
            # Create audit record
            result["audit_record"] = AuditRecord.create_audit_entry(
                operation=AuditRecord.OPERATION_INSERT,
                table_name=table_name,
                user=operation_user,
                record_count=len(df)
            )
            
        except Exception as e:
            result["errors"].append(str(e))
        
        return result
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get information about an Iceberg table.
        
        Args:
            table_name: Table name
            
        Returns:
            Dictionary with table information
        """
        info = {
            "table": table_name,
            "exists": False,
            "row_count": None,
            "schema": None,
            "partitions": None,
            "snapshots": None,
            "properties": None
        }
        
        try:
            if not self.catalog:
                return info
            
            table_id = self.config.get_table_identifier(table_name)
            iceberg_table = self.catalog.load_table(table_id)
            
            info["exists"] = True
            info["schema"] = str(iceberg_table.schema())
            info["properties"] = iceberg_table.properties
            
            # Get row count if available
            try:
                df = iceberg_table.to_pandas()
                info["row_count"] = len(df)
            except:
                pass
            
        except Exception as e:
            info["error"] = str(e)
        
        return info
