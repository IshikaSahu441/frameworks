"""
PyIceberg Integration Example

Demonstrates practical usage of Iceberg for patient admission data.
"""

from admission_iceberg_integration import AdmissionIcebergIntegration
from Iceberg.audit_trail import Operation
from datetime import datetime, timedelta


def example_basic_integration():
    """Example 1: Basic integration setup."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Iceberg Integration")
    print("=" * 80)
    
    integration = AdmissionIcebergIntegration()
    
    # Setup and ingest data
    integration.setup_tables(overwrite=False)
    integration.ingest_data("output/daft_processed")
    
    print("\n✓ Integration complete. Tables created and data loaded.")


def example_schema_evolution():
    """Example 2: Schema evolution."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Schema Evolution")
    print("=" * 80)
    
    from Iceberg import IcebergIngestor, SchemaEvolutionManager
    
    ingestor = IcebergIngestor()
    schema_mgr = SchemaEvolutionManager(ingestor)
    
    # Scenario: Adding new ML prediction features
    print("\nScenario: Evolving schema to add ML features...")
    
    ml_features = [
        ("readmission_risk_score", "double", "30-day readmission prediction"),
        ("mortality_risk_score", "double", "In-hospital mortality prediction"),
        ("los_prediction_days", "double", "Predicted length of stay"),
        ("quality_of_life_impact", "double", "Post-discharge QoL impact score"),
    ]
    
    for col_name, col_type, description in ml_features:
        result = schema_mgr.add_column(
            table_name="admissions_enriched",
            column_name=col_name,
            column_type=col_type,
            description=description,
            applied_by="ml_pipeline"
        )
        print(f"  ✓ Added {col_name}: {result.get('status', 'UNKNOWN')}")
    
    # Get evolution summary
    summary = schema_mgr.get_summary()
    print(f"\nSchema Evolution Summary:")
    print(f"  Total changes: {summary['total_changes']}")
    print(f"  Applied: {summary['applied_changes']}")
    print(f"  Pending: {summary['pending_changes']}")


def example_audit_trail():
    """Example 3: Audit trail operations."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Audit Trail Operations")
    print("=" * 80)
    
    from Iceberg import IcebergIngestor, AuditTrailManager
    
    ingestor = IcebergIngestor()
    audit_mgr = AuditTrailManager(ingestor)
    
    # Log a data correction
    print("\nScenario: Data quality correction workflow...")
    
    audit_mgr.log_update(
        table_name="admissions",
        record_count=245,
        changes={
            "hospital_expire_flag": "corrected from duplicate records",
            "discharge_location": "standardized to valid codes"
        },
        user="data_quality_team",
        where_clause="quality_score < 0.5"
    )
    print("  ✓ Logged data correction")
    
    # Log schema migration
    audit_mgr.log_schema_change(
        table_name="admissions",
        change_description="Migrated admission_type to categorical format",
        user="data_engineer",
        change_details={
            "old_format": "string",
            "new_format": "enum",
            "mapping": "EMERGENCY->1, URGENT->2, ELECTIVE->3, NEWBORN->4"
        }
    )
    print("  ✓ Logged schema change")
    
    # Create backup snapshot
    audit_mgr.log_snapshot(
        table_name="admissions",
        user="backup_system",
        snapshot_metadata={
            "snapshot_name": "pre_migration_backup",
            "reason": "Data migration checkpoint"
        }
    )
    print("  ✓ Logged snapshot")
    
    # Get audit history
    history = audit_mgr.get_table_audit_history("admissions")
    print(f"\nAudit History for 'admissions':")
    print(f"  Total operations: {len(history)}")
    for record in history[:3]:
        print(f"  - {record['operation']} by {record['user']} at {record['timestamp']}")


def example_data_lineage():
    """Example 4: Data lineage tracking."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Data Lineage Tracking")
    print("=" * 80)
    
    from Iceberg import IcebergIngestor, AuditTrailManager
    
    ingestor = IcebergIngestor()
    audit_mgr = AuditTrailManager(ingestor)
    
    # Log data flow through pipeline
    print("\nTracking data flow:")
    
    # Source: CSV
    audit_mgr.log_insert(
        "admissions",
        record_count=58976,
        user="etl_pipeline",
        source_tables=["MIMIC_III.ADMISSIONS_CSV"]
    )
    print("  1. Loaded from MIMIC-III CSV")
    
    # Daft processing
    audit_mgr.log_insert(
        "admissions_enriched",
        record_count=58976,
        user="daft_pipeline",
        source_tables=["admissions"]
    )
    print("  2. Processed with Daft (enriched)")
    
    # Get lineage
    lineage = audit_mgr.get_data_lineage("admissions_enriched")
    print(f"\nData Lineage for 'admissions_enriched':")
    print(f"  Derived from: {lineage['derived_from']}")
    print(f"  Feeds into: {lineage['feeds_into']}")


