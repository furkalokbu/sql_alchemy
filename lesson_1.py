from sqlalchemy import create_engine, URL, text
from sqlalchemy.orm import sessionmaker


url = URL.create(
    drivername="postgresql+psycopg2",  # driver name = postgresql + the library we are using (psycopg2)
    username='',
    password='',
    host='localhost',
    database='testuser',
    port=5432,
)

engine = create_engine(url, echo=True)
session_pool = sessionmaker(engine)

# session = session_pool()
# session.execute()
# session.commit()
# session.close()

with session_pool() as session:
    query_1 = text("""
        CREATE TABLE IF NOT EXISTS users
            (
                telegram_id   BIGINT PRIMARY KEY,
                full_name     VARCHAR(255) NOT NULL,
                username      VARCHAR(255),
                language_code VARCHAR(255) NOT NULL,
                created_at    TIMESTAMP DEFAULT NOW(),
                referrer_id   BIGINT,
                FOREIGN KEY (referrer_id)
                    REFERENCES users (telegram_id)
                    ON DELETE SET NULL
            );
                """)

    query_2 = (text("""
        INSERT INTO users
            (telegram_id, full_name, username, language_code, created_at)
        VALUES (1, 'John Doe', 'johnny', 'en', '2020-01-01');

        INSERT INTO users
            (telegram_id, full_name, username, language_code, created_at, referrer_id)
        VALUES (2, 'Jane Doe', 'jane', 'en', '2020-01-02', 1)       
    """))
    
    results = session.execute(text("""
        SELECT full_name FROM users WHERE telegram_id= :telegram_id;
    """).params(telegram_id=1))

print(results.all())

# for row in results:
#     print(row)
