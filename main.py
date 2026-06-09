import argparse

from src.finance_agent.setup import Setup


# TODO: Implement Debug logger

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the main application.")

    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="The absolute path to the persistent data directory.",
    )

    args = parser.parse_args()
    data_dir = args.data_dir

    print(f"📚 Reading configuration and data from: {data_dir}")

    setup = Setup(data_dir)

    if setup.is_first_run():
        setup.run_setup()
    else:
        setup.run_migrations()

    # run_agent()

    print("\n\n================================================")
    print("Press ENTER to exit the application.")
    input()
