"""initial schema

Revision ID: 001
Revises:
Create Date: 2025-03-01
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('customers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('full_name', sa.String(150), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('phone', sa.String(20)),
        sa.Column('address', sa.Text()),
        sa.Column('city', sa.String(100)),
        sa.Column('country', sa.String(2), default='US'),
        sa.Column('loyalty_points', sa.Integer(), default=0),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('hashed_password', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_customers_email', 'customers', ['email'], unique=True)
    op.create_index('ix_customers_city', 'customers', ['city'])

    op.create_table('products',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('sku', sa.String(100), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('brand', sa.String(100)),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('discount_pct', sa.Numeric(5, 2), default=0),
        sa.Column('stock_qty', sa.Integer(), default=0),
        sa.Column('image_url', sa.Text()),
        sa.Column('rating', sa.Numeric(3, 2), default=0),
        sa.Column('review_count', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_products_sku', 'products', ['sku'], unique=True)
    op.create_index('ix_products_category', 'products', ['category'])
    op.create_index('ix_products_brand', 'products', ['brand'])
    op.create_index('ix_products_is_active', 'products', ['is_active'])

    op.create_table('orders',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('customer_id', sa.String(36), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('order_number', sa.String(30), nullable=False, unique=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('subtotal', sa.Numeric(12, 2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(12, 2), default=0),
        sa.Column('tax_amount', sa.Numeric(12, 2), default=0),
        sa.Column('total_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('payment_method', sa.String(50)),
        sa.Column('shipping_address', sa.Text()),
        sa.Column('tracking_number', sa.String(100)),
        sa.Column('shipped_at', sa.DateTime(timezone=True)),
        sa.Column('delivered_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_orders_customer_id', 'orders', ['customer_id'])
    op.create_index('ix_orders_status', 'orders', ['status'])
    op.create_index('ix_orders_created_at', 'orders', ['created_at'])

    op.create_table('order_items',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('order_id', sa.String(36), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.String(36), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('discount_pct', sa.Numeric(5, 2), default=0),
        sa.Column('line_total', sa.Numeric(12, 2), nullable=False),
    )
    op.create_index('ix_order_items_order_id', 'order_items', ['order_id'])

    op.create_table('conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('customer_id', sa.String(36), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('title', sa.String(255), default='New Conversation'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(50)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('products')
    op.drop_table('customers')
