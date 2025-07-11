"""Remove unique constraint from startup_set_code

Revision ID: 4d6dab09833b
Revises: 6ae70b9a1061
Create Date: 2025-07-11 16:07:42.826436

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d6dab09833b'
down_revision = '6ae70b9a1061'
branch_labels = None
depends_on = None


def upgrade():
    # Rename the existing table
    op.rename_table('startup_set_assignment', 'startup_set_assignment_old')

    # Create a new table without UNIQUE constraint
    op.create_table(
        'startup_set_assignment',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('participant_id', sa.String(100), nullable=True),
        sa.Column('startup_set_code', sa.String(10), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('used', sa.Boolean(), nullable=True),
        sa.Column('date_created', sa.DateTime(), nullable=True)
    )

    # Copy data
    op.execute("""
        INSERT INTO startup_set_assignment (id, participant_id, startup_set_code, assigned_at, duration_seconds, used, date_created)
        SELECT id, participant_id, startup_set_code, assigned_at, duration_seconds, used, date_created
        FROM startup_set_assignment_old
    """)

    # Drop the old table
    op.drop_table('startup_set_assignment_old')


def downgrade():
    pass
