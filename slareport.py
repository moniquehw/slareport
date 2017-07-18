#!/usr/bin/python3
import argparse
from datetime import datetime
from pprint import pprint
import re
import sys

from renderer import SLARenderer
from api_deployments import get_deployments
from client import Client


#### TODO:

    #v2
    #what kind of chart to show the distribution of small/medium/large requests (pie chart?)
    #for response time - what counts as a response? work done, note added etc
    #for distribution of WR types and severity, is this just done with an api call over the wr's listed for that month? (including the 0's?)


    #different report to show how many sla hours used/left and how many have been quoted

    # for a working dev report - make a table for the current month and the month before with WR number, hyperlink, first firew words of brief, sum amount.
    # could have a column for quoted amount and timesheeted amount, and total hours used for that month.
    # instead of taking the lump sum off straight away, add it up as it goes and say when it has reached the number quoted. if it goes over, make red :)
    #at bottom, 2 totals - total timesheeted and total quoted

    #noapi argv - readme file and argv help
    # check if any of the wr numbers for the deployments match, then print out an error at the end (or a warning on the report - name it differently?)

    #https://blog.oio.de/2010/05/14/embed-an-image-into-an-openoffice-org-writer-document/

    # Argv - set default to org.csv, and a 3rd argv uses that file name instead.
    #Argv usage instructions should be better. (It can't tell which arg is missing if they aren't all there, and doesn't print help file every time it should)
    # Save reports into a report folder

#argv connect url. Run in seperate terminal - soffice --writer --accept="socket,host=localhost,port=2002;urp;StarOffice.ServiceManager"


def time_spread(client):
    """takes a wr and puts it into the category of small, medium or large for the amount of time spent on them"""
    small = [] #0-2 hours
    medium = [] #2-8 hours
    large = [] #>8 hours
    #for wr in client['months_data']['wrs']


def update_deployment_list(client):
    pprint.pprint(client)
    if sys.argv[3] != 'noapi':
        deployment_list = get_deployments(sys.argv[3], client['date'], client['deployment_head_wr'])
        for deployment in deployment_list:
            client['list_of_production_changes'].append(deployment)
            date = deployment['date'].strftime("%d %B %Y")
            deployment['date'] = date
            deployment['request_id'] = str(deployment['request_id'])
            for deployed_wrs in deployment['deployed_wrs']:
                deployed_wrs['request_id'] = str(deployed_wrs['request_id'])

    if client['hosting'] is True and client['list_of_production_changes'][0] != "None":
        slist = sorted(client['list_of_production_changes'], key=lambda d:("date" not in d, d.get("date")))
        client['list_of_production_changes'] = slist


def solve(s):
    """ Takes a date with 'st', 'nd', 'rd, or 'th' on the end (such as July 1st 2017), and turns it into a datetime format"""
    return re.sub(r'(\d)(st|nd|rd|th)', r'\1', s)


def check_sla_date(client):
    """Checks to see if the SLA has expired via the data in the config file. Asks for user input to continue or exit if the report month is for a month not covered by the current SLA (according to the config file)
    """
    date = datetime.strptime(solve(client.config['sla_end_date']), "%B %d %Y")
    if client.date > date:
        check = input('The SLA for the organisation you are trying to run a report on has expired. Either the config file is out of date or you have entered the incorrect month. Would you like to continue? y/n? ')
        if check.lower() == 'n':
            print ('Exiting program...')
            sys.exit(-1)

if __name__ == '__main__':
    check =  input('Before creating reports, run get_data_from_csv.py first to update csv files. Have you done this? y/n? ')
    if check.lower() == 'n':
        print ('Exiting program...')
    else:
        argparser = argparse.ArgumentParser()
        argparser.add_argument("client", help="lowercased short name of the client")
        argparser.add_argument("date", help="date - for example march17")
        argparser.add_argument("token", help="api token")#api token. If using config data for platform statistics instead of an api call, token is None
        argparser.add_argument("--norender", action="store_true", help="Don't render the report")
        args = argparser.parse_args()
        auth_token = args.token

        filename = sys.argv[1] + '-' + sys.argv[2] + '.json'
        client = Client(sys.argv[1], filename, sys.argv[3])
        client.initialise_data()
        check_sla_date(client)
        if not args.norender:
            renderer = SLARenderer(client)
            renderer.render()
