import argparse


from langchain.messages import HumanMessage


from src.finance_agent.orchestrator import GraphState, orchestrator
from src.finance_agent.setup import Setup


# TODO: Implement Debug logger


# USER_PROMPT = "Please load my data from the file data.csv"
# USER_PROMPT = "How much did I spend on transport last month?"
USER_PROMPT = "I need your help with something"

if __name__ == "__main__":
    ## PARSE USER ARGS
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

    ## RUN APP SETUP
    setup = Setup(data_dir)

    if setup.is_first_run():
        setup.run_setup()
    else:
        setup.run_migrations()

    ## RUN ORCHESTRATOR
    user_input = HumanMessage(content=USER_PROMPT)

    result = orchestrator.invoke(
        GraphState(user_input=user_input, messages=[user_input])
    )

    for m in result["messages"]:
        m.pretty_print()

    print("\n\n================================================")
    print("Press ENTER to exit the application.")
    input()
