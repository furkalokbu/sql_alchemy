import random
import asyncio
from faker import Faker
from lesson_2 import User, Order, Product, OrderProduct
from sqlalchemy.orm import Session, sessionmaker, aliased
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import URL, create_engine, select, or_, and_, func, update, delete, bindparam
from environs import Env
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from typing import List


"""
    INSERT INTO users
        (telegram_id, full_name, username, language_code, created_at)
    VALUES (1, 'John Doe', 'johnny', 'en', '2020-01-01');
"""

class Repo:

    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def create_new_order_for_user(self, user_id: int):
        new_order = (
            insert(Order).values(
                user_id=user_id
            ).returning(Order.order_id)
        )
        result =  await self.session.scalar(new_order)
        await self.session.commit()
        return result

    async def add_products_to_order(self, order_id: int, products: List[dict]):
        stmt = (
            insert(OrderProduct).values(
                order_id=order_id,
                product_id=bindparam('product_id'),
                quantity=bindparam('quantity'),
            )
        )
        await self.session.execute(stmt, products)
        await self.session.commit()


if __name__ == '__main__':

    env = Env()
    env.read_env('.env')

    url = URL.create(
        drivername="postgresql+asyncpg",  # driver name = postgresql + the library we are using (psycopg2)
        username=env.str("POSTGRES_USER"),
        password=env.str("POSTGRES_PASSWORD"),
        host=env.str("DB_HOST"),
        database=env.str("POSTGRES_DB"),
        port=5432,
    ).render_as_string(hide_password=False)

    engine = create_async_engine(url, echo=True)
    session_pool = async_sessionmaker(engine)

    async def main():
        async with session_pool() as session:
            repo = Repo(session)

            order_id = await repo.create_new_order_for_user(18)
            await repo.add_products_to_order(order_id, [{"product_id": 1, "quantity": 1}, {"product_id": 2, "quantity": 2}, {"product_id": 3, "quantity": 3}])

    asyncio.run(main())
