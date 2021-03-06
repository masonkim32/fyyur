"""empty message

Revision ID: 7e399606911a
Revises: 434fb844e887
Create Date: 2020-02-04 21:34:20.916787

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e399606911a'
down_revision = '434fb844e887'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('shows_artist_id_fkey', 'shows', type_='foreignkey')
    op.drop_constraint('shows_venue_id_fkey', 'shows', type_='foreignkey')
    op.create_foreign_key(None, 'shows', 'venues', ['venue_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'shows', 'artists', ['artist_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'shows', type_='foreignkey')
    op.drop_constraint(None, 'shows', type_='foreignkey')
    op.create_foreign_key('shows_venue_id_fkey', 'shows', 'venues', ['venue_id'], ['id'])
    op.create_foreign_key('shows_artist_id_fkey', 'shows', 'artists', ['artist_id'], ['id'])
    # ### end Alembic commands ###
