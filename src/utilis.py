from flask import request, session, flash, redirect, url_for
import hashlib
import os
import json
import random
import string
import pandas as pd


# Utilities
def get_client_ip():
    return request.remote_addr


def get_user_agent():
    return request.headers.get("User-Agent")


def generate_unique_participant_id():
    ip = get_client_ip()
    user_agent = get_user_agent()
    unique_string = f"{ip}-{user_agent}"
    return hashlib.sha256(unique_string.encode()).hexdigest()


NEWS_FILE = "news_story.json"

HOLMES_ARTICLE = {
    "title": "Elizabeth Holmes, Theranos C.E.O. and Silicon Valley Star, Accused of Fraud",
    "content": """Holding up a few drops of blood, Elizabeth Holmes became a darling of Silicon Valley by promising that her company’s new device would give everyday Americans unlimited control over their health with a single finger prick.
Ms. Holmes, a Stanford University dropout who founded her company, Theranos, at age 19, captivated investors and the public with her invention: a technology cheaply done at a local drugstore that could detect a range of illnesses, from diabetes to cancer.
With that carefully crafted pitch, Ms. Holmes, whose striking stage presence in a uniform of black turtlenecks drew comparisons to Steve Jobs, became an overnight celebrity, featured on magazine covers and richest-woman lists and in glowing articles.
Her fall — and the near-collapse of Theranos — has been equally dramatic in the last few years. On Wednesday, the Securities and Exchange Commission charged Ms. Holmes, now 34, with widespread fraud, accusing her of exaggerating — even lying — about her technology while raising $700 million from investors.""",
    "source": "The New York Times",
    "question": "What was the product promised by Elizabeth Holmes’ start-up and what happened to it?",
    "options": [
        "The product was a medical device that can cure cancer which was not approved to be used in hospitals.",
        "The product was an invention that can diagnose diabetes which was not successful in having a market scale-up.",
        "The product was a technology that can diagnose illnesses with minimal amounts of blood which was accused of cheating.",
    ],
    "correct_answer": "The product was a technology that can diagnose illnesses with minimal amounts of blood which was accused of cheating.",
}

MYSTICETES_ARTICLE = {
    "title": "How whales sing without drowning, an anatomical mystery solved",
    "content": """The deep haunting tones of the world’s largest animals, baleen whales (mysticetes), are iconic. But how the songs are produced has long been a mystery. 
Whales evolved from land dwelling mammals, which vocalize by passing air through a structure called the larynx — a structure that also helps keep food from entering the respiratory system. However, toothed whales such as dolphins do not use their larynx to make sound, instead they have evolved a specialized organ in their nose. 
Now the structure used by baleen whales — a modified version of the larynx is discovered. Whales like humpbacks and blue whales are able to create powerful vocalizations but their anatomy also limits the frequency of the sounds they can make and depth at which they can sing. This leaves them unable to escape anthropogenic noise pollution that occurs in the same range.""",
    "source": "Nature",
    "question": "What is mysticetes and what happened to it?",
    "options": [
        "mysticetes is a whale pieces that can produce sounds at high frequencies and how they could do that is now discovered.",
        "mysticetes is a whale pieces also known as baleen that can sing while breathing in water and how they could do that is now being argued.",
        "mysticetes is a whale pieces that can sing while breathing in water and how they could do that is now discovered.",
    ],
    "correct_answer": "mysticetes is a whale pieces that can sing while breathing in water and how they could do that is now discovered.",
}


def generate_news_story_file():
    """Create the JSON file at startup if it does not exist."""
    if os.path.exists(NEWS_FILE):
        return  # File already exists, do nothing

    def generate_code():
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    # Generate 500 unique entries for each story type
    stories = []
    for _ in range(500):
        stories.append({"code": generate_code(), "used": False, "story": "holmes"})
        stories.append({"code": generate_code(), "used": False, "story": "mysticetes"})

    # Save to JSON file
    with open(NEWS_FILE, "w") as f:
        json.dump(stories, f, indent=4)


def get_unused_story():
    """Fetch a random unused story entry but DO NOT mark it as used yet."""
    if not os.path.exists(NEWS_FILE):
        generate_news_story_file()  # Ensure the file exists

    with open(NEWS_FILE, "r") as f:
        stories = json.load(f)

    # Find all unused stories
    unused_stories = [story for story in stories if not story["used"]]

    if not unused_stories:
        return None  # No unused stories left

    # Randomly select one
    selected_story = random.choice(unused_stories)

    return selected_story  # Return but don't mark as used yet


def mark_story_as_used(story_code):
    """Mark the story as used only if the user answers correctly."""
    if not os.path.exists(NEWS_FILE):
        return  # No file means no data to update

    with open(NEWS_FILE, "r") as f:
        stories = json.load(f)

    for story in stories:
        if story["code"] == story_code:
            story["used"] = True  # Now mark it as used

    # Save updated JSON file
    with open(NEWS_FILE, "w") as f:
        json.dump(stories, f, indent=4)


