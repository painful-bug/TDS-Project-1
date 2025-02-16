import subprocess
from datetime import datetime
import json
import pathlib
import requests
import os
import glob
import base64
import sqlite3
from dotenv import load_dotenv
from helpers import cosine_sim, request_ai_proxy, extract_text
import duckdb
from PIL import Image
import markdown
import csv
import speech_recognition as sr
from pydub import AudioSegment
from bs4 import BeautifulSoup
import sys
load_dotenv()
from pathlib import Path
from scipy.spatial.distance import cosine


# Task 1
def generate_data_files(user_email: str):
    subprocess.Popen(
        [
            "uv",
            "run",
            "https://raw.githubusercontent.com/ANdIeCOOl/TDS-Project1-Ollama_FastAPI-/refs/heads/main/datagen.py",
            f"{user_email}",
            "--root",
            "./data",
        ]
    )
    print("data generated successfully")


# Task 2
# def format_markdown_file(path="./data/format.md"):
#     # subprocess.Popen(
#     #     ["prettier", path, "--write", "--parser", "markdown"],
#     # )
#     subprocess.Popen(['npx', 'prettier@3.4.2', '--stdin-filepath', './data/format.md'])
#     print("data formatted successfully")

def format_markdown_file(path: str, version: str = "3.4.2"):
    """
    Format the contents of a specified file using a particular formatting tool, ensuring the file is updated in-place.
    Args:
        file_path: The path to the file to format.  
        prettier_version: The version of Prettier to use.
    """
    
    subprocess.run(["npx", f"prettier@{version}", "--write", path])

# Task 3
def count_wednesdays_in_dates(input_file, output_file):
    count = 0
    date_formats = [
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d",
        "%d-%b-%Y",
        "%b %d, %Y",
    ]
    with open(input_file) as f:
        for i in f:
            date = i.strip()
            if date:
                for format in date_formats:
                    try:
                        date_obj = datetime.strptime(date, format)
                        if date_obj.weekday() == 2:
                            count += 1
                    except ValueError:
                        continue
    with open(output_file, "w") as f:
        f.write(str(count).replace('"',''))


# Task 4
def sort_contacts(input_file="./data/contacts.json", output_file="./data/contacts-sorted.json"):
    with open("./data/contacts.json", "r") as f:
        contacts = json.load(f)
        sorted_contacts = sorted(
            contacts, key=lambda x: (x["last_name"], x["first_name"])
        )
    with open("./data/contacts-sorted.json", "w") as f:
        json.dump(sorted_contacts, f)


# Task 5
# def extract_recent_log_lines(input_file="./data/logs/", output_file="./data/logs-recent.txt"):
#     log_files = os.listdir(input_file)
#     max_filename = max(log_files, key=lambda x: int(
#         x.split("-")[1].split(".")[0]))
#     with open(f"./data/logs/{max_filename}", "r") as f:
#         lines = [next(f) for _ in range(10)]
#         with open(output_file, "w") as fw:
#             for line in lines:
#                 fw.write(line)

def extract_recent_log_lines(input_file='/data/logs', output_file='/data/logs-recent.txt', num_files=10):
    log_dir = Path(input_file)
    output_file = Path(output_file)

    # Get list of .log files sorted by modification time (most recent first)
    log_files = sorted(log_dir.glob('*.log'), key=os.path.getmtime, reverse=True)[:num_files]

    # Read first line of each file and write to the output file
    with output_file.open('w') as f_out:
        for log_file in log_files:
            with log_file.open('r') as f_in:
                first_line = f_in.readline().strip()
                f_out.write(f"{first_line}\n")
# Task 6
# def create_docs_index(input_file="./data/docs", output_file="./data/index.json"):
#     index = {}
#     p = pathlib.Path(input_file)
#     for i in p.rglob("*"):
#         if i.is_file() and i.suffix == ".md":
#             with open(i, "r") as f:
#                 title = f.readline().strip("#").strip()
#                 index[i.name] = title
#     with open(output_file, "w") as f:
#         json.dump(index, f)



def create_docs_index(input_file='/data/docs', output_file='/data/docs/index.json'):
    docs_dir = input_file
    index_data = {}

    # Walk through all files in the docs directory
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md'):
                # print(file)
                file_path = os.path.join(root, file)
                # Read the file and find the first occurrence of an H1
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('# '):
                            # Extract the title text after '# '
                            title = line[2:].strip()
                            # Get the relative path without the prefix
                            relative_path = os.path.relpath(file_path, docs_dir).replace('\\', '/')
                            index_data[relative_path] = title
                            break  # Stop after the first H1
    # Write the index data to index.json
    print(index_data)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=4)

# Task 7
# def extract_sender_email(input_file, output_file):
#     with open(input_file, "r") as f:
#         email_file_contents = f.read()
#     payload = {
#         "model": "gpt-4o-mini",
#         "messages": [
#             {
#                 "role": "user",
#                 "content": f"Extract the sender's email address from the following text : {email_file_contents} and return only the sender's email address, nothing else",
#             }
#         ],
#     }
#     response = request_ai_proxy(payload, debug=True)
#     print("RESPONSE : ", response)
#     with open(output_file, "w") as f:
#         f.write(response)

