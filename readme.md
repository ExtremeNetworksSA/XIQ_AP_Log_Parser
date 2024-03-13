# XIQ AP Log Parser
### XIQ_Log_Parser.py
## Purpose
This script will collect log files for selected APs and look for specific elements with in the log files. The script can save just the log files that include one of the searches or save all log files. the script will output a csv file 'device_report.csv' that will include a list of devices and a column for each search with True or False, if it was found on that device. The script will automatically open this file unless a flag is set to disable.

## Information
##### Collecting Devices
There are multiple options to add devices to the script.

1. Enter names of the devices separated by commas.
2. Collect logs for all APs at a SITE. Enter the name of a Site in XIQ
3. Collect logs for all APs at a BUILDING. Enter the name of a building in XIQ
4. Collect logs for all APs on a FLOOR of a building. Enter the name of a floor and the building it is associated with in XIQ 
5. Upload a txt or csv file with AP names listed. Add the '-a' or '--apFile' with the name of the file. 
    python3 XIQ_Log_Parser.py --apFile ap.csv

##### Collecting Searches
There are 2 ways to add searches for the log files.
1. Typing in the searches. You can do this one at a time when the script prompts. The script will prompt you with "Would you like to search another?" You can add additional searches until you enter 'no' or 'n'
2. Update a text or csv file with the searches listed. Add the '-f' or '--filterFile' with the name of the file.
    python3 XIQ_Log_Parser.py -f filter.csv

#### All Available Flags 
```
python XIQ_Log_Parser.py --help                            
usage: XIQ_Log_Parser.py [-h] [-a APFILE] [-f FILTERFILE] [--fullaplogs] [--foundaplogs] [--noaplogs] [--nocsv] [--noopencsv]

options:
  -h, --help            show this help message and exit
  -a APFILE, --apFile APFILE
                        add csv or text file with AP names on each row
  -f FILTERFILE, --filterFile FILTERFILE
                        add csv or text file with filters on each row
  --fullaplogs          prevents y/n question about storing all logs. Sets to store all log files
  --foundaplogs         prevents y/n question about storing all logs. Sets to store only found log files
  --noaplogs            prevents the saving of any AP log files
  --nocsv               prevents saving results for APs to device_report.csv file
  --noopencsv           prevents opening the csv at script completion
  ```
  You can add multiple flags to the script. For example if you wanted to run the script with no prompts and not open the csv file when complete you would run.
  ```
  python XIQ_Log_Parser.py -a ap.csv -f filt.csv --foundaplogs --noopencsv

## Needed Files
This script uses other files. If these files are missing the script will not function. 
In the same folder as the script, there should be an /app/ folder. Inside of this folder there should be a xiq_logger.py file and a xiq_api.py file.
After running the script, a new folder /script_logs/ will be created under the /app/ folder. This folder will store the logs of the script. 
This log file can be used if an errors are encountered while running the script. 
A new folder /ap_logs/ will be created in the same folder as the script. This folder will store all the log files that are saved by the script.
Lastly, the script will save the device_report.csv file in the same folder as the script.

## Running the script
open the terminal to the location of the script and run this command.
```
python XIQ_Log_Parser.py
```
add any flags to that command

## requirements
There are additional modules that need to be installed in order for this script to function. They are listed in the requirements.txt file and can be installed with the command 'pip install -r requirements.txt' if using pip.