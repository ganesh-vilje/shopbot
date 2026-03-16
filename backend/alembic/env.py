from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context
import os, sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Load environment variables from .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from app.db.base import Base
from app.models.customer import Customer
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.conversation import Conversation, Message

config = context.config
db_url = os.environ.get("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        url = os.environ.get("DATABASE_URL")
    
    connectable = create_engine(url, poolclass=pool.NullPool)
    
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
