"""chracter table

Revision ID: 34cff2f8179d
Revises: 23688b006e2a
Create Date: 2025-04-23 00:44:41.931317

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '34cff2f8179d'
down_revision: Union[str, None] = '23688b006e2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
