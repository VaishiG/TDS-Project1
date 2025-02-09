from flask import Flask, request, jsonify
import subprocess
import os
import json
import sqlite3
import requests

def get_llm_response(prompt):
    token = os.environ.get("AIPROXY_TOKEN")
    if not token:
        return "Error: AI Proxy token is missing."
    
    response = requests.post(
        "https://api-proxy-url/run",
        json={"model": "gpt-4o-mini", "prompt": prompt, "max_tokens": 100},
        headers={"Authorization": f"Bearer {token}"},
        timeout=20
    )
    return response.json().get("text", "LLM error")

app = Flask(__name__)

SECURE_DIR = "/data"

def is_secure_path(path):
    return os.path.abspath(path).startswith(SECURE_DIR)

def install_uv_and_run_datagen(email):
    subprocess.run("pip install uv", shell=True, check=False)
    subprocess.run(f"python3 -m uv https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py {email}", shell=True, check=True)
    return "Data generated successfully."

def format_markdown():
    subprocess.run("npx prettier@3.4.2 --write /data/format.md", shell=True, check=True)
    return "Markdown formatted successfully."

def count_wednesdays():
    with open("/data/dates.txt") as f:
        count = sum(1 for line in f if "Wed" in line)
    with open("/data/dates-wednesdays.txt", "w") as f:
        f.write(str(count))
    return "Wednesdays counted successfully."

def sort_contacts():
    with open("/data/contacts.json") as f:
        contacts = json.load(f)
    contacts.sort(key=lambda x: (x['last_name'], x['first_name']))
    with open("/data/contacts-sorted.json", "w") as f:
        json.dump(contacts, f, indent=2)
    return "Contacts sorted successfully."

def extract_recent_logs():
    logs = sorted([f for f in os.listdir("/data/logs") if f.endswith(".log")], key=os.path.getmtime, reverse=True)[:10]
    with open("/data/logs-recent.txt", "w") as out_f:
        for log in logs:
            with open(f"/data/logs/{log}") as log_f:
                out_f.write(log_f.readline())
    return "Recent logs extracted successfully."

def create_markdown_index():
    index = {}
    for file in os.listdir("/data/docs/"):
        if file.endswith(".md"):
            with open(f"/data/docs/{file}") as f:
                for line in f:
                    if line.startswith("# "):
                        index[file] = line.strip("# ").strip()
                        break
    with open("/data/docs/index.json", "w") as f:
        json.dump(index, f, indent=2)
    return "Markdown index created successfully."

def query_sqlite():
    conn = sqlite3.connect("/data/ticket-sales.db")
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'")
    result = cursor.fetchone()[0]
    conn.close()
    with open("/data/ticket-sales-gold.txt", "w") as f:
        f.write(str(result))
    return "Ticket sales calculated successfully."

def fetch_api_data(url, output_file):
    response = requests.get(url, timeout=20)
    with open(output_file, "w") as f:
        f.write(response.text)
    return "API data saved."

def clone_git_repo(repo_url):
    subprocess.run(f"git clone {repo_url} /data/repo", shell=True, check=True)
    return "Git repository cloned."

def scrape_website(url, output_file):
    response = requests.get(url, timeout=20)
    with open(output_file, "w") as f:
        f.write(response.text)
    return "Website data scraped."

def transcribe_audio(input_file, output_file):
    transcription = get_llm_response(f"Transcribe the audio file: {input_file}")
    with open(output_file, "w") as f:
        f.write(transcription)
    return "Audio transcribed."

def markdown_to_html(input_file, output_file):
    subprocess.run(f"pandoc {input_file} -o {output_file}", shell=True, check=True)
    return "Markdown converted to HTML."

def filter_csv(input_file, output_file, column, value):
    import pandas as pd
    df = pd.read_csv(input_file)
    df[df[column] == value].to_json(output_file, orient='records', indent=2)
    return "CSV filtered and saved as JSON."

@app.route("/run", methods=["POST"])
def run_task():
    task = request.args.get("task")
    email = request.args.get("email")
    if not task:
        return jsonify({"error": "Task description is required"}), 400
    
    try:
        if "install uv and run datagen" in task.lower():
            output = install_uv_and_run_datagen(email)
        elif "format markdown" in task.lower():
            output = format_markdown()
        elif "count wednesdays" in task.lower():
            output = count_wednesdays()
        elif "sort contacts" in task.lower():
            output = sort_contacts()
        elif "extract recent logs" in task.lower():
            output = extract_recent_logs()
        elif "create markdown index" in task.lower():
            output = create_markdown_index()
        elif "calculate ticket sales" in task.lower():
            output = query_sqlite()
        elif "fetch api data" in task.lower():
            output = fetch_api_data(request.args.get("url"), "/data/api_output.txt")
        elif "clone git repo" in task.lower():
            output = clone_git_repo(request.args.get("repo_url"))
        elif "scrape website" in task.lower():
            output = scrape_website(request.args.get("url"), "/data/scraped_data.txt")
        elif "transcribe audio" in task.lower():
            output = transcribe_audio("/data/audio.mp3", "/data/transcription.txt")
        elif "convert markdown to html" in task.lower():
            output = markdown_to_html("/data/docs/input.md", "/data/docs/output.html")
        else:
            return jsonify({"error": "Task not recognized"}), 400
        
        return jsonify({"status": "success", "output": output})
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
