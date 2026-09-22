"""Add pipeline execution tracking

Revision ID: 007
Revises: 006
Create Date: 2024-01-20 10:00:00.000000

Purpose:
- Track pipeline execution state for each project
- Enable checkpoint resume and progress monitoring
- Store stage results for debugging and recovery
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '007_pipeline_tracking'
down_revision = '54ce86695f64'  # 基于fix_document_chunks_schema之后
branch_labels = None
depends_on = None


def upgrade():
    """Create pipeline_executions table for state persistence"""

    # Pipeline executions table - tracks overall pipeline run
    op.execute("""
        CREATE TABLE pipeline_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            execution_id VARCHAR(50) NOT NULL UNIQUE,
            mode VARCHAR(50) NOT NULL,
            current_stage VARCHAR(50),
            status VARCHAR(50) NOT NULL DEFAULT 'running',
            progress_percentage FLOAT DEFAULT 0.0,
            total_stages INTEGER,
            completed_stages INTEGER DEFAULT 0,
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            total_duration_seconds FLOAT,
            error_message TEXT,
            metadata JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

    # Pipeline stage results table - tracks individual stage execution
    op.execute("""
        CREATE TABLE pipeline_stage_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id VARCHAR(50) NOT NULL,
            stage VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            success BOOLEAN,
            duration_seconds FLOAT,
            output JSON,
            errors JSON,
            warnings JSON,
            retry_count INTEGER DEFAULT 0,
            start_time DATETIME,
            end_time DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            FOREIGN KEY (execution_id) REFERENCES pipeline_executions(execution_id) ON DELETE CASCADE,
            UNIQUE(execution_id, stage)
        )
    """)

    # Indexes for performance
    op.execute("CREATE INDEX idx_pipeline_exec_project ON pipeline_executions(project_id)")
    op.execute("CREATE INDEX idx_pipeline_exec_status ON pipeline_executions(status)")
    op.execute("CREATE INDEX idx_pipeline_stage_exec ON pipeline_stage_results(execution_id)")
    op.execute("CREATE INDEX idx_pipeline_stage_status ON pipeline_stage_results(status)")

    print("✅ Pipeline execution tracking tables created")


def downgrade():
    """Drop pipeline execution tracking tables"""
    op.execute("DROP TABLE IF EXISTS pipeline_stage_results")
    op.execute("DROP TABLE IF EXISTS pipeline_executions")
    print("✅ Pipeline execution tracking tables dropped")
