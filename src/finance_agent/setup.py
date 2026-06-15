import os
import duckdb

# TODO: Implement Migration Support


class Setup:
    def __init__(self, app_dir: str):
        self.app_dir = app_dir
        self.db_path = os.path.join(app_dir, "finance-agent.duckdb")

    def is_first_run(self) -> bool:
        return not os.path.exists(self.db_path)

    def run_setup(self):
        print("Welcome! Setting up your personal finance agent...")
        self._create_database()
        self.run_migrations()
        self._collect_user_preferences()
        print("Setup complete.")

    def run_migrations(self):
        pass

    def _create_database(self):
        with duckdb.connect(self.db_path) as conn:
            create_accounts_table = """
            CREATE TABLE IF NOT EXISTS Accounts (
                account_id INTEGER PRIMARY KEY,
                name VARCHAR(20) NOT NULL,
                type VARCHAR(50) NOT NULL,
            );
            """

            create_transactions_table = """
            CREATE TABLE IF NOT EXISTS Transactions (
                transaction_id INTEGER PRIMARY KEY,
                account_id INTEGER NOT NULL,
                date DATE NOT NULL,
                amount DECIMAL(15, 2) NOT NULL,
                type VARCHAR(50),
                description VARCHAR(255),
                is_outgoing BOOLEAN NOT NULL,
                FOREIGN KEY (account_id) REFERENCES Accounts (account_id)
            );
            """

            create_balance_table = """
            CREATE TABLE IF NOT EXISTS Balances (
                balance_id INTEGER PRIMARY KEY,
                account_id INTEGER NOT NULL,
                date DATE NOT NULL,
                amount DECIMAL(15, 2) NOT NULL,
                FOREIGN KEY (account_id) REFERENCES Accounts (account_id)
            );
            """

            conn.execute(create_accounts_table)
            conn.execute(create_transactions_table)
            conn.execute(create_balance_table)
            print("✅ Database schema initialized successfully.")

    def _collect_user_preferences(self):
        pass
