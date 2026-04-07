from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.customer import Customer    
from app.models.conversation import Conversation, Message
from app.models.refresh_session import RefreshSession
from app.db.base import Base
from app.db.session import engine


def create_tables(engine):
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables(engine)
    print("✅ Database tables created successfully!")
