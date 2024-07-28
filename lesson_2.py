from typing import List
from sqlalchemy import create_engine, URL, func, ForeignKey, DECIMAL
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import BIGINT, VARCHAR, TIMESTAMP, INTEGER
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
from typing import Optional
from typing_extensions import Annotated


class Base(DeclarativeBase):
    pass


class TimestampMixin:

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(),
    )


int_pk = Annotated[
    int,
    mapped_column(
        INTEGER,
        primary_key=True,
        autoincrement=True,
    )
]

user_fk = Annotated[
    int,
    mapped_column(
        ForeignKey(
            "users.telegram_id",
            ondelete="SET NULL"
        )
    )
]

str255 = Annotated[str, mapped_column(VARCHAR(255))]


class TableNameMixin:

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower() + 's'


class User(Base, TimestampMixin, TableNameMixin):

    telegram_id: Mapped[int] = mapped_column(
        BIGINT, primary_key=True,
    )
    full_name: Mapped[str255]
    user_name: Mapped[Optional[str255]]
    language_code: Mapped[str] = mapped_column(VARCHAR(10))
    referrer_id: Mapped[Optional[user_fk]]

    orders: Mapped[List['Order']] = relationship(back_populates="user")


class Order(Base, TimestampMixin, TableNameMixin):
    order_id: Mapped[int_pk]
    user_id: Mapped[user_fk]

    products: Mapped[List["OrderProduct"]] = relationship()
    user: Mapped["User"] = relationship(back_populates="orders")


class Product(Base, TimestampMixin, TableNameMixin):
    product_id: Mapped[int_pk]
    title: Mapped[str255]
    description: Mapped[Optional[str]] = mapped_column(VARCHAR(3000))
    price: Mapped[float] = mapped_column(DECIMAL(precision=16, scale=4))


class OrderProduct(Base, TimestampMixin, TableNameMixin):
    order_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("orders.order_id", ondelete="CASCADE"), primary_key=True, autoincrement=True)

    product_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("products.product_id", ondelete="RESTRICT"), primary_key=True)

    quantity: Mapped[int]

    product: Mapped["Product"] = relationship()


url = URL.create(
    drivername="postgresql+psycopg2",  # driver name = postgresql + the library we are using (psycopg2)
    username='testuser',
    password='testpassword',
    host='localhost',
    database='testuser',
    port=5432,
)

engine = create_engine(url, echo=True)
