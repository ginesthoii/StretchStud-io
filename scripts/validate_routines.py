import json
import os
import sys
from jsonschema import validate, ValidationError

# JSON schema for routines
routine_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "pose": {"type": "string"},
                    "duration": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["pose", "duration", "description"]
            }
        },
        "tags": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["name", "steps", "tags"]
}

def validate_file(filepath):
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        validate(instance=data, schema=routine_schema)
        print(f"✔ {filepath} is valid")
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"✗ {filepath} is invalid: {e}")

if __name__ == "__main__":
    routines_dir = "routines"
    if not os.path.exists(routines_dir):
        print("No routines directory found.")
        sys.exit(1)

    for file in os.listdir(routines_dir):
        if file.endswith(".json"):
            validate_file(os.path.join(routines_dir, file))
