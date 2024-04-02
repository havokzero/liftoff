import subprocess
import logging
from asterisk.agi import AGI

# Setup logging
logging.basicConfig(filename='cid_manager.log', level=logging.INFO, format='%(asctime)s %(message)s')

def update_caller_id(extension, caller_id):
    """
    Updates the caller ID for a specific extension in the Asterisk configuration.
    """
    try:
        # Construct the command to change the caller ID in the Asterisk database
        # This uses the 'database put' command to update the CID name and number
        name_command = f'asterisk -rx "database put AMPUSER {extension}/cidname {caller_id}"'
        num_command = f'asterisk -rx "database put AMPUSER {extension}/cidnum {caller_id}"'
        subprocess.run(name_command, shell=True, check=True)
        subprocess.run(num_command, shell=True, check=True)

        # Reload the Asterisk configuration to apply changes
        subprocess.run(['fwconsole', 'reload'], shell=True, check=True)

        logging.info(f"Caller ID for extension {extension} updated to {caller_id} and changes applied successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to update Caller ID for extension {extension}: {e}")
        return False

def main():
    agi = AGI()
    extension = agi.env['agi_extension']
    # Assuming caller_id is passed as an argument or fetched from the AGI script's environment
    caller_id = agi.get_variable('CALLERID')  # Adjust if needed based on how you want to set caller ID

    if update_caller_id(extension, caller_id):
        agi.verbose("Caller ID updated successfully.")
    else:
        agi.verbose("Failed to update Caller ID.")

if __name__ == "__main__":
    main()
