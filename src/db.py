import logging

import oracledb

import config


def connect() -> oracledb.Connection:
    try:
        connection = oracledb.connect(
            user=config.username, password=config.password, dsn=config.dsn
        )
        logging.info("Successfully connected to the Oracle database.")
        return connection
    except oracledb.Error as e:
        logging.error(f"Failed to connect to the database: {e}")
        raise
