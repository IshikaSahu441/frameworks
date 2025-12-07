"""
Iceberg Integration Script

Integrates PyIceberg with the admission processing pipeline,
handling data ingestion, schema evolution, and audit trails.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from Iceberg.iceberg_config import IcebergConfig
from Iceberg.iceberg_ingestor import IcebergIngestor
from Iceberg.schema_evolution import SchemaEvolutionManager
from Iceberg.audit_trail import AuditTrailManager, Operation


class AdmissionIcebergIntegration:
    """Main integration class for Iceberg-based admission system."""
    
    def __init__(self):
        """Initialize Iceberg integration."""
        self.config = IcebergConfig()
        self.ingestor = IcebergIngestor()
        self.schema_manager = SchemaEvolutionManager(self.ingestor)
        self.audit_manager = AuditTrailManager(self.ingestor)
        
        print("\n" + "=" * 80)
        print("ICEBERG INTEGRATION: Patient Admission Processing")
        print("=" * 80)
        print(f"Warehouse: {self.config.WAREHOUSE_PATH}")
        print(f"Namespace: {self.config.NAMESPACE}")
    
    def setup_tables(self, overwrite: bool = False) -> Dict[str, bool]:
        """
        Create all Iceberg tables.
        
        Args:
            overwrite: Whether to overwrite existing tables
            
        Returns:
            Dictionary with creation status for each table
        """
        print("\n[Step 1] Creating Iceberg Tables")
        print("-" * 80)
        
        results = {
            "admissions": self.ingestor.create_admissions_table(overwrite=overwrite),
            "enriched": self.ingestor.create_enriched_table(overwrite=overwrite),
            "audit": self.ingestor.create_audit_table(overwrite=overwrite),
            "schema_evolution": self.ingestor.create_schema_evolution_table(overwrite=overwrite)
        }
        
        success_count = sum(1 for v in results.values() if v)
        print(f"\nCreated {success_count}/{len(results)} tables")
        
        return results
    
    def ingest_data(self, daft_output_path: str = "output/daft_processed") -> Dict[str, Any]:
        """
        Ingest processed Daft data into Iceberg tables.
        
        Args:
            daft_output_path: Path to Daft-processed data
            
        Returns:
            Dictionary with ingestion results
        """
        print("\n[Step 2] Ingesting Daft-Processed Data")
        print("-" * 80)
        
        results = {
            "admissions_full": None,
            "admission_type_stats": None,
            "insurance_stats": None,
            "emergency_analysis": None,
            "admissions_enriched": None
        }
        
        # Ingest main admissions data
        parquet_path = os.path.join(daft_output_path, "admissions_full.parquet")
        if os.path.exists(parquet_path):
            print(f"\nLoading: {parquet_path}")
            result = self.ingestor.load_parquet_file(
                parquet_path,
                self.config.ADMISSIONS_TABLE,
                operation_user="daft_pipeline"
            )
            results["admissions_full"] = result
            
            # Log to audit trail
            if result["success"]:
                self.audit_manager.log_insert(
                    self.config.ADMISSIONS_TABLE,
                    result["records_loaded"],
                    user="daft_pipeline",
                    details={"source": parquet_path}
                )
                print(f"  Loaded {result['records_loaded']} records")
            else:
                print(f"  [ERROR] Failed: {result['errors']}")
        
        # Ingest enriched data
        enriched_path = os.path.join(daft_output_path, "admissions_enriched.parquet")
        if os.path.exists(enriched_path):
            print(f"\nLoading: {enriched_path}")
            result = self.ingestor.load_parquet_file(
                enriched_path,
                self.config.ADMISSIONS_ENRICHED_TABLE,
                operation_user="daft_pipeline"
            )
            results["admissions_enriched"] = result
            
            if result["success"]:
                self.audit_manager.log_insert(
                    self.config.ADMISSIONS_ENRICHED_TABLE,
                    result["records_loaded"],
                    user="daft_pipeline",
                    details={"source": enriched_path},
                    source_tables=[self.config.ADMISSIONS_TABLE]
                )
                print(f"  Loaded {result['records_loaded']} records")
            else:
                print(f"  [ERROR] Failed: {result['errors']}")
        
        return results
    
    def demonstrate_schema_evolution(self) -> Dict[str, Any]:
        """
        Demonstrate schema evolution capabilities.
        
        Returns:
            Dictionary with schema evolution examples
        """
        print("\n[Step 3] Schema Evolution Examples")
        print("-" * 80)
        
        examples = {}
        
        # Example 1: Add new feature column
        print("\nExample 1: Add column for mortality prediction score")
        result = self.schema_manager.add_column(
            table_name=self.config.ADMISSIONS_ENRICHED_TABLE,
            column_name="mortality_prediction_score",
            column_type="double",
            description="ML model prediction score for mortality risk (0-1)",
            applied_by="data_scientist"
        )
        examples["add_mortality_score"] = result
        print(f"  Status: {result.get('status', 'unknown')}")
        
        # Example 2: Add readmission tracking column
        print("\nExample 2: Add column for readmission risk")
        result = self.schema_manager.add_column(
            table_name=self.config.ADMISSIONS_ENRICHED_TABLE,
            column_name="readmission_risk_score",
            column_type="double",
            description="Readmission risk prediction (0-1)",
            applied_by="data_scientist"
        )
        examples["add_readmission_score"] = result
        print(f"  Status: {result.get('status', 'unknown')}")
        
        # Example 3: Type change for compatibility
        print("\nExample 3: Demonstrate type compatibility checking")
        result = self.schema_manager.change_column_type(
            table_name=self.config.ADMISSIONS_ENRICHED_TABLE,
            column_name="length_of_stay_hours",
            old_type="double",
            new_type="string",
            applied_by="data_engineer"
        )
        examples["type_change_warning"] = result
        if result.get("status") == "WARNING":
            print(f"  Warning: {result.get('warning')}")
        
        return examples
    
    def demonstrate_audit_trail(self) -> Dict[str, Any]:
        """
        Demonstrate audit trail capabilities.
        
        Returns:
            Dictionary with audit trail examples
        """
        print("\n[Step 4] Audit Trail Examples")
        print("-" * 80)
        
        examples = {}
        
        # Log various operations
        print("\nLogging sample operations to audit trail...")
        
        # Insert operation
        result = self.audit_manager.log_insert(
            table_name=self.config.ADMISSIONS_TABLE,
            record_count=58976,
            user="data_pipeline",
            details={"batch_id": "batch_001", "source": "MIMIC-III"}
        )
        examples["insert"] = result
        print(f"  Logged INSERT: {result['audit_id']}")
        
        # Schema change operation
        result = self.audit_manager.log_schema_change(
            table_name=self.config.ADMISSIONS_ENRICHED_TABLE,
            change_description="Added mortality prediction feature",
            user="data_scientist",
            change_details={
                "column": "mortality_prediction_score",
                "type": "double",
                "reason": "ML model integration"
            }
        )
        examples["schema_change"] = result
        print(f"  Logged SCHEMA_CHANGE: {result['audit_id']}")
        
        # Snapshot operation
        result = self.audit_manager.log_snapshot(
            table_name=self.config.ADMISSIONS_TABLE,
            user="data_engineer",
            snapshot_metadata={
                "snapshot_name": "baseline_snapshot",
                "description": "Initial data snapshot for ML training"
            }
        )
        examples["snapshot"] = result
        print(f"  Logged SNAPSHOT: {result['audit_id']}")
        
        # Data export operation
        result = self.audit_manager.log_data_export(
            table_name=self.config.ADMISSIONS_ENRICHED_TABLE,
            record_count=50000,
            export_format="parquet",
            destination="s3://ml-training-bucket/admissions/",
            user="data_scientist"
        )
        examples["export"] = result
        print(f"  Logged DATA_EXPORT: {result['audit_id']}")
        
        return examples
    
    def generate_reports(self, output_dir: str = "output/iceberg_reports") -> Dict[str, str]:
        """
        Generate reports for schema evolution and audit trails.
        
        Args:
            output_dir: Output directory for reports
            
        Returns:
            Dictionary with report file paths
        """
        print("\n[Step 5] Generating Reports")
        print("-" * 80)
        
        os.makedirs(output_dir, exist_ok=True)
        reports = {}
        
        # Schema evolution summary
        print("\nGenerating schema evolution report...")
        schema_summary = self.schema_manager.get_summary()
        schema_path = os.path.join(output_dir, "schema_evolution_summary.txt")
        
        with open(schema_path, 'w') as f:
            f.write("SCHEMA EVOLUTION SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total Changes: {schema_summary['total_changes']}\n")
            f.write(f"Tables Modified: {schema_summary['tables_modified']}\n")
            f.write(f"Applied Changes: {schema_summary['applied_changes']}\n")
            f.write(f"Pending Changes: {schema_summary['pending_changes']}\n")
            f.write(f"Failed Changes: {schema_summary['failed_changes']}\n\n")
            
            f.write("Change Types:\n")
            for change_type, count in schema_summary['change_types'].items():
                f.write(f"  {change_type}: {count}\n")
            
            f.write("\nSchema Versions:\n")
            for table, version in schema_summary['schema_versions'].items():
                f.write(f"  {table}: v{version}\n")
        
        reports["schema_evolution"] = schema_path
        print(f"  Generated: {schema_path}")
        
        # Audit trail summary
        print("\nGenerating audit trail report...")
        audit_summary = self.audit_manager.get_summary()
        audit_path = os.path.join(output_dir, "audit_trail_summary.txt")
        
        with open(audit_path, 'w') as f:
            f.write("AUDIT TRAIL SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total Operations: {audit_summary['total_operations']}\n")
            f.write(f"Tables Affected: {audit_summary['tables_affected']}\n")
            f.write(f"Total Records Modified: {audit_summary['total_records_modified']}\n\n")
            
            f.write("Users:\n")
            for user in audit_summary['users']:
                f.write(f"  {user}\n")
            
            f.write("\nOperations by Type:\n")
            for op_type, count in audit_summary['operations_by_type'].items():
                f.write(f"  {op_type}: {count}\n")
        
        reports["audit_trail"] = audit_path
        print(f"  Generated: {audit_path}")
        
        # Export detailed logs
        print("\nExporting detailed logs...")
        evolution_path = os.path.join(output_dir, "schema_evolution_log.json")
        self.schema_manager.export_evolution_log(evolution_path)
        reports["evolution_log"] = evolution_path
        
        audit_log_path = os.path.join(output_dir, "audit_log.json")
        self.audit_manager.export_audit_log(audit_log_path)
        reports["audit_log"] = audit_log_path
        
        return reports
    
    def run_integration(self, daft_output_path: str = "output/daft_processed"):
        """
        Run complete Iceberg integration pipeline.
        
        Args:
            daft_output_path: Path to Daft-processed data
        """
        try:
            # Setup tables
            self.setup_tables(overwrite=False)
            
            # Ingest data
            self.ingest_data(daft_output_path)
            
            # Demonstrate schema evolution
            self.demonstrate_schema_evolution()
            
            # Demonstrate audit trail
            self.demonstrate_audit_trail()
            
            # Generate reports
            self.generate_reports()
            
            print("\n" + "=" * 80)
            print("ICEBERG INTEGRATION COMPLETE")
            print("=" * 80)
            print("\nAll Iceberg tables created and configured")
            print("Data ingestion pipeline established")
            print("Schema evolution tracking enabled")
            print("Comprehensive audit trail in place")
            
        except Exception as e:
            print(f"\n[ERROR] Integration failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    integration = AdmissionIcebergIntegration()
    integration.run_integration()
