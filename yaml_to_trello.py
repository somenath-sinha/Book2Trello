import os
import sys
import yaml
import requests
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class TrelloManager:
    def __init__(self):
        # Pull secrets securely from the environment
        self.api_key = os.getenv("TRELLO_API_KEY")
        self.token = os.getenv("TRELLO_TOKEN")
        
        if not self.api_key or not self.token:
            print("Error: Missing Trello API Key or Token in .env file.")
            sys.exit(1)
            
        self.base_url = "https://api.trello.com/1"
        self.auth = {"key": self.api_key, "token": self.token}

    def get_or_create_label(self, board_id, label_name, color="yellow"):
        url = f"{self.base_url}/boards/{board_id}/labels"
        response = requests.get(url, params=self.auth)
        labels = response.json()
        
        for label in labels:
            if label['name'].lower() == label_name.lower():
                return label['id']
                
        payload = {**self.auth, "name": label_name, "color": color, "idBoard": board_id}
        response = requests.post(f"{self.base_url}/labels", params=payload)
        return response.json()['id']

    def create_card(self, list_id, name, label_id, comment_text, subheadings):
        payload = {**self.auth, "idList": list_id, "name": name, "idLabels": label_id}
        card_res = requests.post(f"{self.base_url}/cards", params=payload)
        card_id = card_res.json()['id']
        
        comment_payload = {**self.auth, "text": comment_text}
        requests.post(f"{self.base_url}/cards/{card_id}/actions/comments", params=comment_payload)
        
        if subheadings:
            check_payload = {**self.auth, "name": "Chapter progress"}
            check_res = requests.post(f"{self.base_url}/cards/{card_id}/checklists", params=check_payload)
            checklist_id = check_res.json()['id']
            
            for item in subheadings:
                item_payload = {**self.auth, "name": item}
                requests.post(f"{self.base_url}/checklists/{checklist_id}/checkItems", params=item_payload)
                
        return card_res.json()


def main():
    if len(sys.argv) < 2:
        print("Usage: python yaml_to_trello.py ")
        sys.exit(1)
        
    yaml_file = sys.argv[1]
    
    with open(yaml_file, "r", encoding="utf-8") as f:
        chapters = yaml.safe_load(f)

    # Pull board and list IDs from environment
    board_id = os.getenv("TRELLO_BOARD_ID")
    list_id = os.getenv("TRELLO_LIST_ID")
    
    if not board_id or not list_id:
        print("Error: Missing TRELLO_BOARD_ID or TRELLO_LIST_ID in .env file.")
        sys.exit(1)

    print("\n--- Book Metadata ---")
    tag_name = input("Tag/Label name (e.g., 'Git'): ")
    book_title = input("Book Name: ")
    edition = input("Edition: ")
    isbn = input("ISBN (optional): ")
    
    comment_text = f"**Source:** {book_title}\n**Edition:** {edition}\n**ISBN:** {isbn}"
    
    trello = TrelloManager()
    
    print("\nPreparing board labels...")
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
            subheadings=chapter.get('subheadings', [])
        )
        
    print("\nSuccess! Trello board populated.")

if __name__ == "__main__":
    main()