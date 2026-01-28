
# SKELETON: Reasoning over Knowledge Graphs for Evidence-Aware LLM Answering

This repository contains the implementation for the paper **"SKELETON: Reasoning over Knowledge Graphs for Evidence-Aware LLM Answering"**.

## Environment Setup

### Knowledge Graph Database
The system relies on a local Freebase Knowledge Graph. Please follow the instructions in [`freebase_setup.md`](freebase_setup.md) to set up the required database before proceeding.

### Python Dependencies
*   **`openai`**: For making API calls to the LLM (e.g., GPT models).
*   **`loguru` & `beautifultable`**: For logging and formatted output display.

## Repository Structure

```
.
├── data/                   # Contains the Question-Answering datasets.
├── jsons/                  # Stores the extracted reasoning skeletons in dictionary format.
├── logs/                   # Runtime logs generated during execution.
├── prepare_steps/          # Python scripts for skeleton extraction.
│   ├── step1_*.py
│   ├── step2_*.py
│   └── ...                 # Run scripts in sequential order to generate files in `jsons/`.
├── prompts/                # Contains all prompt templates used for LLM interaction.
├── utils.py                # Core utilities (API key configuration here).
├── main.py                 # Main script to run the SKELETON pipeline.
└── freebase_setup.md       # Instructions for setting up the Freebase KG.
```

**Note:** The `jsons/` folder contains pre-generated skeleton files. You can use them directly. If you wish to regenerate them, run the scripts in the `prepare_steps/` directory in order.

## Usage

### Configuration
Before running the code, you must set your **API key** in [`utils.py`](utils.py). Replace the placeholder in the relevant configuration section.

### Running the Pipeline
Execute the main script with the following command:

```bash
python main.py --dataset <dataset_name> --start_id <start_index> --end_id <end_index>
```

**Example:**
```bash
python main.py --dataset cwq --start_id 0 --end_id 50
```

**Arguments:**
*   `--dataset`: The QA dataset to use (e.g., `cwq`).
*   `--start_id`: The starting index (inclusive) of the questions to process.
*   `--end_id`: The ending index (exclusive) of the questions to process.
