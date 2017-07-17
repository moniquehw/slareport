from pprint import pprint


class MonthlyData:
    def __init__(self, client, csv_data):
        self.client = client
        self.month = csv_data['month']
        self.wrs = csv_data['wrs']

    def pop_wr(self, request_id):
        return self.wrs.pop(self.index_of(request_id))

    def index_of(self, request_id):
        i = 0
        for wr in self.wrs:
            if wr["request_id"] == request_id:
                return i
            i += 1

    def get_wr(self, request_id):
        for wr in self.wrs:
            if wr["request_id"] == request_id:
                return wr

    def get_sla_wrs(self):
        """ Returns a list of sla wrs

        """
        sla_wrs = []
        for wr in self.wrs:
            if wr["sla"]:
                sla_wrs.append(wr)
        return sla_wrs

    def get_non_sla_wrs(self):
        """ Returns a list of non sla wrs

        """
        non_sla_wrs = []
        for wr in self.wrs:
            if not wr["sla"]:
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
