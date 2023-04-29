import psycopg2
import os
from dotenv import load_dotenv
import yaml
from datetime import datetime, timedelta
import atexit

class DataBaseManager:
    def __init__(self, app_name: str):
        self.app_name = app_name

        # load config
        with open("config.yaml", "r") as config_file:
            config = yaml.safe_load(config_file)

        use_database = config["database"]["use_database"]
        host = config["database"]["host"]
        port = config["database"]["port"]
        dbname = config["database"]["dbname"]
        user = config["database"]["user"]
        self.model_name = config["chat_gpt_model"]

        load_dotenv()
        password = os.environ["DB_PASSWORD"]
        self.api_key = os.environ["OPENAI_API_KEY"]

        assert(use_database)

        # connect to database
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )

        # create cursor
        self.cursor = self.conn.cursor()
        atexit.register(self.close_connection)

    def close_connection(self) -> None:
        self.cursor.close() # type: ignore
        self.conn.close()

    def insert_transaction(self, sent_tokens: float, received_tokens: float) -> None:
        timestamp = datetime.now()
        self.cursor.execute("SELECT id FROM models WHERE name = %s;", (self.model_name,))
        result = self.cursor.fetchone()
        if result is None:
            raise Exception("Model not found")
        model_id = result[0]
        query = f"""
        INSERT INTO transactions (api_key, app_name, model_id, sent_tokens, received_tokens, timestamp)
        VALUES ('{self.api_key}', '{self.app_name}', {model_id}, {sent_tokens}, {received_tokens}, '{timestamp}');
        """
        self.cursor.execute(query)
        self.conn.commit()

    def initialize_tables(self) -> None:
        # create transactions table
        query = """
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            api_key VARCHAR(255) NOT NULL,
            app_name VARCHAR(255) NOT NULL,
            sent_tokens INTEGER NOT NULL,
            received_tokens INTEGER NOT NULL,
            timestamp TIMESTAMP NOT NULL
        );
        """
        self.cursor.execute(query)

        # create token_rates table
        query = """
        CREATE TABLE IF NOT EXISTS token_rates (
            id SERIAL PRIMARY KEY,
            model_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE,
            sent_token_rate NUMERIC(10, 2) NOT NULL,
            received_token_rate NUMERIC(10, 2) NOT NULL
        );
        """
        self.cursor.execute(query)

        # create models table
        query = """
        CREATE TABLE IF NOT EXISTS models (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL
        );
        """
        self.cursor.execute(query)

        # commit
        self.conn.commit()

    def update_token_rate(self, model_name: str, sent_token_rate: float, received_token_rate: float) -> None:
        now = datetime.now()
        yesterday = now - timedelta(days=1)

        self.cursor.execute("SELECT id FROM models WHERE name = %s;", (model_name,))
        result = self.cursor.fetchone()
        if result is None:
            raise Exception("Model not found")
        model_id = result[0]

        # set end_date of the previous record
        self.cursor.execute(
            "UPDATE token_rates SET end_date = %s WHERE model_id = %s AND end_date = '9999-12-31'",
            (yesterday, model_id)
        )

        # insert new record
        self.cursor.execute(
            """
            INSERT INTO token_rates (
                model_id,
                sent_token_rate,
                received_token_rate,
                start_date,
                end_date
            ) VALUES (
                %s,
                %s,
                %s,
                %s,
                '9999-12-31'
            )
            """,
            (model_id, sent_token_rate, received_token_rate, now)
        )

        self.conn.commit()


def main() -> None:
    db = DataBaseManager("test")
    db.initialize_tables()
    db.update_token_rate("gpt-4", 0.03, 0.06)
    db.update_token_rate("gpt-4-32k", 0.06, 0.12)
    db.update_token_rate("gpt-3.5-turbo", 0.002, 0.002)

if __name__ == "__main__":
    main()

