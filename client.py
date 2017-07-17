from monthlydata import MonthlyData
from datetime import datetime
from csv_data import get_sla_data
import json
import os
from pprint import pprint
from api_deployments import get_deployments
import math


class Client:
    def __init__(self, name, filename, token):
        self.name = name
        self.months = []
        self.config = self.get_data_from_config()
        self.month_config = self.get_month_config(filename)
        self.token = token

    def get_data_from_config(self):
        """ Gets data from a config file

        Returns:
            A dictionary with that data
        """
        try:
            with open('clients/' + self.name + '/' + self.name + '.json') as data_file:
                config = json.load(data_file)
                return config
        except FileNotFoundError:
            print('\nERROR: Either there is no config file for that Organisation, or you have entered their name incorrectly in argv. See usage instructions \n(Argv is all lowercase. Org name must be the short version and month must be the month + shorthand year)\n')

    def get_month_config(self, filename):
        """ Gets data from data that has been manually entered into that months config file (eg org-may17.json)

        Returns:
             The months config as a dictionary
        """
        with open('clients/' + self.name + '/' + filename) as data_file:
            monthly_config = json.load(data_file)
        self.date = datetime.strptime(monthly_config['config_date'], "%B %Y")
        return monthly_config

    def get_last_modified(self):
        """ Get the current date as a YYYY-MM-DD string to be used as a last modified

        Returns:
            A string with the format YYYY-MM-DD

        """
        return datetime.now().strftime('%Y-%m-%d')

    def initialise_data(self):
        """ Initialise the monthly data for this client. Gets data from wrms and the csv.

        Also calls some functions to fiddle the data as appropriate.

        """

        csv_months = self.get_data_from_csv().months
        for csv_month in csv_months:
            split_month = csv_month['month'].split('-')
            csv_month['month'] = datetime(int(split_month[0]), int(split_month[1]), 1)
            if csv_month['month'] > self.date:
                break
            self.months.append(MonthlyData(self, csv_month))
        self.sort_quotes()

    def get_data_from_csv(self):
        """ Get the data from the csv for this client.

        Returns:
            A SLASlurper object with the data loaded

        """
        sla_list = get_sla_data(os.getcwd() + "/clients/" + self.name + '/' + self.name + '.csv')
        return sla_list

    def get_lifetime_summary(self):
        """ Takes the total number of hours from each month for SLA and non SLA work and adds them together.
            Returns: The total number of SLA and non-SLA hours for each month, along with the month name in the correct format (Mar 17 for march 2017)
        """
        summary_data = []
        for m in self.months:
            month_name = m.month.strftime("%b %y")
            month_dict = {"name": month_name}

            month_dict['sla'] = m.get_sla_total()
            month_dict['non_sla'] = m.get_non_sla_total()
            summary_data.append(month_dict)

        #manually insert number of hours for this month to redo the graph with those hours
        if self.month_config["additional_hours_override"] != 0:
            month_dict['non_sla_total'] = self.month_config["additional_hours_override"]
        if self.month_config['sla_hours_override'] !=0:
            month_dict['sla_total'] = self.config['sla_hours_override']
        return summary_data

    def get_deployment_list(self):
        list_of_production_changes = self.month_config['list_of_production_changes']
        if self.token != 'noapi':
            deployment_list = get_deployments(self.token, self.month_config, self.config['deployment_head_wr'])
            for deployment in deployment_list: #for 1 deployment in list of deployments
                list_of_production_changes.append(deployment) # add the deployment to deployments
                date = deployment['date'].strftime("%d %B %Y")
                deployment['date'] = date
                deployment['request_id'] = str(deployment['request_id'])
                for deployed_wrs in deployment['deployed_wrs']:
                    deployed_wrs['request_id'] = str(deployed_wrs['request_id'])

            list_of_production_changes.sort(key=lambda d : (d.get("date")))
        return list_of_production_changes


    def sort_quotes(self):
        """ Update the timesheeted hours in client for each WR (to take into account previous
            months work that has already been quoted and the hours taken off).

        """
        quoted_non_sla = {}
        quoted_sla = {}

        for month in self.months:
            for wr in month.wrs:
                wr["timesheets"] = round_up_to(wr['timesheets'], self.config['rounding'])
                if self.config['hosting_hrs_additional'] and 'Hosting' in wr['system']:
                     # if the wr is in a hosting system and hosting counts towards sla hours
                     pass

                #if the wr has a quote
                    #if the quote is for sla
                        #if the quote is for this months sla:
                            #add it to quoted sla
                        #else:
                            #ignore it
                    #else:
                        #add it to additional hours


                elif wr['request_id'] in quoted_non_sla or wr['request_id'] in quoted_sla: # If the wr was quoted in the previous months
                    try:
                        if '-' in wr['quotes'][0]['orig'][1]:
                            quote_month = wr['quotes'][0]['orig'][1][7:-4]
                            #quote_month = quote_month[7:-4]
                            quote_month = datetime.strptime(quote_month, "%Y-%m")
                            print ('test', quote_month)
                    except ValueError:
                        print ('Error with WR # {}\n Please fix the \'Invoice to\' field in WRMS for this WR. The date needs to be entered with 3 fields (YYYY-m-d). If the data in this field is not a date, edit it so it doensn\'t read like one. Then fetch the csv data again with get_csv_data.py')




                    wr['timesheets'] = 0
                elif len(wr['quotes']) > 0: # if there's a quote
                    if wr['quotes'][0]['status'] == 'Approved':
                        if wr['quotes'][0]['sla'] is False: #approved and not sla - uses time quoted instead of timesheeted
                            quoted_non_sla[wr['request_id']] = wr['quotes'][0]['orig'][4]
                        else:#approved and sla
                            quoted_sla[wr['request_id']] = wr['quotes'][0]['orig'][4]
                        wr['timesheets'] = float(wr['quotes'][0]['orig'][4])
                    else:
                        if wr['quotes'][0]['sla'] is False:#quoted, not approved not sla
                            quoted_non_sla[wr['request_id']] = wr['quotes'][0]['orig'][4]
                        else: #quoted, not approved sla
                            non_quoted_sla[wr['request_id']] = wr['quotes'][0]['orig'][4]
                        #wr['timesheets'] = float(wr['quotes'][0]['orig'][4]) # use timesheeted hours for unapproved quotes

    def get_active_month(self):
        for month in self.months:
            if month.month == self.date:
                return month


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
