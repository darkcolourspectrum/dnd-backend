"""new field is_gm in SessionPlayer model

Revision ID: 8ab18e688736
Revises: b6ea85affe4b
Create Date: 2025-04-23 01:48:54.403612

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ab18e688736'
down_revision: Union[str, None] = 'b6ea85affe4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('session_players', sa.Column('is_gm', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('session_players', 'is_gm')
    # ### end Alembic commands ###