def example_temporal_queries():
    """Example 5: Time-based queries."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Temporal Queries")
    print("=" * 80)
    
    from Iceberg import IcebergIngestor, AuditTrailManager
    
    ingestor = IcebergIngestor()
    audit_mgr = AuditTrailManager(ingestor)
    
    # Query operations in last 7 days
    print("\nQuerying audit trail for last 7 days...")
    
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    
    recent_ops = audit_mgr.get_operations_in_timerange(week_ago, now)
    print(f"  Operations in last 7 days: {len(recent_ops)}")
    
    # Get operations by user
    print("\nOperations by user:")
    for user in ["daft_pipeline", "data_scientist", "system"]:
        user_ops = audit_mgr.get_user_operations(user)
        if user_ops:
            print(f"  {user}: {len(user_ops)} operations")


def example_multi_user_scenario():
    """Example 6: Multi-user data governance."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Multi-User Data Governance")
    print("=" * 80)
    
    from Iceberg import IcebergIngestor, SchemaEvolutionManager, AuditTrailManager
    
    ingestor = IcebergIngestor()
    schema_mgr = SchemaEvolutionManager(ingestor)
    audit_mgr = AuditTrailManager(ingestor)
    
    # Simulate multi-user workflow
    print("\nScenario: Multi-user data governance...")
    
    # Data engineer ingests data
    audit_mgr.log_insert(
        "admissions",
        record_count=1000,
        user="alice_engineer",
        details={"batch": "daily_load_2024_12_06"}
    )
    print("  1. Alice (Engineer) ingests data")
    
    # Data scientist evolves schema
    schema_mgr.add_column(
        "admissions_enriched",
        "clinical_risk_score",
        "double",
        "Clinical decision support score",
        applied_by="bob_scientist"
    )
    audit_mgr.log_schema_change(
        "admissions_enriched",
        "Added clinical risk score for CDSS",
        user="bob_scientist"
    )
    print("  2. Bob (Data Scientist) adds feature column")
    
    # Data quality team validates
    audit_mgr.log_update(
        "admissions",
        record_count=25,
        changes={"validation_status": "approved"},
        user="charlie_qa"
    )
    print("  3. Charlie (QA) validates quality")
    
    # Get summary
    summary = audit_mgr.get_summary()
    print(f"\nData Governance Summary:")
    print(f"  Total operations: {summary['total_operations']}")
    print(f"  Users involved: {', '.join(summary['users'])}")
    print(f"  Total records modified: {summary['total_records_modified']}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("PyIceberg Integration Examples")
    print("Intelligent Real-Time Patient Flow Optimization System")
    print("=" * 80)
    
    try:
        # Example 1: Basic integration
        example_basic_integration()
        
        # Example 2: Schema evolution
        example_schema_evolution()
        
        # Example 3: Audit trail
        example_audit_trail()
        
        # Example 4: Data lineage
        example_data_lineage()
        
        # Example 5: Temporal queries
        example_temporal_queries()
        
        # Example 6: Multi-user scenario
        example_multi_user_scenario()
        
        print("\n" + "=" * 80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
