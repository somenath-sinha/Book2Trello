# Book2Trello: PDF to Practice

[![Tests](https://github.com/somenath-sinha/Book2Trello/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/somenath-sinha/Book2Trello/actions/workflows/tests.yml)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Code coverage](https://codecov.io/gh/somenath-sinha/Book2Trello/branch/main/graph/badge.svg)](https://codecov.io/gh/somenath-sinha/Book2Trello)

Welcome to **Book2Trello**! This is a collection of scripts designed to take the structure of your PDF books and turn them into actionable, organized tasks on a Trello board. 

It helps you seamlessly integrate reading into your workflow by turning chapters and subheadings into checklists and cards.

## The Scripts

1. **`pdf_to_yaml.py`**: Extracts the table of contents from your PDF file, ignoring common distractions like prefaces and indices, and neatly formats the structure into a `book_structure.yaml` file.
2. **`yaml_to_trello.py`**: Reads your generated YAML file and automatically creates Trello cards. Each chapter gets a card, complete with a checklist of subheadings for you to track your progress.
3. **`nuke_trello_list.py`**: A handy utility script to completely clear out your target Trello list. Great for when you need a fresh start (but use with caution!).

## Installation & Setup

1. Clone the repository:
```bash
git clone https://github.com/somenath-sinha/Book2Trello.git
cd Book2Trello
```

2. Install the required dependencies:
```bash
pip install pymupdf pyyaml requests python-dotenv
```

### Configuration (`.secrets`)

To interact with Trello, you'll need to set up your API credentials. Create a `.secrets` file in the root directory (this file is git-ignored for your safety):

```env
TRELLO_API_KEY=your_trello_api_key
TRELLO_TOKEN=your_trello_token
TRELLO_BOARD_ID=your_trello_board_id
TRELLO_LIST_ID=your_trello_list_id
```

**How to find your Trello IDs:**
1. **API Key & Token:** Go to [Trello's Power-Up Admin portal](https://trello.com/power-ups/admin/) to generate your API Key and a Server Token.
2. **Board ID:** Open your Trello board in a web browser. Add `.json` to the end of the URL (e.g., `https://trello.com/b/xyz123/my-board.json`). Search the resulting JSON page for `"id":` near the top—that's your `TRELLO_BOARD_ID`.
3. **List ID:** *Note: First, create a list on your board named "Automated TODO". This list is meant to be managed exclusively by these scripts, so try to leave it alone unless you are interacting via the script.* On that same `.json` page, search for `"name":"Automated TODO"`. The `"id":` property directly preceding or inside that list object is your `TRELLO_LIST_ID`.

## Usage

### 1. Extract the Book Structure
Convert your PDF into a YAML structure file:
```bash
python src/pdf_to_yaml.py path/to/your/book.pdf
```
*This will generate a `book_structure.yaml` file in your directory.*

### 2. Populate Trello
Turn the YAML structure into Trello cards:
```bash
python src/yaml_to_trello.py book_structure.yaml
```
*You'll be prompted to provide a tag/label and a short name for the cards.*

### 3. Clear the List (Optional)
If you made a mistake or just want to wipe the target Trello list clean:
```bash
python src/nuke_trello_list.py
```
*Note: This will permanently delete all cards in the specified list.*

## Running Tests

If you want to run the test suite and check coverage:

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run pytest with coverage
pytest --cov=src --cov-report=term-missing
```

Happy reading, and happy doing!
