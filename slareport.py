#!/usr/bin/python3
import argparse
import json
from datetime import datetime
import sys
import os
import math
from renderer import SLARenderer
from csv_data import get_sla_data
import re
from api_deployments import get_deployments

#### TODO:

    #round each wr to nearest half hour
    # change hosting to true or false, lower case. fix in sla report

    #noapi argv - readme file and argv help
    # check if any of the wr numbers for the deployments match, then print out an error at the end (or a warning on the report - name it differently?)
    #try and except if it cant convert the wr number (ie its written wrong in wrms)
    #https://blog.oio.de/2010/05/14/embed-an-image-into-an-openoffice-org-writer-document/

    # Argv - set default to org.csv, and a 3rd argv uses that file name instead.
    #Argv usage instructions should be better. (It can't tell which arg is missing if they aren't all there, and doesn't print help file every time it should)
    # Save reports into a report folder
    #testing/debugging - make a try and except for a connect error, telling user to connect in seperate terminal if it doenst work.

    #make client dictionary a class


#argv connect url. Run in seperate terminal - soffice --writer --accept="socket,host=localhost,port=2002;urp;StarOffice.ServiceManager"


def round_up_to(number, accuracy):
    """ Round a number up to the closest accuracy
    Args:
        number: int, float - The number to round
        accuracy - The accuracy you want
    Returns:
        float
    Example: round_up_to(2.67, 0.5) = 3.0
             round_up_to(2.67, 0.25) = 2.75
    """
    return math.ceil(number /accuracy) * accuracy


def put_data_into(client):
    """ Takes data from config files and WRMS, and updates the client dictionary with it
    """

    client.update(get_data_from_config(client['name']))
    client['deployment_head_wr'] = int(client['deployment_head_wr'])

    #Makes last_modified the current date
    client['last_modified'] = datetime.now().strftime('%Y-%m-%d')

    client.update(get_month_config(client['short_name'] + '/' + sys.argv[1] + '-' + sys.argv[2]))

    client['sla_list'] = get_data_from_csv(client)
    # TODO: Create a new WorkRequest object for each work request
    client['all_months'] = client['sla_list'].months

    split_date(client)

    csv_date = "{}-{}".format( client['date'].year, client['date'].month) # date_to_csv_date(client['month'], client['year'])

    update_deployment_list(client)

    get_month_data_from_csv(client, csv_date)

    sla_hours(client)

    sort_quotes(client)

    client['total_non_quoted_sla'] = get_total_hours(client['non_quoted_sla'])
    client['total_quoted_sla'] = get_total_hours(client['quoted_sla'])
    client['total_quoted_non_sla'] = get_total_hours(client['quoted_non_sla'])

    check_sla_date(client)

    summary_data = []
    for m in client['all_months']:
        my_month = {'name': m['month'].strftime("%b %y")}
        hours = extract_hours(m)
        my_month['sla'] = get_total_hours(hours['non_quoted_sla']) + get_total_hours(hours['quoted_sla'])
        my_month['non_sla'] = get_total_hours(hours['quoted_non_sla'])
        summary_data.append(my_month)
    #my_month['non_sla'] = 17 #manually insert number of additional hours to redo the graph
    if client["additional_hours_override"] != 0:
        my_month['non_sla'] = client["additional_hours_override"]
    if client['sla_hours_override'] !=0:
        my_month['sla'] = client['sla_hours_override']
    client['lifetime_summary'] = summary_data

    recipient_list = bullet_point_list(client['recipients'])
    client['recipients'] = "\n".join(recipient_list)

def update_deployment_list(client):
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


def get_data_from_csv(client):
    sla_list = get_sla_data(os.getcwd() + "/clients/" + client['short_name'] + '/' + client['short_name'] + '.csv')
    return sla_list


def get_month_data_from_csv(client, csv_date):
    #sla_list = get_sla_data('client['short_name'] + '.csv')
    months_data = client['sla_list'].get_month(client['date'])
    client['months_data'] = months_data
    return months_data


def get_lifetime_summary(client):
    months = client['all_months']
    results = []
    for m in months:
        month_dict = {"month_name": m['month']}
        m.update(extract_hours(m))
        month_dict['total_non_quoted_sla'] = get_total_hours(m['non_quoted_sla'])
        month_dict['total_quoted_sla'] = get_total_hours(m['quoted_sla'])
        month_dict['total_quoted_non_sla'] = get_total_hours(m['quoted_non_sla'])
        results.append(month_dict)
    return results


def sla_hours(client):
    """ Takes WR data and updates the client dictionary with the data sorted into quoted sla, non quoted sla and quoted non sla """
    results = extract_hours(client['months_data'])
    client.update(results)


def extract_hours(month):
    quoted_non_sla = []
    quoted_sla = []
    non_quoted_sla = []
    for wr in month['wrs']:
        if client['hosting_hrs_additional'] and "Hosting" in wr['system']:
            quoted_non_sla.append(wr)
        elif len(wr['quotes']) > 0: # if there's a quote
            if wr['quotes'][0]['status'] == 'Approved':   #if the quote is approved
                if wr['quotes'][0]['sla'] is False:
                    quoted_non_sla.append(wr)
                else:
                    quoted_sla.append(wr)
            else:
                if wr['quotes'][0]['sla'] is False:
                    quoted_non_sla.append(wr)
                else:
                    quoted_sla.append(wr)
        else:
            non_quoted_sla.append(wr)
    results = {
        'quoted_non_sla': quoted_non_sla,
        'quoted_sla': quoted_sla,
        'non_quoted_sla': non_quoted_sla,
    }
    return results


