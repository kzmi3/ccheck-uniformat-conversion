# Uniformat II Data Enrichment Project

This repository contains the code and resources for extracting, enriching, and exploring Uniformat II construction classification codes using a combination of PDF parsing, Google Gemini AI, and a SQLite database.

## Table of Contents
1.  Project Overview
2.  Setup
    * Prerequisites
    * Environment Variables
    * Installation
    * Running the Data Processing Workflow
3.  Data
4.  Model (AI/LLM)

---

## 1. Project Overview

The goal of this project is to create a comprehensive and enriched database of Uniformat II construction elements. This involves:
* Ingesting initial Uniformat codes from a CSV file.
* Extracting detailed "Includes" and "Excludes" lists from a Uniformat II guide PDF using PDF parsing and Google Gemini AI.
* Leveraging Google Gemini AI to generate rich, detailed descriptions for each Uniformat Level 3 element, combining information from their names, inclusions, and exclusions.
* Storing all this structured information in a SQLite database.

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
    **Note:** Do NOT commit your `.env` file to version control (e.g., Git). It's already included in the `.gitignore` to prevent this.


### Running the Data Processing Workflow

The entire data processing and enrichment pipeline is orchestrated and explained within the `Data_preprocessing.ipynb` Jupyter Notebook. This notebook provides a detailed, cell-by-cell explanation and interactive execution of the data preprocessing and enrichment pipeline. It's ideal for understanding how each modular script contributes to the overall process.

To run this notebook:
* Ensure you are in the **root directory** of the project in your terminal.
* Start Jupyter Notebook:
    ```bash
    jupyter notebook
    ```
* In the Jupyter interface, navigate into the `final_scripts/` folder and open `Data_preprocessing.ipynb`.
* Execute the cells sequentially. The notebook includes specific instructions within its first cell to correctly set up the Python path for importing modules from the `final_scripts` package and accessing project-root-level files.

*Note: This process involves API calls and may take some time to complete depending on the number of elements and API rate limits.*

---

## 3. Data

* `data_sources/uniformat-ii-codes.csv`: The initial source of Uniformat II codes (Level 1 to Level 4).
* `data_sources/uniformat-guide.pdf`: The official guide used for extracting detailed "Includes" and "Excludes" information.
* `uniformat.db`: The SQLite database that stores all processed, extracted, and enriched Uniformat II data. This database will be created and populated in the 'gtech_practicum_data_alignment' **root directory** of the project when the data processing workflow is run.

---

## 4. Model (AI/LLM)

This project leverages the **Google Gemini AI** (specifically `gemini-1.5-flash-latest` and `gemini-2.5-flash` or similar, as configured in `gemini_processor.py`) for:
* Accurately extracting "Includes" and "Excludes" lists from unstructured text in the PDF.
* Generating comprehensive and detailed descriptions for each Uniformat Level 3 element based on its name, inclusions, and exclusions.



