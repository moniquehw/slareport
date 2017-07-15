#!/usr/bin/python3
from datetime import datetime
import re
import requests


# The wrms website to talk to.
BASE_URL = 'https://wrms.catalyst.net.nz'


class WRMSClient(object):
    def __init__(self, auth_token, debug=False):
        self.auth_token = auth_token
        self.debug = debug

    def login(self, username, password):
        """ Log in to WRMS and store the returned auth token """
        url = BASE_URL + '/api2/login'

        payload = {
            'username': username,
            'user_id': '',
            'password': password,
        }

        response = requests.post(url, data=payload)

        content = response.json()
        if not content['success']:
            raise Exception(content['message'])

        # Save the auth token and relevant data
        self.auth = content['response']
        self.auth_token = content['response']['auth_cookie_value']

    def _get_auth_headers(self):
        return {
            'Cookie': 'wrms3_auth=%s' % self.auth_token
        }


    def report(self, report_type, display_fields, page_size=10000, page_no=1, extra_params=None):
        """ Run a report_type report against the wrms api

        This is a rewrite of report_old

        """
        if extra_params is None:
            extra_params = {}

        url = BASE_URL + '/api2/report'

        params = extra_params
        params.update({
            'report_type': report_type,
            'display_fields': ','.join(display_fields),
            'page_size': 10000,
            'page_no': 1
        })

        # Add the rest of the arguments from function definition as shown below
        if self.debug:
            params["output_format"] = "pretty_json"

        results = self.get_request(url, params)
        # Check for errors
        if not results['success']:
            raise Exception(results['message'])
        return results

    def request_details(self, request_id):
        # approved_hours
        #https://wrms.catalyst.net.nz/api2/report?request_id_range=273821&report_type=admin_request&display_fields=request_id,status_desc,has_approved_quote,approved_hours

        params = {
            "request_id_range": request_id,
        }
        report = self.report("admin_request", ("request_id", "status_desc", "has_approved_quote", "approved_hours", "unapproved_hours", "brief"), extra_params=params)
        return report['response']["results"]

    def child_requests(self, request_id):
        """ Get all the children of work request "request_id"

        Args:
            request_id: The id of the work request to search for children of.
        Returns:
            A list of work requests with request_id, brief and details

        """
        params = {
            "parent_request_id": request_id
        }
        report = self.report("request", (
            "request_id",
            "brief",
            "detailed"
        ), extra_params=params)
        return report['response']['results']

    def post_request(self, url, params):
        headers = self._get_auth_headers()

        if not self.debug:
            response = requests.post(url, data=params, headers=headers)

            report = response.json()
            if not report['success']:
                raise Exception(report)
        else:
            print(url, params, headers)


    def get_request(self, url, params):
        """ Get a dictionary of values from a wrms url

        Args:
            url: The wrms url to hit
            params: Extra parameters to add to the url
        Returns:
            dictionary

        """
        headers = self._get_auth_headers()
        response = requests.get(url, params=params, headers=headers)
        return response.json()

    def get_wr_briefs(self, wr_list):
        """ Gets the details for a list of work requests - just the brief and wr number
            Args: wr_list: A list of work request numbers
            Returns: A list of dictionaries, each of which has the brief and the wr number in it

        """
        results = []
        for wr in wr_list:
            print("Fetching WR {} from wrms".format(wr))
            details = self.request_details(wr)
            #pprint(details[0])
            wr_dict = {}
            wr_dict['request_id'] = (details[0]['request_id'])
            wr_dict['brief'] = (details[0]['brief'])
            results.append(wr_dict)

        return results


def get_deployments(token, month, head_hosting_wr):
    wrms = WRMSClient(token)
    final_wrs = []
    for wr in wrms.child_requests(head_hosting_wr):
        if wr['request_id'] != head_hosting_wr:
            if '/' in wr['brief']:
                date = datetime.strptime(wr['brief'][-10:], "%d/%m/%Y")
            elif '-' in wr['brief']:
                date = datetime.strptime(wr['brief'][-10:], "%d-%m-%Y")
            elif '.' in wr['brief'] or 'security release' in wr['brief'].lower():
                print ('\nError with: {}: {}\nThis does not appear to be a deployment.\n'.format(wr['request_id'], wr['brief']))
            else:
                try:
                    date = datetime.strptime(wr['brief'][-8:], "%Y%m%d")
                except ValueError:
                    print ('Error with: {} {}\n Either this wr has no date in the brief, the date has been entered incorrectly or there is an extraneous child in WRMS. To include this WR in the report, include the correct date in the WRMS brief and run .sla_report.py again.\nACCEPTABLE DATE FORMATS: YYYYmmdd, dd-mm-YYYY, dd/mm/YYYY\n'.format(wr['request_id'], wr['brief']))

            if date >= month and date < next_month(month):
                deployed_wrs = [] # A list of dictionaries

                released = re.findall("[^\\d](\\d{6})[^\\d]", wr["detailed"])
                deployed_wrs = wrms.get_wr_briefs(released)
                this_release = {
                    "request_id": wr["request_id"],
                    "date": date,
                    "deployed_wrs": deployed_wrs
                }
                final_wrs.append(this_release)
    return final_wrs


def next_month(date):
    """ Get the same day next month

    Args:
        date: A datetime object
    Returns:
        A datetime object with the same day the next month

    """
    next_month = date.month + 1
    if next_month == 13:
        return datetime(date.year + 1, 1, date.day)
    else:
        return datetime(date.year, next_month, date.day)