def sort_quotes(client):
    """ Update the timesheeted hours for each WR to take into account previous months work

    """
    quoted_non_sla = {}
    quoted_sla = {}

    report_month = client['date']

    for month in client['all_months']:
        if month['month'] > report_month:
            break
            sys.exit(-1)
        for wr in month['wrs']:
            if client['hosting_hrs_additional'] and 'Hosting' in wr['system']:
                 # if the wr is in a hosting system and hosting counts towards sla hours
                 pass
            elif wr['request_id'] in quoted_non_sla or wr['request_id'] in quoted_sla:
                # If the wr was quoted in the previous months, then ignore it
                wr['timesheets'] = 0
            elif len(wr['quotes']) > 0: # if there's a quote
                if wr['quotes'][0]['status'] == 'Approved':   #TODO where should non-appproved quotes go?
                    if wr['quotes'][0]['sla'] is False: #approved and not sla
                        quoted_non_sla[wr['request_id']] = wr['quotes'][0]['orig'][4]
                    else:#approved and sla
                        quoted_sla[wr['request_id']] = wr['quotes'][0]['orig'][4]
                    wr['timesheets'] = float(wr['quotes'][0]['orig'][4])
                else:
                    if wr['quotes'][0]['sla'] is False:#quoted, not approved not sla
                        quoted_non_sla[wr['request_id']] = 0 # wr['quotes'][0]['orig'][4]
                    else: #quoted, not approved sla
                        quoted_sla[wr['request_id']] = 0 # wr['quotes'][0]['orig'][4]
                    wr['timesheets'] = 0


def get_data_from_config(name):
    """Gets data from a config file
        Returns a dictionary with that data
    """
    try:
        with open('clients/' + name + '/' + name + '.json') as data_file:
            client = json.load(data_file)
            return client
    except FileNotFoundError:
        print('\nERROR: Either there is no config file for that Organisation, or you have entered their name incorrectly in argv. See usage instructions \n(Argv is all lowercase. Org name must be the short version and month must be the month + shorthand year)\n')


def get_month_config(filename):
    """ Gets data from data that has been manually entered into that months config file (eg org-may17.json)
        Returns a dictionary
    """
    with open('clients/' + filename + '.json') as data_file:
        exec_summary = json.load(data_file)
    return exec_summary


def get_total_hours(wr_list): #non_quoted_sla list
    """ Adds up the total hours of work done.
        Returns a dictionary with wr details and total hours for all those wr's.
    """
    total = 0.0

    for wr in wr_list:
        total += wr['timesheets']
    return total


def get_system_name (system_id):
    """ Gets system name from config file using system_id. Returns system name
    """
    with open('clients/' + sys.argv[1] + '.json') as data_file:
         data = json.load(data_file)

         for system in data["systems"]:
             if system['id'] == system_id:
                 return system['system_name']


def bullet_point_list(normal_list):
    """ Takes a list and returns it on seperate lines with bullet points """
    bullet_list = []
    for item in normal_list:
        item = u"\u2022" + " " + item
        bullet_list.append(item)
    return bullet_list


def split_date(client):
    """ Takes a date from the format < March 2017 > and seperates it into year and month
        Updates the client dictionary with 'month' and 'year'
        Returns client dictionary
    """
    client['date'] = datetime.strptime(client['config_date'], "%B %Y")
    for m in client['all_months']:
        split_month = m['month'].split('-')
        m['month'] = datetime(int(split_month[0]), int(split_month[1]), 1)
    return client


def solve(s):
    """ Takes a date with 'st', 'nd', 'rd, or 'th' on the end (such as July 1st 2017), and turns it into a datetime format"""
    return re.sub(r'(\d)(st|nd|rd|th)', r'\1', s)


def check_sla_date(client):
    """Checks to see if the SLA has expired via the data in the config file. Asks for user input to continue or exit if the report month is for a month not covered by the current SLA (according to the config file)
    """
    date = datetime.strptime(solve(client['sla_end_date']), "%B %d %Y")
    if client['date'] > date:
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
        args = argparser.parse_args()
        auth_token = args.token


        #wrms = WRMSClient(auth_token)
        #if auth_token is None:
        #    wrms.login(AUTH_USERNAME, AUTH_PASSWORD)

        #argv usage instructions - print explanation about api call. continue, y/n

        #run with the api token - no api token defaults to config data and prints out a message saying it's using config data

    #print("Run this in seperate terminal: soffice --writer --accept="socket,host=localhost,port=2002;urp;StarOffice.ServiceManager"
    #print("To save without the document popping up: soffice --writer --accept="socket,host=localhost,port=2002;urp;StarOffice.ServiceManager" -- headless

        client = {}
        client['name'] = sys.argv[1]
        put_data_into(client)
        renderer = SLARenderer(client)
        renderer.render()
        #if NoConnectException:
        #    print ('cant connect')
