import logging

import oracledb
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

import config

pool = oracledb.create_pool(
    user=config.username,
    password=config.password,
    host=config.host,
    port=config.port,
    service_name=config.service_name,
    min=1,
    max=4,
    increment=1,
)

engine = create_engine("oracle+oracledb://", creator=pool.acquire, poolclass=NullPool)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def connect():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# def connect() -> oracledb.Connection:
#     try:
#         connection = oracledb.connect(
#             user=config.username, password=config.password, dsn=config.dsn
#         )
#         logging.info("Successfully connected to the Oracle database.")
#         return connection
#     except oracledb.Error as e:
#         logging.error(f"Failed to connect to the database: {e}")
#         raise
