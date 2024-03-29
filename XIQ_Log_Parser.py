#!/usr/bin/env python3
import argparse
import os
import sys
import getpass
import logging
import re
import subprocess
import pandas as pd
from app.xiq_api import XIQ
from app.xiq_logger import logger
logger = logging.getLogger('AP_log_parser.Main')
from pprint import pprint as pp

PATH = os.path.dirname(os.path.abspath(__file__))

# Git Shell Coloring - https://gist.github.com/vratiu/9780109
RED   = "\033[1;31m"
GREEN = "\033[0;32m" 
RESET = "\033[0;0m"

parser = argparse.ArgumentParser()
parser.add_argument('-a','--apFile',type=str, help="add csv or text file with AP names on each row")
parser.add_argument('-f','--filterFile', type=str, help="add csv or text file with filters on each row")
parser.add_argument('--fullaplogs',action="store_true",help="prevents y/n question about storing all logs. Sets to store all log files")
parser.add_argument('--foundaplogs',action="store_true",help="prevents y/n question about storing all logs. Sets to store only found log files")
parser.add_argument('--noaplogs',action="store_true",help="prevents the saving of any AP log files")
parser.add_argument('--nocsv',action="store_true",help="prevents saving results for APs to device_report.csv file")
parser.add_argument('--noopencsv',action="store_true", help="prevents opening the csv at script completion")
args = parser.parse_args()


## TOKEN permission needs - device:r, locations:r, account:r, account:switch, lro:r
XIQ_token = ''

def yesNoLoop(question):
    validResponse = False
    while validResponse != True:
        response = input(f"{question} (y/n) ").lower()
        if response =='n' or response == 'no':
            response = 'n'
            validResponse = True
        elif response == 'y' or response == 'yes':
            response = 'y'
            validResponse = True
        elif response == 'q' or response == 'quit':
            sys.stdout.write(RED)
            sys.stdout.write("script is exiting....\n")
            sys.stdout.write(RESET)
            logger.debug("User selected to quit in the yes/no loop")
            raise SystemExit
    return response


def manuallyCollectDevices(x):
    # Prompt for devices based on location or manually typing name
    print("How would you like to enter the devices?")
    validResponse = False
    while not validResponse:
        print("1. Enter names of the devices separated by commas.")
        print("2. Collect logs for all APs at a SITE.")
        print("3. Collect logs for all APs at a BUILDING.")
        print("4. Collect logs for all APs on a FLOOR of a building.")
        selection = input("Please enter 1 - 4: ")
        print()
        try:
            selection = int(selection)
        except:
            logger.warning("Please enter a valid response!!")
            print()
            continue
        
        #if User selects 1
        if selection == 1:
            validResponse = True
            # AP list separated by comma
            ap_list = input("Please enter a list of APs separated by commas: ")
            print()
            try:
                aps = [x.strip() for x in str(ap_list).split(',')]
                validResponse = True
                devices = x.collectDevices(pageSize=100, hostname=aps)
                logger.info(f"{len(devices)} APs were found")
                print()
            except:
                logger.warning(f"Unable to split line {ap_list} by comma. Please try again.")
            # check for APs that were not found in XIQ
            found_ap_list = [x['hostname'] for x in devices]
            missing_aps = set(aps).difference(found_ap_list)
            # If missing APs were found send message to screen and log
            if missing_aps:
                logger.warning(f"The following APs were not found: " + ", ".join(missing_aps))
                print()
        
        #if User selects 2
        if selection == 2:
            site_name = input("Enter the name of the site you would like to collect devices from: ")
            print()
            try:
                devices = x.DevicesFromSite(name=site_name)
                logger.info(f"{len(devices)} APs were found in site {site_name}")
                print()
                validResponse = True
            except ValueError as e:
                logger.error(str(e))
                print()
        
        #if User selects 3
        if selection == 3:
            building_name = input("Enter the name of the building you would like to collect devices from: ")
            print()
            try:
                devices = x.DevicesFromBuilding(name=building_name)
                logger.info(f"{len(devices)} APs were found in building {building_name}")
                print()
                validResponse = True
            except ValueError as e:
                logger.error(str(e))
                print()
        
        #if User selects 4
        if selection == 4:
            validResponse = True
            building_name = input("Enter the name of the building the floor is part of: ")
            floor_name = input("Enter the name of the Floor in the building: ")
            print()
            try:
                devices = x.DevicesFromFloor(building_name=building_name,floor_name=floor_name)
                logger.info(f"{len(devices)} APs were found on floor {floor_name} in building {building_name}")
                print()
                validResponse = True
            except ValueError as e:
                logger.error(str(e))
                print()
    return devices
        

