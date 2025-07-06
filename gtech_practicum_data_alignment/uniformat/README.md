# Uniformat II Data Enrichment Project

This repository contains the code and resources for extracting, enriching, and exploring Uniformat II construction classification codes using a combination of PDF parsing, Google Gemini AI, and a SQLite database.

## Table of Contents
1.  [Project Overview](#project-overview)
2.  [Setup](#setup)
    * [Prerequisites](#prerequisites)
    * [Environment Variables](#environment-variables)
    * [Installation](#installation)
    * [Running the Data Processing Workflow](#running-the-data-processing-workflow)
    * [Running the Dashboard](#running-the-dashboard)
3.  [Data](#data)
4.  [Model (AI/LLM)](#model-aillm)
5.  [Repository Structure](#repository-structure)
6.  [Code Guidelines & Collaborators](#code-guidelines--collaborators)
7.  [License](#license)

---

## 1. Project Overview

The goal of this project is to create a comprehensive and enriched database of Uniformat II construction elements. This involves:
* Ingesting initial Uniformat codes from a CSV file.
* Extracting detailed "Includes" and "Excludes" lists from a Uniformat II guide PDF using PDF parsing and Google Gemini AI.
* Leveraging Google Gemini AI to generate rich, detailed descriptions for each Uniformat Level 3 element, combining information from their names, inclusions, and exclusions.
* Storing all this structured information in a SQLite database.
* Providing a Streamlit dashboard for interactive exploration of the enriched data.

---

## 2. Setup

### Prerequisites

* Python 3.8+
* Git
* Jupyter Notebook (for running `.ipynb` files)

### Environment Variables

This project requires a Google Gemini API key to interact with the large language model.
1.  Obtain your API key from the [Google AI Studio](https://makersuite.google.com/app/apikey).
2.  Create a file named `.env` in the **root directory** of this repository.
3.  Add your API key to the `.env` file as follows:
    ```
    GEMINI_API_KEY=your_actual_gemini_api_key_here
    ```
    **Security Note:** Do NOT commit your `.env` file to version control (e.g., Git). It's already included in the `.gitignore` to prevent this.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your_username/uniformat_project.git](https://github.com/your_username/uniformat_project.git)
    cd uniformat_project
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Data Processing Workflow

The core data extraction and enrichment pipeline can be initiated in two ways:

1.  **Via the `main_workflow.py` script (recommended for full, automated run):**
    This script orchestrates the entire data enrichment pipeline from start to finish. It will:
    * Set up the `uniformat.db` SQLite database in the **root directory** of the project.
    * Load initial Uniformat codes from `data_sources/uniformat-ii-codes.csv`.
    * Extract text from `data_sources/uniformat-guide.pdf` (pages 61-83) using `final_scripts/pdf_extractor.py`.
    * Call the Gemini API via `final_scripts/gemini_processor.py` to extract "Includes" and "Excludes" for Level 3 codes.
    * Call the Gemini API via `final_scripts/gemini_processor.py` to generate detailed descriptions for all Level 3 codes.
    * Update the database with all extracted and generated information using `final_scripts/db_operations.py`.

    To run the workflow:
    ```bash
    python final_scripts/main_workflow.py
    ```
    *Note: This process involves API calls and may take some time to complete depending on the number of elements and API rate limits.*

2.  **Step-by-step via `Data_preprocessing.ipynb` (recommended for understanding and interactive execution):**
    This Jupyter Notebook provides a detailed, cell-by-cell explanation and interactive execution of the data preprocessing and enrichment pipeline. It's ideal for understanding how each modular script contributes to the overall process.

    To run this notebook:
    * Ensure you are in the **root directory** of the project in your terminal.
    * Start Jupyter Notebook:
        ```bash
        jupyter notebook
        ```
    * In the Jupyter interface, navigate into the `final_scripts/` folder and open `Data_preprocessing.ipynb`.
    * Execute the cells sequentially. The notebook includes specific instructions within its first cell to correctly set up the Python path for importing modules from the `final_scripts` package and accessing project-root-level files.

### Running the Dashboard

Once the `uniformat.db` has been populated by the data processing workflow, you can run the interactive Streamlit dashboard.

```bash
streamlit run dashboard.py