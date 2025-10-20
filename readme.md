# Homerun

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=billxu1_homerun&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=billxu1_homerun)

A Streamlit application for analyzing real estate data with geographic visualization and school information.

## Installation

### Prerequisites

- Python 3.11 (or 3.10+)
- Git

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd homerun
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install Python dependencies via pip:
```bash
# If a requirements.txt exists in the repo:
pip install -r requirements.txt
```

4. Set up environment variables (do not hard-code secrets):
```bash
cp .env.example .env
# Export variables from .env into your shell environment:
set -a && [ -f .env ] && source .env && set +a
# or, manually:
# export DOMAIN_API_TOKEN="your_token_here"
```

> Note: The command above exports all KEY=VALUE pairs in .env into your current shell session. Confirm .env contents before sourcing.

## Running the Application

Start the Streamlit app:
```bash
source .venv/bin/activate   # ensure venv is active
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.
