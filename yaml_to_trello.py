"""
Reads a book structure from a YAML file and creates corresponding
cards and checklists in a specified Trello list.
"""

import os
import sys
import yaml
import requests
import re
from dotenv import load_dotenv

load_dotenv(dotenv_path=".secrets")

class TrelloManager:
    """
    Manages API interactions with Trello.
    """
    def __init__(self):
        """
        Initializes the manager by loading credentials from environment variables.
        """
        self.api_key = os.getenv("TRELLO_API_KEY")
        self.token = os.getenv("TRELLO_TOKEN")
        
        if not self.api_key or not self.token:
            print("Error: Missing keys in .secrets file.")
            sys.exit(1)
            
        self.base_url = "https://api.trello.com/1"
        self.auth = {"key": self.api_key, "token": self.token}

    def get_or_create_label(self, board_id, label_name, color="yellow"):
        """
        Retrieves the ID of an existing label by name or creates it if it doesn't exist.
        """
        url = f"{self.base_url}/boards/{board_id}/labels"
        response = requests.get(url, params=self.auth)
        
        for label in response.json():
            if label['name'].lower() == label_name.lower():
                return label['id']
                
        payload = {**self.auth, "name": label_name, "color": color, "idBoard": board_id}
        return requests.post(f"{self.base_url}/labels", params=payload).json()['id']

    def get_existing_card_names(self, list_id):
        """
        Returns a set of card names currently present in the specified list.
        """
        url = f"{self.base_url}/lists/{list_id}/cards"
        response = requests.get(url, params=self.auth)
        return {card['name'] for card in response.json()}

    def _flatten_subheadings(self, subheadings, prefix=""):
        """
        Recursively flattens a nested list of subheadings into a flat list of strings.
        """
        flat_list = []
        for item in subheadings:
            if isinstance(item, str):
                flat_list.append(f"{prefix}{item}")
            elif isinstance(item, dict):
                title = item["title"]
                flat_list.append(f"{prefix}{title}")
                
                if "subheadings" in item:
                    new_prefix = f"{prefix}{title} > " if prefix else f"{title} > "
                    flat_list.extend(self._flatten_subheadings(item["subheadings"], new_prefix))
        return flat_list

    def create_card(self, list_id, name, label_id, comment_text, raw_subheadings):
        """
        Creates a new card with a label, comment, and optional checklist for subheadings.
        """
        payload = {**self.auth, "idList": list_id, "name": name, "idLabels": label_id}
        card_res = requests.post(f"{self.base_url}/cards", params=payload)
        card_id = card_res.json()['id']
        
        requests.post(f"{self.base_url}/cards/{card_id}/actions/comments", params={**self.auth, "text": comment_text})
        
        if raw_subheadings:
            check_res = requests.post(f"{self.base_url}/cards/{card_id}/checklists", params={**self.auth, "name": "Chapter progress"})
            checklist_id = check_res.json()['id']
            
            flat_items = self._flatten_subheadings(raw_subheadings)
            
            for item in flat_items:
                requests.post(f"{self.base_url}/checklists/{checklist_id}/checkItems", params={**self.auth, "name": item})

def main():
    """
    Main function to read the YAML file, prompt the user for configuration,
    and trigger Trello card creation.
    """
    if len(sys.argv) < 2:
        print("Usage: python yaml_to_trello.py ")
        sys.exit(1)
        
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    metadata = data.get("metadata", {})
    chapters = data.get("chapters", [])

    board_id = os.getenv("TRELLO_BOARD_ID")
    list_id = os.getenv("TRELLO_LIST_ID")

    print("\n--- Extracted Book Metadata ---")
    for key, value in metadata.items():
        print(f"{key.capitalize()}: {value}")
    print("-------------------------------\n")
    
    tag_name = input("Tag/Label name for the Trello board (e.g., 'DevOps'): ")
    
    suggested_short = metadata.get('short_title', metadata.get('title', 'Book'))
    short_name = input(f"Short book name for card titles [{suggested_short}]: ")
    
    if not short_name.strip():
        short_name = suggested_short
    
    base_comment_lines = [
        f"**Source:** {metadata.get('title', 'Unknown Title')}",
        f"**Author:** {metadata.get('author', 'Unknown Author')}"
    ]
    
    if "edition" in metadata:
        base_comment_lines.append(f"**Edition:** {metadata['edition']}")
    if "isbn" in metadata:
        base_comment_lines.append(f"**ISBN:** {metadata['isbn']}")
        
    base_comment_text = "\n".join(base_comment_lines)
    
    trello = TrelloManager()
    label_id = trello.get_or_create_label(board_id, tag_name)
    
    print("\nChecking for existing cards...")
    existing_cards = trello.get_existing_card_names(list_id)
    
    print("\nBuilding Trello Cards...")
    for idx, chapter in enumerate(chapters, 1):
        
        raw_title = chapter['title']
        
        # Aggressively strip "1. " or "Chapter 1: " from the raw title
        cleaned_title = re.sub(r'^(?:Chapter\s+)?\d+[\.\:\-]?\s*', '', raw_title, flags=re.IGNORECASE)
        
        # Build the custom numeric prefix
        part_val = chapter.get('part')
        num_prefix = f"{part_val}.{idx}" if part_val else f"{idx}"
        
        card_title = f"{short_name.strip()}: {num_prefix}. {cleaned_title}"
        
        if card_title in existing_cards:
            print(f"Skipping -> {card_title} (Already exists)")
            continue
            
        print(f"Creating -> {card_title}")
        
        chapter_comment = f"{base_comment_text}\n**Length:** {chapter.get('length_pages', 0)} pages"
        
        trello.create_card(
            list_id=list_id,
            name=card_title,
            label_id=label_id,
            comment_text=chapter_comment,
            raw_subheadings=chapter.get('subheadings', [])
        )
        
    print("\nSuccess! Board populated.")

if __name__ == "__main__":
    main()