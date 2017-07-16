from pprint import pprint


class MonthlyData:
    def __init__(self, client, csv_data):
        self.client = client
        self.month = csv_data['month']
        self.wrs = csv_data['wrs']

    def get_sla_wrs(self):
        """ Returns a list of sla wrs

        """
        sla_wrs = []
        for wr in self.wrs:
            if self.client.config['hosting_hrs_additional'] and "Hosting" in wr['system']:
                pass
            elif len(wr['quotes']) > 0:
                if wr['quotes'][0]['sla'] is not False:
                    sla_wrs.append(wr)
            else:
                sla_wrs.append(wr)
        return sla_wrs

    def get_non_sla_wrs(self):
        """ Returns a list of non sla wrs

        """
        non_sla_wrs = []
        for wr in self.wrs:
            if self.client.config['hosting_hrs_additional'] and "Hosting" in wr['system']:
                non_sla_wrs.append(wr)
            elif len(wr['quotes']) > 0:
                if wr['quotes'][0]['sla'] is False:
                    non_sla_wrs.append(wr)
        return non_sla_wrs

    def get_sla_total(self):
        total = 0.0
        for wr in self.get_sla_wrs():
            total += wr["timesheets"]
        return total

    def get_non_sla_total(self):
        total = 0.0
        for wr in self.get_non_sla_wrs():
            total += wr['timesheets']
        return total
