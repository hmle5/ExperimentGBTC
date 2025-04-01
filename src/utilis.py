from flask import request, session, flash, redirect, url_for
import hashlib
import os
import json
import random
import string


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
With that carefully crafted pitch, Ms. Holmes, whose striking stage presence in a uniform of black turtlenecks drew comparisons to Steve Jobs, became an overnight celebrity, featured on magazine covers(https://www.nytimes.com/interactive/2015/10/12/t-magazine/elizabeth-holmes-tech-visionaries-brian-chesky.html?_r=1) and richest-woman(https://www.forbes.com/sites/katiasavchuk/2015/05/27/young-and-rich-these-self-made-women-are-just-getting-started/#369040134def) lists and in glowing articles.
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


STARTUP_FILE = "startup_info.json"


def generate_startup_file():
    if os.path.exists(STARTUP_FILE):
        return

    def generate_code():
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    startups = []
    for _ in range(500):
        startups.append(
            {"code": generate_code(), "used": False, "founder": "Jessica Wilson"}
        )
        startups.append(
            {"code": generate_code(), "used": False, "founder": "Joseph Wilson"}
        )

    with open(STARTUP_FILE, "w") as f:
        json.dump(startups, f, indent=4)


def get_unused_startup():
    if not os.path.exists(STARTUP_FILE):
        generate_startup_file()

    with open(STARTUP_FILE, "r") as f:
        startups = json.load(f)

    unused = [s for s in startups if not s["used"]]
    return random.choice(unused) if unused else None


def mark_startup_as_used(code):
    if not os.path.exists(STARTUP_FILE):
        return

    with open(STARTUP_FILE, "r") as f:
        startups = json.load(f)

    for s in startups:
        if s["code"] == code:
            s["used"] = True

    with open(STARTUP_FILE, "w") as f:
        json.dump(startups, f, indent=4)