def extract_sender_email(input_file='/data/email.txt', output_file='/data/email-sender.txt'):
    # Read the content of the email
    with open(input_file, 'r') as file:
        email_content = file.readlines()

    sender_email = "sujay@gmail.com"
    for line in email_content:
        if "From" == line[:4]:
            sender_email = (line.strip().split(" ")[-1]).replace("<", "").replace(">", "")
            break

    # Get the extracted email address

    # Write the email address to the output file
    with open(output_file, 'w') as file:
        file.write(sender_email)


# Task 8
def extract_credit_card_number(image_path="./data/credit_card.png", output_file="./data/credit-card.txt"):
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "You are a specialized OCR assistant. Your only task is to analyze the provided image and return ONLY the 16-digit credit card number, with no additional text, commentary, or formatting. Do not offer any other information or make any assumptions about the card's validity.Format your response as exactly 16 digits with no spaces or separators. Nothing else should be included in your response. Note that there may be same digits placed adjacently in the card number. Please include all the digits. Do not generate any new digit",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    }
                ],
            },
        ],
    }

    cno = request_ai_proxy(payload=payload)
    with open(output_file, "w") as f:
        f.write(str(extract_text(image_path)).replace(" ", ""))  # Ensure the response is written as a string


# Task 9

def get_embedding(text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ.get("AIPROXY_TOKEN")}"
    }
    data = {
        "model": "text-embedding-3-small",
        "input": [text]
    }
    response = requests.post("http://aiproxy.sanand.workers.dev/openai/v1/embeddings", headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]

def find_most_similar_comments(input_file, output_file):
    with open(input_file, 'r') as f:
        comments = [line.strip() for line in f.readlines()]

    # Get embeddings for all comments
    embeddings = [get_embedding(comment) for comment in comments]

    # Find the most similar pair
    min_distance = float('inf')
    most_similar = (None, None)

    for i in range(len(comments)):
        for j in range(i + 1, len(comments)):
            distance = cosine(embeddings[i], embeddings[j])
            if distance < min_distance:
                min_distance = distance
                most_similar = (comments[i], comments[j])

    # Write the most similar pair to file
    with open(output_file, 'w') as f:
        f.write(most_similar[0] + '\n')
        f.write(most_similar[1] + '\n')


# Task 10
def calculate_gold_ticket_sales(input_file, output_file):
    conn = sqlite3.connect(input_file)
    cur = conn.cursor()
    total_sales = cur.execute(
        "SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'"
    ).fetchone()[0]
    print("Total sales of Gold tickets : ", total_sales)
    with open(output_file, "w") as f:
        f.write(str(total_sales))
    conn.close()


# Task B3 - Fetch data from an API and save it
def fetch_api_data(url=None):
    if not url:
        url = "https://jsonplaceholder.typicode.com/posts"
    response = requests.get(url)
    data = response.json()
    with open("./data/api_data.json", "w") as f:
        json.dump(data, f)


# Task B4 - Clone a git repo and make a commit
def clone_and_commit(url=None, commit_message="This is a commit message"):
    if os.path.exists("./data/testing"):
        os.system("rm -rf ./data/testing")
    if not url:
        url = "https://github.com/painful-bug/testing.git"
    repo_name = url.split('/')[-1].split('.')[0]
    repo_path = os.path.join("./data", repo_name)

    os.makedirs(repo_path, exist_ok=True)

    os.system(f"git clone {url} {repo_path}")

    commit_file = os.path.join(repo_path, "commit.txt")
    with open(commit_file, "w") as f:
        f.write(commit_message)

    os.chdir(repo_path)
    os.system("git add .")
    os.system(f'git commit -m "{commit_message}"')
    os.chdir("../..")

    print("Repo cloned and commit made successfully")

# Task B5 - Run a SQL query on a SQLite or DuckDB database


def run_sql_query(query, db_type, db_path=None):
    """
    Execute SQL query on a specified database.

    Args:
        query (str): SQL query to execute
        db_type (str): Type of database ('sqlite' or 'duckdb')
        db_path (str, optional): Path to database file. Defaults to "./data/ticket-sales.db"

    Returns:
        list: Query results as a list of tuples
    """
    print("DB_TYPE : ", db_type)
    print("DB_PATH : ", db_path)
    print("QUERY : ", query)
    print("Running SQL query...")
    if db_type == "sqlite":
        conn = sqlite3.connect(db_path or "./data/ticket-sales.db")
        cur = conn.cursor()
        resp = cur.execute(query).fetchall()
        print("QUERY RESPONSE : ", resp)
        conn.commit()
        conn.close()
    elif db_type == "duckdb":
        conn = duckdb.connect(db_path or "./data/ticket-sales.db")
        resp = conn.sql(query).fetchall()
        print("QUERY RESPONSE : ", resp)
        conn.close()
    else:
        print("Invalid database type")
    return resp
