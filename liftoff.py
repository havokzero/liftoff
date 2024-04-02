import os
import random
import shutil
import logging
import phonenumbers
import asyncio
import aiofiles
import subprocess
import re

# Setup basic logging
logging.basicConfig(filename='call_placement.log', level=logging.INFO, format='%(asctime)s %(message)s')

def generate_phone_number(area_code=None):
    area_code_part = area_code if area_code else random.choice('23456789') + ''.join(random.choice('0123456789') for _ in range(2))
    prefix = random.choice('23456789') + ''.join(random.choice('0123456789') for _ in range(2))
    subscriber_number = ''.join(random.choice('0123456789') for _ in range(4))
    return f"1{area_code_part}{prefix}{subscriber_number}"

def validate_and_format_phone_number(phone_number):
    try:
        phone_number = phone_number.lstrip('+').lstrip('1')
        parsed = phonenumbers.parse(phone_number, "US")
        if phonenumbers.is_valid_number(parsed):
            return '1' + phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL).replace(' ', '').replace('(', '').replace(')', '').replace('-', '')
    except phonenumbers.NumberParseException as e:
        print(f"Number parse exception: {e}")
        return None
    return None

# Regex patterns
channel_pattern = re.compile(r'(Channel: PJSIP/)\d+(@Bulk_Flood)')
caller_id_pattern = re.compile(r'(CallerID: "?)\d+("?)')

async def process_call(source_file, destination_dir, dialed_number, caller_id, iteration, delay):
    logging.info(f"Call {iteration}: Dialing {dialed_number} with Caller ID {caller_id}")
    temp_file_path = f"/tmp/callfile_{iteration}.call"
    final_file_path = os.path.join(destination_dir, f"callfile_{iteration}.call")

    shutil.copy(source_file, temp_file_path)

    try:
        async with aiofiles.open(temp_file_path, 'r+') as temp_file:
            content = await temp_file.read()
            content = channel_pattern.sub(r'\g<1>' + dialed_number + r'\g<2>', content)
            content = caller_id_pattern.sub(r'\g<1>' + caller_id + r'\g<2>', content)

            await temp_file.seek(0)
            await temp_file.write(content)
            await temp_file.truncate()

        shutil.move(temp_file_path, final_file_path)
        subprocess.run(['chown', 'asterisk:asterisk', final_file_path], check=True)
        subprocess.run(['chmod', '777', final_file_path], check=True)

        logging.info(f"Call file {final_file_path} processed and moved successfully.")
        await asyncio.sleep(delay)
    except Exception as e:
        logging.error(f"Error processing call file {iteration}: {e}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

async def create_calls_concurrently(source_file, destination_dir, num_calls, target_number, caller_id, delay):
    logging.info(f"Starting to create {num_calls} call(s) to {target_number} with Caller ID {caller_id}.")

    tasks = []
    for i in range(num_calls):
        try:
            task = process_call(source_file, destination_dir, target_number, caller_id, i, delay)
            tasks.append(task)
            logging.info(f"Prepared to place call {i+1}/{num_calls}: Dialing {target_number} with Caller ID {caller_id}.")
        except Exception as e:
            logging.error(f"Error preparing call {i+1}: {e}")

    if tasks:  # Proceed if there are any tasks prepared
        await asyncio.gather(*tasks)
        logging.info(f"{len(tasks)} call(s) have been initiated successfully.")
    else:
        logging.warning("No calls were initiated due to preparation errors.")

    # This will ensure even if tasks list is empty due to errors, it will be logged accordingly.


async def hangup_all_calls():
    try:
        process = await asyncio.create_subprocess_shell("asterisk -rx 'channel request hangup all'", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            logging.info("All calls have been hung up successfully.")
        else:
            logging.error(f"Failed to hang up calls: {stderr.decode().strip()}")
    except Exception as e:
        logging.error(f"Error hanging up calls: {e}")

def get_user_caller_id_choice():
    print("\nCaller ID Options:")
    print("1 - Specify complete Caller ID")
    print("2 - Specify just the area code and randomize the rest")
    print("3 - Randomize the entire Caller ID")
    choice = input("Choose how to set the Caller ID: ").strip()
    if choice == '1':
        full_number = input("Enter the full Caller ID number: ").strip()
        return validate_and_format_phone_number(full_number)
    elif choice == '2':
        area_code = input("Enter the 3-digit area code: ").strip()
        return generate_phone_number(area_code)
    elif choice == '3':
        return generate_phone_number()
    else:
        print("Invalid option.")
        return None

async def main():
    source_file = 'callfile.bak'
    destination_dir = '/var/spool/asterisk/outgoing'

    while True:
        print("\nOptions:")
        print("1 - Initiate Calls")
        print("2 - Hang Up All Calls")
        print("3 - Exit Program")
        user_choice = input("Select an option: ").strip()

        if user_choice == "1":
            caller_id = get_user_caller_id_choice()
            if not caller_id:
                continue

            target_number_input = input("Enter the phone number to call: ").strip()
            target_number = validate_and_format_phone_number(target_number_input)
            if not target_number:
                print("Invalid phone number.")
                continue

            num_calls_input = input("How many calls do you want to place?: ").strip()
            num_calls = int(num_calls_input) if num_calls_input.isdigit() else 0
            if num_calls <= 0:
                print("Invalid number of calls.")
                continue

            delay = float(input("Enter the delay between calls (in seconds): ").strip())

            await create_calls_concurrently(source_file, destination_dir, num_calls, target_number, caller_id, delay)

        elif user_choice == "2":
            await hangup_all_calls()

        elif user_choice == "3":
            print("Exiting program.")
            break

        else:
            print("Invalid option. Please select 1, 2, or 3.")

if __name__ == "__main__":
    asyncio.run(main())
