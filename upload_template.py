import argparse
import json
import yaml
import requests

def load_dsl_file(file_path: str) -> str:
    if file_path.endswith(".json"):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.dumps(json.load(f))
    elif file_path.endswith((".yml", ".yaml")):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.dumps(yaml.safe_load(f))
    else:
        raise ValueError("Unsupported file type. Use .json or .yml")

def upload_template(name: str, dsl_str: str, endpoint: str):
    payload = {
        "name": name,
        "dsl": dsl_str
    }
    response = requests.post(endpoint, json=payload)
    if response.status_code == 200:
        print("✅ Template uploaded successfully.")
        print(response.json())
    else:
        print(f"❌ Failed to upload. Status: {response.status_code}")
        print(response.text)

def main():
    parser = argparse.ArgumentParser(description="Upload workflow DSL template.")
    parser.add_argument("file", help="Path to the DSL file (.json or .yml)")
    parser.add_argument("--name", required=True, help="Template name to upload")
    parser.add_argument("--url", default="http://127.0.0.1:3000/v1/templates", help="API endpoint")

    args = parser.parse_args()

    try:
        dsl_str = load_dsl_file(args.file)
        upload_template(args.name, dsl_str, args.url)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()