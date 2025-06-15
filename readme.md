# Homerun

A Streamlit application for analyzing real estate data with geographic visualization and school information.

## Installation

### Prerequisites

Make sure you have [Conda](https://docs.conda.io/en/latest/miniconda.html) installed on your system.

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd homerun
```

2. Create and activate the Conda environment:
```bash
conda env create -f environment.yml
conda activate homerun
```

3. Dependencies are installed via the `environment.yml` file during the previous step.

4. Set up environment variables:
    - Copy `.env.example` to `.env`
    - the .env keys are only required if you want to use the "get_" functions which create the underlying data (i.e. POI data, Google times, Domain scraped data)

## Running the Application

Start the Streamlit app:
```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.
By default the app won't render any maps until you hit "apply".
