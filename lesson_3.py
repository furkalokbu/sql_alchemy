import random
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

    def __init__(self, session: Session):
        self.session: Session = session

    def add_user(
        self,
        telegram_id: int,
        full_name: str,
        user_name: str,
        language_code: str = None,
        referrer_id: int = None,
    ) -> User:
        stmt = select(User).from_statement(
            insert(User).values(
                telegram_id=telegram_id,
                full_name=full_name,
                user_name=user_name,
                language_code=language_code,
                referrer_id=referrer_id,
            ).returning(
                User
            ).on_conflict_do_update(
                index_elements=[User.telegram_id],
                set_=dict(
                    user_name=user_name,
                    full_name=full_name,
                )
            )
        )

        result = self.session.scalars(stmt).first()
        self.session.commit()
        return result

    def add_order(self, user_id: int) -> Order:
        stmt = select(Order).from_statement(
            insert(Order).values(user_id=user_id).returning(Order)
        )
        result = self.session.scalars(stmt)
        self.session.commit()
        return result.first()
    
    def add_product(self, title: str, description: str, price: int) -> Product:
        stmt = select(Product).from_statement(
            insert(Product).values(
                title=title,
                description=description,
                price=price
            ).returning(Product)
        )
        result = self.session.scalars(stmt)
        self.session.commit()
        return result.first()

    def add_product_to_order(self, order_id: int, product_id: int, quantity: int) -> OrderProduct:
        stmt = insert(OrderProduct).values(
                order_id=order_id,
                product_id=product_id,
                quantity=quantity,
        )
        self.session.execute(stmt)
        self.session.commit()

    def get_user_by_id(self, telegram_id: int) -> User:
        stmt = select(User).where(User.telegram_id==telegram_id)
        result = self.session.execute(stmt)
        return result.scalars().first()

    def get_all_users(self):
        stmt = select(
            User
        ).where(
            and_(
                # or_(User.language_code=='en', User.language_code=='uk'),
                # User.user_name.ilike("%john%"),
            )
        ).order_by(
            User.created_at.asc()
        ).limit(
            10
        )
        result = self.session.execute(stmt)
        return result.scalars().all()

    def get_user_language(self, telegram_id):
        stmt = select(User.language_code).where(User.telegram_id==telegram_id)
        result = self.session.execute(stmt)
        return result.scalar()

    def select_all_invited_users(self):
        ParentUser = aliased(User)
        ReferralUser = aliased(User)
        stmt = select(
            ParentUser.full_name.label('parent_name'),
            ReferralUser.full_name.label('referral_name')
        ).outerjoin(
            ReferralUser, ReferralUser.referrer_id==ParentUser.telegram_id
        ).where(
            ParentUser.referrer_id.isnot(None)
        )

        result = self.session.execute(stmt)
        return result.all()

    def get_all_user_orders(self, telegram_id):
        stmt = (select(Product ,Order, User, OrderProduct.quantity)
            .join(User.orders)
            .join(Order.products)
            .join(Product)
            .where(User.telegram_id==telegram_id))
        result = self.session.execute(stmt)
        return result.all()

    def get_total_number_of_orders(self):
        stmt = (
            select(func.count(Order.order_id), User.full_name)
            .join(User)
            .group_by(User.telegram_id)
        )
        result = self.session.execute(stmt)
        return result.all()

    def get_total_number_of_products(self):
        stmt = (
            select(func.sum(OrderProduct.quantity).label('quantity'), User.full_name)
            .join(Order, Order.order_id == OrderProduct.order_id)
            .join(User)
            .group_by(User.telegram_id)
            .having(func.sum(OrderProduct.quantity)<6000)
        )
        result = self.session.execute(stmt)
        return result.all()

    def set_new_referrer_id(self, user_id: int, referrer_id: int):
        stmt = (
            update(User)
            .where(User.telegram_id==user_id)
            .values(referrer_id=referrer_id)
        )

        self.session.execute(stmt)
        self.session.commit()

    def delete_user_by_id(self, user_id: int):
        stmt = (
            delete(User)
            .where(User.telegram_id==user_id)
        )
        self.session.execute(stmt)
        self.session.commit()

    def create_new_order_for_user(self, user_id: int):
        new_order = (
            insert(Order).values(
                user_id=user_id
            ).returning(Order.order_id)
        )
        result = self.session.scalar(new_order)
        self.session.commit()
        return result

    def add_products_to_order(self, order_id: int, products: List[dict]):
        stmt = (
            insert(OrderProduct).values(
                order_id=order_id,
                product_id=bindparam('product_id'),
                quantity=bindparam('quantity'),
            )
        )
        self.session.execute(stmt, products)
        self.session.commit()


def seed_fake_data(repo: Repo):
    Faker.seed(0)
    fake = Faker()
    users = []
    orders = []
    products = []
    for _ in range(10):
        refferer_id = None if not users else users[-1].telegram_id
        user = repo.add_user(
            telegram_id=fake.pyint(),
            full_name=fake.name(),
            language_code=fake.language_code(),
            user_name=fake.user_name(),
            referrer_id=refferer_id,
        )
        users.append(user)
        
    for _ in range(10):
        order = repo.add_order(
            user_id=random.choice(users).telegram_id,
        )
        orders.append(order)

    for _ in range(10):
        product = repo.add_product(
            title=fake.word(),
            description=fake.sentence(),
            price=fake.pyint(),
        )
        products.append(product)

    for order in orders:
        for _ in range(3):
            repo.add_product_to_order(
                order_id=order.order_id,
                product_id=random.choice(products).product_id,
                quantity=fake.pyint(),
            )

if __name__ == '__main__':

    env = Env()
    env.read_env('.env')

    url = URL.create(
        drivername="postgresql",  # driver name = postgresql + the library we are using (psycopg2)
        username=env.str("POSTGRES_USER"),
        password=env.str("POSTGRES_PASSWORD"),
        host=env.str("DB_HOST"),
        database=env.str("POSTGRES_DB"),
        port=5432,
    ).render_as_string(hide_password=False)

    engine = create_engine(url, echo=True)
    session_pool = sessionmaker(engine)

    with session_pool() as session:
        repo = Repo(session)

        # user = repo.get_user_by_id(1)
        # users = repo.get_all_users()
        # lang_code = repo.get_user_language(1)
        # repo.add_user(
        #     telegram_id=2,
        #     user_name='johnny',
        #     full_name='John Doe',
        #     language_code='en',
        # )
        # seed_fake_data(repo)

        # for row in repo.select_all_invited_users():
        #     print(f'Parent: {row.parent_name} Referral: {row.referral_name}')
        # for user in repo.get_all_users():
        #     print(f'User: {user.user_name}, ({user.telegram_id})')
        #     for order in user.orders:
        #         print(f'Order: {order.order_id}')
        #         for product in order.products:
        #             print(f'Product: {product.product.title}')

        # for product, order, user, quantity in repo.get_all_user_orders(telegram_id=3909):
        #     print(f'# {product.title} - {order.order_id} - {user.full_name} - {quantity}')

        # for num, name in repo.get_total_number_of_products():
        #     print(f'Total: {num} for {name}')
        order_id = repo.create_new_order_for_user(18)
        repo.add_products_to_order(order_id, [{"product_id": 1, "quantity": 1}, {"product_id": 2, "quantity": 2}, {"product_id": 3, "quantity": 3}])
