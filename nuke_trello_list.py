"""
Script to permanently delete all cards from a specified Trello list.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Pull credentials from the same hidden file
load_dotenv(dotenv_path=".secrets")

def main():
    """
    Reads Trello API credentials and list ID from the .secrets file,
    fetches all cards in the list, and prompts the user for confirmation
    before permanently deleting them.
    """
    api_key = os.getenv("TRELLO_API_KEY")
    token = os.getenv("TRELLO_TOKEN")
    list_id = os.getenv("TRELLO_LIST_ID")
    
    if not all([api_key, token, list_id]):
        print("Error: Missing API Key, Token, or List ID in .secrets file.")
        sys.exit(1)
        
    base_url = "https://api.trello.com/1"
    auth = {"key": api_key, "token": token}
    
    print("Connecting to Trello to assess the damage...")
    
    # Fetch all cards currently sitting in the "Automated TODO" list
    url = f"{base_url}/lists/{list_id}/cards"
    response = requests.get(url, params=auth)
    cards = response.json()
    
    if not cards:
        print("The list is already completely empty. Nothing to nuke.")
        return
        
    print(f"\nFound {len(cards)} cards in the target list.")
    
    # The Fail-Safe Confirmation
    confirm = input("Are you absolutely sure you want to PERMANENTLY delete these cards? (y/N): ")
    
    if confirm.strip().lower() != 'y':
        print("\nAbort sequence confirmed. Your cards are safe.")
        return
        
    print("\nInitiating hard-delete sequence...\n")
    
    # Loop through and permanently delete each card
    for card in cards:
        card_id = card['id']
        card_name = card['name']
        
        print(f"Deleting -> {card_name}")
        requests.delete(f"{base_url}/cards/{card_id}", params=auth)
        
    print("\nPurge complete. Your 'Automated TODO' list is wiped clean.")

if __name__ == "__main__":
    main()