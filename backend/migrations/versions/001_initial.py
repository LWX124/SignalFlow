"""Initial migration

Revision ID: 001
Revises:
Create Date: 2025-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums
    op.execute("CREATE TYPE user_role AS ENUM ('user', 'admin', 'operator')")
    op.execute("CREATE TYPE user_tier AS ENUM ('free', 'pro', 'enterprise')")
    op.execute("CREATE TYPE subscription_status AS ENUM ('active', 'paused', 'expired', 'cancelled')")
    op.execute("CREATE TYPE signal_side AS ENUM ('buy', 'sell', 'opportunity', 'observe', 'warning')")
    op.execute("CREATE TYPE delivery_status AS ENUM ('pending', 'sent', 'failed', 'cancelled')")
    op.execute("CREATE TYPE delivery_channel AS ENUM ('site', 'email', 'wechat', 'app')")
    op.execute("CREATE TYPE notification_type AS ENUM ('signal', 'system', 'announcement')")
    op.execute("CREATE TYPE strategy_type AS ENUM ('arbitrage', 'technical', 'fundamental', 'ai')")
    op.execute("CREATE TYPE market AS ENUM ('SH', 'SZ', 'HK', 'US')")
    op.execute("CREATE TYPE instrument_type AS ENUM ('stock', 'etf', 'qdii', 'bond')")
    op.execute("CREATE TYPE risk_level AS ENUM ('low', 'medium', 'high')")

    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('nickname', sa.String(100)),
        sa.Column('avatar_url', sa.String(500)),
        sa.Column('phone', sa.String(20)),
        sa.Column('role', postgresql.ENUM('user', 'admin', 'operator', name='user_role', create_type=False), default='user'),
        sa.Column('tier', postgresql.ENUM('free', 'pro', 'enterprise', name='user_tier', create_type=False), default='free'),
        sa.Column('tier_expires_at', sa.DateTime(timezone=True)),
        sa.Column('preferences', postgresql.JSONB, default={}),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_tier', 'users', ['tier'])

    # Instruments table
    op.create_table(
        'instruments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('market', postgresql.ENUM('SH', 'SZ', 'HK', 'US', name='market', create_type=False), nullable=False),
        sa.Column('type', postgresql.ENUM('stock', 'etf', 'qdii', 'bond', name='instrument_type', create_type=False), nullable=False),
        sa.Column('exchange', sa.String(20)),
        sa.Column('currency', sa.String(10), default='CNY'),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_instruments_symbol', 'instruments', ['symbol'])
    op.create_index('idx_instruments_market_type', 'instruments', ['market', 'type'])

    # Strategies table
    op.create_table(
        'strategies',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('type', postgresql.ENUM('arbitrage', 'technical', 'fundamental', 'ai', name='strategy_type', create_type=False), nullable=False),
        sa.Column('markets', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('risk_level', postgresql.ENUM('low', 'medium', 'high', name='risk_level', create_type=False)),
        sa.Column('frequency_hint', sa.String(20)),
        sa.Column('params_schema', postgresql.JSONB, nullable=False),
        sa.Column('default_params', postgresql.JSONB, default={}),
        sa.Column('default_cooldown', sa.Integer, default=3600),
        sa.Column('metrics_summary', postgresql.JSONB, default={}),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_public', sa.Boolean, default=True),
        sa.Column('tier_required', postgresql.ENUM('free', 'pro', 'enterprise', name='user_tier', create_type=False), default='free'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_strategies_type', 'strategies', ['type'])
    op.create_index('idx_strategies_active', 'strategies', ['is_active'])

    # Subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('strategy_id', sa.String(50), sa.ForeignKey('strategies.id'), nullable=False),
        sa.Column('params', postgresql.JSONB, default={}),
        sa.Column('channels', postgresql.ARRAY(sa.String), default=['site']),
        sa.Column('cooldown_seconds', sa.Integer, default=3600),
        sa.Column('status', postgresql.ENUM('active', 'paused', 'expired', 'cancelled', name='subscription_status', create_type=False), default='active'),
        sa.Column('last_signal_at', sa.DateTime(timezone=True)),
        sa.Column('signal_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'strategy_id'),
    )
    op.create_index('idx_subscriptions_user', 'subscriptions', ['user_id'])
    op.create_index('idx_subscriptions_strategy', 'subscriptions', ['strategy_id'])
    op.create_index('idx_subscriptions_status', 'subscriptions', ['status'])

    # Signals table
    op.create_table(
        'signals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('strategy_id', sa.String(50), sa.ForeignKey('strategies.id'), nullable=False),
        sa.Column('strategy_version', sa.String(20), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('market', postgresql.ENUM('SH', 'SZ', 'HK', 'US', name='market', create_type=False), nullable=False),
        sa.Column('side', postgresql.ENUM('buy', 'sell', 'opportunity', 'observe', 'warning', name='signal_side', create_type=False), nullable=False),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False),
        sa.Column('reason_points', postgresql.JSONB, nullable=False),
        sa.Column('risk_tags', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('snapshot', postgresql.JSONB, nullable=False),
        sa.Column('dedup_key', sa.String(200)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_signals_strategy', 'signals', ['strategy_id'])
    op.create_index('idx_signals_symbol', 'signals', ['symbol'])
    op.create_index('idx_signals_created', 'signals', ['created_at'])
    op.create_index('idx_signals_dedup', 'signals', ['dedup_key', 'created_at'])

    # Signal explains table
    op.create_table(
        'signal_explains',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('signal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('signals.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('model', sa.String(50)),
        sa.Column('prompt_version', sa.String(20)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Delivery plans table
    op.create_table(
        'delivery_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('signal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('signals.id'), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('channel', postgresql.ENUM('site', 'email', 'wechat', 'app', name='delivery_channel', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'sent', 'failed', 'cancelled', name='delivery_status', create_type=False), default='pending'),
        sa.Column('payload', postgresql.JSONB, nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True)),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('error_message', sa.Text),
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_delivery_status', 'delivery_plans', ['status'])
    op.create_index('idx_delivery_user', 'delivery_plans', ['user_id'])
    op.create_index('idx_delivery_scheduled', 'delivery_plans', ['scheduled_at'])

    # Notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', postgresql.ENUM('signal', 'system', 'announcement', name='notification_type', create_type=False), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text),
        sa.Column('link', sa.String(500)),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('is_read', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_notifications_user', 'notifications', ['user_id', 'is_read', 'created_at'])

    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('entity_type', sa.String(50)),
        sa.Column('entity_id', sa.String(100)),
        sa.Column('old_value', postgresql.JSONB),
        sa.Column('new_value', postgresql.JSONB),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text),
        sa.Column('request_id', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_audit_user', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_time', 'audit_logs', ['created_at'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('notifications')
    op.drop_table('delivery_plans')
    op.drop_table('signal_explains')
    op.drop_table('signals')
    op.drop_table('subscriptions')
    op.drop_table('strategies')
    op.drop_table('instruments')
    op.drop_table('users')

    op.execute("DROP TYPE risk_level")
    op.execute("DROP TYPE instrument_type")
    op.execute("DROP TYPE market")
    op.execute("DROP TYPE strategy_type")
    op.execute("DROP TYPE notification_type")
    op.execute("DROP TYPE delivery_channel")
    op.execute("DROP TYPE delivery_status")
    op.execute("DROP TYPE signal_side")
    op.execute("DROP TYPE subscription_status")
    op.execute("DROP TYPE user_tier")
    op.execute("DROP TYPE user_role")