# Task B6 - Extract data from (i.e. scrape) a website


def scrape_website_data(url, output_file="./data/website_data.html"):
    """
    Scrape data from a website and save it to a file.

    Args:
        url (str): Website URL to scrape
        output_file (str, optional): Path to save scraped data. Defaults to "./data/website_data.html"

    Returns:
        str: Prettified HTML content
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    with open(output_file, "w") as file:
        file.write(soup.prettify())
    return soup.prettify()


def compress_image(input_file, quality, output_file="../data/compressed_image.jpg"):
    """
    Compress an image with specified quality.

    Args:
        input_file (str): Path to input image file
        quality (int): Compression quality (0-100)
        output_file (str, optional): Path to save compressed image. Defaults to "../data/compressed_image.jpg"

    Returns:
        None: Saves compressed image to output_file
    """
    img = Image.open(input_file)
    img.save(output_file, quality=quality)


def convert_markdown_to_html(input_file: str, output_file: str = "../data/markdown_to_html.html"):
    """
    Convert a markdown file to HTML format.

    Args:
        input_file (str): Path to input markdown file
        output_file (str, optional): Path to save HTML output. Defaults to "../data/markdown_to_html.html"

    Returns:
        None: Saves converted HTML to output_file
    """
    with open(input_file, "r") as file:
        html = markdown.markdown(file.read())
    with open(output_file, "w") as file:
        file.write(html)


def filter_csv_api_endpoint():
    """
    Create a Flask API endpoint for filtering CSV data.

    The endpoint accepts POST requests with parameters:
    - input_file: Path to input CSV
    - column: Column name to filter on
    - value: Value to filter for
    - output_file: Path to save filtered JSON

    Returns:
        str: Flask application code as a string
    """
    return """
from flask import Flask

app = Flask()

def filter_csv(input_file: str, column: str, value: str, output_file: str):
    results = []
    with open(input_file, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row[column] == value:
                results.append(row)
    with open(output_file, "w") as file:
        json.dump(results, file)

@app.route("/filter_csv", methods=["POST"])
def filter_csv():
    input_file = request.args.get("input_file")
    column = request.args.get("column")
    value = request.args.get("value")
    output_file = request.args.get("output_file")
    filter_csv(input_file, column, value, output_file)
    return {"result" : "ok"}, 200
"""


def check_dependencies():
    """
    Check if required system dependencies (ffmpeg) are installed.

    Returns:
        None: Exits with error if dependencies are missing
    """
    # Check if ffmpeg is installed
    try:
        subprocess.run(['ffmpeg', '-version'],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("Error: ffmpeg is not installed. Install it using:")
        print("sudo apt-get update && sudo apt-get install ffmpeg")
        sys.exit(1)


def transcriber(audio_path, output_file="./data/transcription.txt"):
    """
    Transcribe audio from an MP3 file to text.

    Args:
        audio_path (str): Path to input MP3 file
        output_file (str, optional): Path to save transcription. Defaults to "./data/transcription.txt"

    Returns:
        None: Saves transcription to output_file
    """
    check_dependencies()
    # Check if input file exists
    if not os.path.exists(audio_path):
        print(f"Error: File '{audio_path}' not found")
        return

    # Initialize recognizer
    recognizer = sr.Recognizer()

    # Convert mp3 to wav using pydub
    print("Converting mp3 to wav...")
    try:
        audio = AudioSegment.from_mp3(audio_path)
        wav_path = "/tmp/temp_audio.wav"  # Using /tmp directory for temporary files
        audio.export(wav_path, format="wav")
    except Exception as e:
        print(f"Error converting audio: {e}")
        return

    # Transcribe the audio
    print("Transcribing audio...")
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)

            # Save transcription to file
            output_path = output_file
            with open(output_path, "w") as f:
                f.write(text)
            print(f"Transcription saved to: {output_path}")

        except sr.UnknownValueError:
            print("Speech recognition could not understand the audio")
        except sr.RequestError as e:
            print(
                f"Could not request results from speech recognition service; {e}")
        finally:
            # Clean up temporary wav file
            if os.path.exists(wav_path):
                os.remove(wav_path)

# def transcriber(file_path):
#     """
#     Given a path to an audio file, this function:
#     1. Detects the language of the audio.
#     2. Transcribes the audio in that detected language.
#     3. Saves the transcription to 'transcription.txt'.
#     """

#     if not os.path.exists(file_path):
#         print("File not found")
#         return None

#     try:
#         # Load the Whisper model (automatically detects language and transcribes accordingly)
#         model = whisper.load_model("base")

#         # Transcribe the audio file
#         result = model.transcribe(file_path)
#         transcription = result.get("text", "")
#         detected_language = result.get("language", "unknown")
#         print(f"Detected language: {detected_language}")

#         # Save the transcription in a file
#         with open("transcription.txt", "w", encoding="utf-8") as f:
#             f.write(transcription)

#         return transcription
#     except Exception as e:
#         print(f"An error occurred during transcription: {e}")
#         return None

# run_sql_query('')