# === CONFIGURABLE CONSTANTS ===
DEFAULT_EXCEL_PATH = "data/clean_data.xlsx"
DEFAULT_JSON_PATH = "startup_data.json"
DEFAULT_NUM_SETS = 1000
DEFAULT_SET_SIZE = 6
DEFAULT_CODE_LENGTH = 10


def normalize_text(text):
    """Fix unicode artifacts like curly quotes, non-breaking spaces, etc."""
    if pd.isna(text):
        return ""
    return (
        str(text)
        .replace("\xa0", " ")  # non-breaking space
        .replace("\u2019", "'")  # curly apostrophe
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .strip()
    )


def load_excel_data(excel_path):
    """Load and normalize all string fields in both sheets."""
    sheets = pd.read_excel(excel_path, sheet_name=None)
    startup_df = sheets["Tabelle1"]
    founder_df = sheets["Tabelle2"]

    # Normalize string fields in both DataFrames
    for df in (startup_df, founder_df):
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].apply(normalize_text)

    return startup_df, founder_df


def generate_unique_code(existing_codes, length=8):
    """Generate a unique alphanumeric code not already in use."""
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if code not in existing_codes:
            return code


def prepare_randomized_startup_set(
    startup_df, founder_names, evaluation_sentences, set_size
):
    """Prepare one startup set with normalized data and substituted evaluation sentence."""
    selected_startups = startup_df.sample(n=set_size, replace=False).to_dict(
        orient="records"
    )
    assigned_founders = random.sample(founder_names, set_size)
    assigned_sentences = random.choices(evaluation_sentences, k=set_size)

    combined = []
    for i, startup in enumerate(selected_startups):
        name = startup["Startup_name_altered"]
        sentence = assigned_sentences[i].replace("[StartupName]", name)

        combined.append(
            {
                "Startup_name": name,
                "Industry": startup["Industry"],
                "Product_info": startup["Product_info_altered"],
                "Founded": (
                    int(startup["Founded_10"])
                    if not pd.isna(startup["Founded_10"])
                    else None
                ),
                "Founder_age": (
                    int(startup["Founder_inferred_age"])
                    if not pd.isna(startup["Founder_inferred_age"])
                    else None
                ),
                "Founder_Nstartups": (
                    int(startup["Founder_Nstartups"])
                    if not pd.isna(startup["Founder_Nstartups"])
                    else None
                ),
                "Assigned_Founder": assigned_founders[i],
                "Evaluation_sentence": sentence,
            }
        )

    random.shuffle(combined)
    return combined


def save_startup_sets_to_json(sets, path):
    """Save the full list of generated sets to a JSON file."""
    with open(path, "w") as f:
        json.dump(sets, f, indent=4)


def generate_startup_sets(
    excel_path=DEFAULT_EXCEL_PATH,
    output_path=DEFAULT_JSON_PATH,
    num_sets=DEFAULT_NUM_SETS,
    set_size=DEFAULT_SET_SIZE,
    code_length=DEFAULT_CODE_LENGTH,
):
    """Generate randomized startup sets and write to JSON if not already existing."""
    if os.path.exists(output_path):
        return False

    startup_df, founder_df = load_excel_data(excel_path)

    # Ensure required fields are present
    startup_df = startup_df.dropna(
        subset=["Startup_name_altered", "Industry", "Product_info_altered"]
    )
    founder_names = founder_df["Founder_name_altered"].dropna().unique().tolist()
    evaluation_sentences = startup_df["Evaluation_sentence"].dropna().tolist()

    # Validation
    if len(founder_names) < set_size:
        raise ValueError("Not enough founder names in Excel to build a full set.")

    startup_sets = []
    used_codes = set()

    for _ in range(num_sets):
        startup_data = prepare_randomized_startup_set(
            startup_df, founder_names, evaluation_sentences, set_size
        )
        code = generate_unique_code(used_codes, length=code_length)
        used_codes.add(code)

        startup_sets.append(
            {
                "code": code,
                "used": False,
                "startups": startup_data,
            }
        )

    save_startup_sets_to_json(startup_sets, output_path)
    return True


def mark_startup_set_as_used(code, path=DEFAULT_JSON_PATH):
    """
    Mark a startup set as 'used': True in the JSON file for a given code.

    Args:
        code (str): The 10-character startup set code.
        path (str): Path to the JSON file.

    Returns:
        bool: True if update was successful, False if code not found or file missing.
    """
    if not os.path.exists(path):
        return False

    with open(path, "r") as f:
        sets = json.load(f)

    updated = False
    for s in sets:
        if s["code"] == code:
            s["used"] = True
            updated = True
            break

    if updated:
        with open(path, "w") as f:
            json.dump(sets, f, indent=4)
    return updated
