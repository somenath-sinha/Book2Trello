import os
import sys
import yaml
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=".secrets")

class TrelloManager:
    def __init__(self):
        self.api_key = os.getenv("TRELLO_API_KEY")
        self.token = os.getenv("TRELLO_TOKEN")
        
        if not self.api_key or not self.token:
            print("Error: Missing keys in .secrets file.")
            sys.exit(1)
            
        self.base_url = "https://api.trello.com/1"
        self.auth = {"key": self.api_key, "token": self.token}

    def get_or_create_label(self, board_id, label_name, color="yellow"):
        url = f"{self.base_url}/boards/{board_id}/labels"
        response = requests.get(url, params=self.auth)
        
        for label in response.json():
            if label['name'].lower() == label_name.lower():
                return label['id']
                
        payload = {**self.auth, "name": label_name, "color": color, "idBoard": board_id}
        return requests.post(f"{self.base_url}/labels", params=payload).json()['id']

    def _flatten_subheadings(self, subheadings, prefix=""):
        """Recursively turns a nested tree into a flat list of breadcrumb strings."""
        flat_list = []
        for item in subheadings:
            if isinstance(item, str):
                # Leaf node
                flat_list.append(f"{prefix}{item}")
            elif isinstance(item, dict):
                # Parent node with its own subheadings
                title = item["title"]
                flat_list.append(f"{prefix}{title}")
                
                if "subheadings" in item:
                    # Pass down the breadcrumb trail
                    new_prefix = f"{prefix}{title} > " if prefix else f"{title} > "
                    flat_list.extend(self._flatten_subheadings(item["subheadings"], new_prefix))
        return flat_list

    def create_card(self, list_id, name, label_id, comment_text, raw_subheadings):
        payload = {**self.auth, "idList": list_id, "name": name, "idLabels": label_id}
        card_res = requests.post(f"{self.base_url}/cards", params=payload)
        card_id = card_res.json()['id']
        
        requests.post(f"{self.base_url}/cards/{card_id}/actions/comments", params={**self.auth, "text": comment_text})
        
        if raw_subheadings:
            check_res = requests.post(f"{self.base_url}/cards/{card_id}/checklists", params={**self.auth, "name": "Chapter progress"})
            checklist_id = check_res.json()['id']
            
            # Flatten the tree before pushing to Trello
            flat_items = self._flatten_subheadings(raw_subheadings)
            
            for item in flat_items:
                requests.post(f"{self.base_url}/checklists/{checklist_id}/checkItems", params={**self.auth, "name": item})

def main():
    if len(sys.argv) < 2:
        print("Usage: python yaml_to_trello.py ")
        sys.exit(1)
        
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        chapters = yaml.safe_load(f)

    board_id = os.getenv("TRELLO_BOARD_ID")
    list_id = os.getenv("TRELLO_LIST_ID")

    print("\n--- Book Metadata ---")
    tag_name = input("Tag/Label name (e.g., 'Git'): ")
    book_title = input("Book Name: ")
    edition = input("Edition: ")
    isbn = input("ISBN (optional): ")
    
    comment_text = f"**Source:** {book_title}\n**Edition:** {edition}\n**ISBN:** {isbn}"
    
    trello = TrelloManager()
    label_id = trello.get_or_create_label(board_id, tag_name)
    
    print("\nBuilding Trello Cards...")
    for idx, chapter in enumerate(chapters, 1):
        card_title = f"{tag_name} {idx}: {chapter['title']} ({chapter.get('length_pages', 0)} pages)"
        print(f"Creating -> {card_title}")
        
        trello.create_card(
            list_id=list_id,
            name=card_title,
            label_id=label_id,
            comment_text=comment_text,
            raw_subheadings=chapter.get('subheadings', [])
        )
        
    print("\nSuccess! Board populated with nested checklist items.")

if __name__ == "__main__":
    main()