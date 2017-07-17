import requests
import json
import os
import sys

from clients.config import sla_list, org_list

def get_url():
    """ Gets a list of the csv url's saved in each organisation's config file.
        Returns dictionary
    """
    url_dict = {}
    # the 2 lists of organisation names to get data for is in clients/config.py

    #if len(sys.argv) > 0 sys.argv[1] == 'sla': #just get data for sla reports if sla is in sys.argv[1]
    #    org_list = sla_list
    #    print (org_list)
    #elif len(sys.argv) > 1 and sys.argv[1] != 'sla': #if there are orgs listed in argv, just get data for those orgs
    #    org_list = []
    #    for org in sys.argv[1:]:
    #        org_list.append(org)
    #elif len(sys.argv) == 0:
    #    for org in sys.argv[1:]:
    #        org_list.append(org)
    #else: # get data for all the orgs
    #    org_list.update(sla_list)

    for org in org_list: #get a list of url's to get csv data from, using the config files
        with open ('clients/' + org + '/' + org + '.json') as data_file:
            json_dict = json.load(data_file)
            url = json_dict['url']
            url_dict[org] = url
    return url_dict

def save_csv():
    """ Saves a .csv file for each organisation in the org_list.
        Saved filename is short_name + month/year + .csv (eg orgname_march17.csv)
    """
    url_dict = get_url()
    for client in url_dict:
        response = requests.get(url_dict[client], stream=True)
        filename = os.getcwd() + "/" + 'clients/' + client + '/' + client + '.csv'
        handle = open(filename, "wb")
        for chunk in response.iter_content(chunk_size=512):
            if chunk:  # filter out keep-alive new chunks
                handle.write(chunk)
save_csv()