def main():
    # dictionary to store results of APs
    device_checks = []

    if not args.noaplogs:
        # check for logs directory and create if missing
        os.makedirs('{}/ap_logs'.format(PATH), exist_ok=True) 
        ap_log_dir = '{}/ap_logs'.format(PATH)
    ## XIQ EXPORT
    if XIQ_token:
        x = XIQ(token=XIQ_token)
    else:
        print("Enter your XIQ login credentials")
        username = input("Email: ")
        password = getpass.getpass("Password: ")
        x = XIQ(user_name=username,password = password)

    # collect AP names from file
    if args.apFile:
       with open(args.apFile, 'r') as f:
            aps = f.read().splitlines()
            devices = x.collectDevices(pageSize=100, hostname=aps)
            logger.info(f"{len(devices)} APs were found {args.apFile}")
            print()
    else:
        devices = manuallyCollectDevices(x)
        
    if not devices:
        logger.warning("No devices found.")
        print("script is exiting...")
        raise SystemExit
    
    # Create dataframe for AP name lookup
    device_df = pd.DataFrame(devices)
    device_df.set_index('id',inplace=True)

    device_ids = [d['id'] for d in devices]

    
    if args.filterFile:
        with open(args.filterFile, 'r') as f:
            log_checks = f.read().splitlines()
    else:
        collect_filters = True
        # user input single search
        log_checks = [input("Please enter string you would like to search the logs for: (NOTE: amount of spaces between words will be ignored) ")]
        
        # allows to add additional searches
        while collect_filters:
            response = yesNoLoop("Would you like to search another?")
            if response == 'y':
                log_checks.append(input("Add another string to search: ")) 
            elif response == 'n':
                collect_filters = False

    
    logger.info(f"Searching logs for {len(log_checks)} items.")
    print()
    logger.debug("List of filters: \n\t-> " + "\n\t-> ".join(log_checks))
    if not args.noaplogs:
        if args.fullaplogs:
            save_all_logs = True
        elif args.foundaplogs:
            save_all_logs = False
        else:
            # ask to save logs
            response = yesNoLoop("Would you like to save all log files to '/ap_logs/' even if the search is not found?")
            if response == 'y':
                save_all_logs = True
            elif response == 'n':
                print("only logs where search is found will be stored.")
                save_all_logs = False
    else:
        print("No AP logs will be stored due to the --noaplogs flag")
        save_all_logs = False

    sys.stdout.write(GREEN)
    sys.stdout.write("Starting to collect logs. This may take a few minutes...\n")
    sys.stdout.write(RESET)
    
    # collect Log files
    logs = x.sendCLI(device_ids, ['show log buffered'])
    # Error and exit if cli output not in responses
    if "device_cli_outputs" not in logs:
        logger.error("CLI output was not found in results!")
        print("Script is exiting...")
        raise SystemExit
    # get count of successful logs
    log_count = len(logs['device_cli_outputs'])
    logger.info(f"{log_count} logs were collected")
    print()


    for key in logs['device_cli_outputs']:
        # Get name of AP from id
        ap_name = device_df.loc[int(key),'hostname']
        ap_data = {
            "ap_name": ap_name,
            "serial_number": key
                   }
        log_saved = False
        if not args.noaplogs and save_all_logs:
            # save log file 
            with open(f"{ap_log_dir}/{ap_name}.log", 'w') as f:
                for line in logs['device_cli_outputs'][key][0]['output'].splitlines(True): 
                    f.write(line)
            logger.info(f"Added {ap_name}.log to /ap_logs/")
            log_saved = True
        for log_check in log_checks:
            ap_data[log_check] = False
            # search logfile for 
            re_log_check = r"\s+".join(log_check.strip().split())
            regex = re.compile(re_log_check)
            found = regex.findall(logs['device_cli_outputs'][key][0]['output'])
            if found:
                ap_data[log_check] = True
                logger.critical(f'"{log_check}" was found in logs of device {ap_name}')
                # save log file 
                if not args.noaplogs and not log_saved:
                    with open(f"{ap_log_dir}/{ap_name}.log", 'w') as f:
                        for line in logs['device_cli_outputs'][key][0]['output'].splitlines(True): 
                            f.write(line)
                    logger.info(f"Added {ap_name}.log to /ap_logs/")
            elif save_all_logs:
                sys.stdout.write(GREEN)
                sys.stdout.write(f"{log_check} was not found on AP {ap_name}\n")
                sys.stdout.write(RESET)
        device_checks.append(ap_data)
    
    if not args.nocsv:
        output_file = f'{PATH}/device_report.csv'

        # save results to csv
        pd.DataFrame(device_checks).to_csv(output_file, index=False)
        if not args.noopencsv:
            if sys.platform == "darwin":
                subprocess.call(["open", output_file])
            elif sys.platform == "win32":
                os.startfile(output_file)
            else:
                subprocess.call(["xdg-open", output_file])
        
if __name__ == '__main__':
    main()