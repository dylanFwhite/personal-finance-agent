import argparse
import os

def run_application(data_directory):
    """Main application logic that requires the data directory."""
    print("===============================================")
    print("✅ Application running successfully!")
    print(f"📚 Reading configuration and data from: {data_directory}")
    # Add the rest of your application logic here...
    print("===============================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the main application.")
    # Define the argument expected from the shell script
    parser.add_argument(
        "--data-dir", 
        type=str, 
        required=True, 
        help="The absolute path to the persistent data directory."
    )
    
    args = parser.parse_args()
    
    run_application(args.data_dir)
