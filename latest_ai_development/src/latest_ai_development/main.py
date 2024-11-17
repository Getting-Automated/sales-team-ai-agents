# main.py

#!/usr/bin/env python
import sys
import warnings
import argparse
import json
import yaml
import pandas as pd
from crew import YourProjectCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the crew.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run the CrewAI project.')
    parser.add_argument('--lead_csv', type=str, required=True, help='Path to the lead CSV file.')
    parser.add_argument('--config', type=str, required=True, help='Path to the configuration file (JSON or YAML).')
    args = parser.parse_args()

    # Load the lead list from the CSV file
    try:
        lead_df = pd.read_csv(args.lead_csv)
    except Exception as e:
        print(f"Error reading lead CSV file: {e}")
        sys.exit(1)

    # Convert the DataFrame to a list of dictionaries
    lead_list = lead_df.to_dict('records')

    # Load the configuration file
    try:
        if args.config.endswith('.json'):
            with open(args.config, 'r') as f:
                config = json.load(f)
        elif args.config.endswith(('.yml', '.yaml')):
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f)
        else:
            print("Configuration file must be in JSON or YAML format.")
            sys.exit(1)
    except Exception as e:
        print(f"Error reading configuration file: {e}")
        sys.exit(1)

    # Combine inputs
    inputs = {
        'lead_list': lead_list,
        **config  # Merge other configurations into inputs
    }

    crew_instance = YourProjectCrew()
    crew = crew_instance.crew()
    crew_output = crew.kickoff(inputs=inputs)

    # Optionally, print or process the crew output
    print("Crew execution completed.")
    print(f"Raw Output: {crew_output.raw}")
    if crew_output.json_dict:
        print(f"JSON Output: {json.dumps(crew_output.json_dict, indent=2)}")
    if crew_output.pydantic:
        print(f"Pydantic Output: {crew_output.pydantic}")
    print(f"Tasks Output: {crew_output.tasks_output}")
    print(f"Token Usage: {crew_output.token_usage}")

# The rest of the code (train, replay, test functions) remains the same.

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Please specify a command: run, train, replay, or test")
    else:
        command = args[0].lower()
        sys.argv = sys.argv[1:]  # Adjust sys.argv to remove the command
        if command == 'run':
            run()
        elif command == 'train':
            train()
        elif command == 'replay':
            replay()
        elif command == 'test':
            test()
        else:
            print("Invalid command. Use 'run', 'train', 'replay', or 'test'.")
