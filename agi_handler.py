import logging
import requests

# Setup logging
logging.basicConfig(filename='cid_manager.log', level=logging.INFO, format='%(asctime)s %(message)s')

api_url = 'https://DOMAIN/admin/api/'
api_token = 'SERVER_TOKEN'

# Headers for API authentication
headers = {
    'Authorization': f'Bearer {api_token}'
}

def update_caller_id(extension, caller_id):
    """
    Updates the caller ID for a specific extension using the FreePBX REST API.
    """
    try:
        # Prepare data for updating the caller ID
        update_data = {'cidname': caller_id, 'cidnum': caller_id}

        # Send request to FreePBX API to update the caller ID
        response = requests.put(f'{api_url}/extensions/{extension}', headers=headers, data=update_data)

        if response.status_code == 200:
            logging.info(f"Caller ID for extension {extension} updated to {caller_id} and changes applied successfully.")
            return True
        else:
            logging.error(f"Failed to update Caller ID for extension {extension}: HTTP {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Exception while updating Caller ID for extension {extension}: {e}")
        return False

def get_caller_id(extension):
    """
    Fetches the current caller ID settings for a specific extension using the FreePBX REST API.
    """
    try:
        # Send request to FreePBX API to get the caller ID info
        response = requests.get(f'{api_url}/extensions/{extension}', headers=headers)

        if response.status_code == 200:
            caller_id_info = response.json()
            cid_name = caller_id_info.get('cidname')
            cid_number = caller_id_info.get('cidnum')
            logging.info(f"Fetched Caller ID for extension {extension}: {cid_name} ({cid_number})")
            return cid_name, cid_number
        else:
            logging.error(f"Failed to fetch Caller ID for extension {extension}: HTTP {response.status_code}")
            return None, None
    except Exception as e:
        logging.error(f"Exception while fetching Caller ID for extension {extension}: {e}")
        return None, None

# Test functions if running as a script
if __name__ == "__main__":
    extension_test = '100'  # Example extension to test
    caller_id_test = 'John Doe <100>'

    print("Getting current Caller ID:")
    name, number = get_caller_id(extension_test)
    print(f"Current Caller ID: {name} ({number})")

    print("\nUpdating Caller ID:")
    if update_caller_id(extension_test, caller_id_test):
        print("Caller ID update successful.")
        name, number = get_caller_id(extension_test)
        print(f"Updated Caller ID: {name} ({number})")
    else:
        print("Failed to update Caller ID.")
