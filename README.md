# Usage instructions

## Organisation names

All of the organisations are called using their short names in lower case - eg, 'University of Sample' is 'sample', and 'Random Organisation Name' is 'ron'


## New organisation

To add a new organisation, create a folder inside the clients directory and name it as the short name for the org (eg sample or ron)
Create two config files for the org inside this folder (use the sample config files and fill in the correct data.) Copy the naming format for these files from the other organisations if you have access to them. The files will be called 'short_name' + '.json' (eg ron.json) and 'short_name' + '-' + monthYY + '.json' (eg ron-june17.json for the June 2017 report for the Random Organisation Name). It is important that these are named correctly.

If the new organisation has a hosting system (or you still want to include their hosting/deployment data in your report), duplicate sample.json and sample-month17.json (from the example folder)
If the new organisation has no hosting system (or you don't want any hosting information included in your report), duplicate sample.json and change the hosting field to 'false', and duplicate sample2_month17.json
For hosting data but no deployment data, duplicate sample.json and sample_month.json and follow the instructions further down in the readme.


## Populate the list of organisations to run reports on

Copy the config.py file from the example directory into the clients directory.
This file is just 2 lists - org_list and sla_list
Add the short name of any organisations you would like to get csv data for. If the organisation will have a monthly sla report generated for it, add their short name to the sla list. Otherwise, add the name to the org_list.
If you add an org name here that does not also have a config file and a monthly config file, you will receive an error - it will not fetch data for any organisations that are missing these 2 config files.
If you like, you can skip this step and instead of adding the organisations to these lists, run the get_csv_data on 1 organisation at a time using an argument on the command line.


## Before running reports

### Data that has to be gathered from other sources

* From the person sending the reports/a PM: Executive summary.
* From sysadmins (for the organisations we host):
    * Disk storage used
    * Uptime
    * Out of hours events

### Organisation config file

Each organisation must have a config file (example/sample.json). This file has base data about the organisation that doesn't change.
* org_name: the short name for the organisation, 1 word with no capitals (eg for the University of Sample, the org_name = sample)
* service name and client name are the full names of the organisation and service (with capitals and spaces) that will be displayed in the report
* rounding: round time up to the nearest... (eg 0.5 = half an hour. This is the default for most orgs)
* url: the url that the program is getting csv data from. This can only be accessed from within Catalyst. This means that you cannot retrieve csv data for the organisations if you are not on the Catalyst network
* hosting: if you want a hosting table to display in the report, hosting should be set to true (no capitals).
* hosting_hours_additional: if this is set to true, hours in the hosting system will count as additional SLA hours for this organisation. This will normally be set to false.
* system: details on the system you are reporting on
* deployment_head_wr: this is the wr number for the head deployments wr. If you don't want to display any hosting data, it doesn't matter what this is. It will be ignored.


### Monthly config file

Each month, a new config file must be added for each organisation.
To create this, either copy the one from the previous month or duplicate the sample-month17.json file and rename it appropriately (with the month name and year that the report is for - eg sample-june17.json for the June 2017 report for the University of Sample).
It is important to name this correctly - ensure the name is all in lower case. The sla_report.py program will tell you if there is no config file for the month and organisation you are trying to run a report on (ie, if it is not there or it is named incorrectly).
Populate this config file with the correct data for the report month:
* 'storage_used' and 'ooh' will output as bulleted lists if there is more than 1 item in them ('ooh' stands for 'out of hours events').
* 'additional_hours_override' and 'sla_hours_override' must be left at 0 unless you want to manually enter the numbers for this month's graph

* The production_changes field is for the monthly deployments and will be populated by an api call (unless you opt not to use api), so these do not need to be entered. Leave it as an empty list if you have no additional information.
However, you may enter any additional deployment data here (as well as anything that the api call misses). Take care of all the json formatting or you will receive a json error. This field is a list of dictionaries and each dictionary has the data for one deployment. The wr field for that deployment is another list of dictionaries, so check that all the dictionary and list paramaters are in the right place if you decide to manually enter anything here. Check the sample_deployments.json file if you are unsure of the formatting.


## To run reports

1.  To get csv data for the organisations:
    Run the get_csv_data.py file.

    Because they will rarely change, the list of organisations to fetch data for is hard coded into the clients/config.py file (org_list and sla_list). Run with no other arguments in the command line, the program will fetch data for the organisations in both those lists (if the organisations have a config file). Make sure this file exists (further instructions for this are under: Populate the list of organisations to run reports on).

    To just fetch data on a specific organisation, or to just fetch data for the SLA reports, use arguments in the command line (you can enter as many organisations here as you want).
    eg, to just get a csv file for sample, run:
    ```get_csv_data.py sample```
    and to just get data for the list of organisations in the sla list (in clients/config.py), run:
    ```get_csv_data.py sla```

    The data will be saved in the folder for that directory as a .csv file (eg .../sla_reports/clients/ron/ron.csv)
    If you would like to manually check over the data before running a report, open this .csv file. The data is sorted by month, with the most recent month at the bottom (which is not necessarily the reporting month).

2.  Before generating reports:
    Open a new terminal.
    Run this in the command line: ```soffice --writer --accept="socket,host=localhost,port=2002;urp;StarOffice.ServiceManager"```.
    A blank libreoffice document will open. Both this and the terminal must stay open in order for reports to write to a document. If either of them are closed, a connection error will occur. Simply rerun the code in the command line to fix this, and ensure that both this 2nd terminal and the blank document are not closed.

3.  Run the report 1 of 2 ways:
    1.  Using an api call to populate the list of production changes (deployment data):

        * Open the catalyst API website (https://wrms.catalyst.net.nz/api2/explorer) and login. Copy the API token (which is the long number+letter token under 'Session ID'). If the program fails to connect to the API, refresh this page and try logging in again.

        * Run sla_reports.py.
        The program requires these command line parameters (there is a command line help file in the program which will tell you if you are missing any parameters):
        organisation short name, monthYY, and the API token copied in the step above

        So to generate a report for the University of Sample for the month of April in 2017, (using the API token of 1234abc567), run:
        ```./sla_report.py sample april17 1234abc567```

    2.  Without using the api call (the list of production changes will just come from whatever you have put in that month's config file):
        Run sla_report.py with the first 2 command line parameters the same, and 'noapi' instead of the api token.
        eg:
        ```./sla_report.py sample april17 noapi```

4.  Making changes:
    Whilst it may only take a second to make minor changes to the reports, it will often still be faster to correct the data in the config or  and simply run the report again, as the sla_report program will (hopefully) fix all of the formatting and insert any necessary hyperlinks for you.

    If you would like to create a new graph with a different number of hours (you can only change the current month without editing previous months in the csv file). In the monthly config file, you can override the number of SLA hours and Additional hours being represented in the graph. Just enter the TOTAL number of hours for that month in either the field for sla_hours_override, or additional_hours_override. If you would like to still use the number of hours being generated by the report for either of these fields, leave this number as 0. There is no addition being done here, these numbers will simply override the previous total.

5.  Opening saved reports:
    The report will save into the organisation's folder in the clients directory (alongside the config and csv files). For the University of Sample in June 2017, the report will be in: .../sla_reports/sample/sample_June 2017.odt.
    The graph inside the report will not stay attached if you try to send it - you must first convert the report into a .pdf file.


## ERRORS

* Most errors should be self explanatory, and the result of incorrect WRMS or config data.
* A json error is almost definitely going to be a missing bracket or comma in the monthly config json file - just correct the mistake and run the report again. If you are unsure what is wrong, compare your config file to the sample_config.json file
* The second most likely error will be data entered into the config file in the incorrect format - some of the fields that almost always have 'None' in them are still lists, to allow for the slight possibility that multiple items are entered there. Check with the sample config file to see which ones are supposed to be lists (ie, inside of square brackets with the list items seperated by a comma).
* The sla_report.py program will list the deployment WR's in the terminal as it goes through them in WRMS. If there is an error with one, just double check the wr number in wrms. The most likely issue will be if the deploymenet date is entered into wrms using an unusual format. The easiest way to fix this is to correct the mistake in WRMS and run the report again.
