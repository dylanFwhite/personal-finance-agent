import os


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
        pass

    def _collect_user_preferences(self):
        pass
