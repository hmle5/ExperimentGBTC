from flask import request, session, flash, redirect, url_for
import random
import pandas as pd
import hashlib
import json
import os
from functools import wraps


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
