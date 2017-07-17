#!/usr/bin/python3
import csv
from datetime import datetime
import pprint
import sys


class RowPrinter:
    def __init__(self, rows):
        self.rows = rows

    def __next__(self):
        row = next(self.rows)
        print(row)
        return row


class SlaSlurper:
    def __init__(self, filename):
        self.months = []
        self.rows = csv.reader(open(filename))
        self.parse()

    def parse(self):
        try:
            self.parse_months()
        except StopIteration:
            return

    def parse_months(self):
        while True:
            next_row = next(self.rows)
            try:
                self.client_name = next_row[0]
            except IndexError:
                return
            self.months.append(self.parse_month())
            self.swallow_blank()

    def parse_month(self):
        month = next(self.rows)[1]
        hours_budget = next(self.rows)[1]
        sla_quoted = next(self.rows)[1]
        unquoted = next(self.rows)[1]
        final_balance = next(self.rows)[1]

        month_data = {
            "month": month,
            "hours_budget": hours_budget,
            "sla_quoted": sla_quoted,
            "unquoted": unquoted,
            "final_balance": final_balance
        }
        self.swallow_blank()
        month_data["wrs"] = self.parse_wrs()
        return month_data

    def swallow_blank(self):
        next(self.rows)

    def parse_wrs(self):
        wrs = []
        while True:
            row = next(self.rows)
            if row[0] == '--------':
                break
            wrs.append(self.parse_wr(row))
        return wrs

    def parse_wr(self, first_row):
        request_id = first_row[1]
        request_id = request_id[4:]
        brief = first_row[2]
        system = first_row[3]
        status = first_row[4]
        data = {
            "request_id": request_id,
            "brief": brief,
            "system": system,
            "status": status
        }

        self.swallow_blank()

        data["quotes_approved"], data["quotes_unapproved"] = self.parse_quotes()
        self.swallow_blank()  # Swallow the line "Timesheets:"
        try:
            data["previous_month"] = float(next(self.rows)[1])
            data["timesheets"] = self.parse_timesheets()
        except IndexError:
            data["previous_month"] = 0
            data["timesheets"] = 0
            return data
        return data

    def parse_quotes(self):
        self.swallow_blank()  # Swallow the line "Quotes:"
        quotes = []
        while True:
            next_row = next(self.rows)
            if len(next_row) == 0:
                break
            quotes.append(self.parse_quote(next_row))
        approved_quotes = []
        unapproved_quotes = []
        for q in quotes:
            if q["status"] == "Approved":
                approved_quotes.append(q)
            else:
                unapproved_quotes.append(q)
        return approved_quotes, unapproved_quotes

    def parse_quote(self, quote):
        parsed_quote = {
            "status": quote[5],
            "quote_brief": quote[3],
            "orig": quote,
        }
        if "SLA" in quote[1]:
            parsed_quote["sla"] = True
            quote_id, month, sla = quote[1].split()
            year, month = month.split("-")
            parsed_quote["sla_month"] = datetime(int(year), int(month), 1)
        else:
            parsed_quote["sla"] = False
        return parsed_quote

    def parse_timesheets(self):
        timesheet_total = 0
        while True:
            next_row = next(self.rows)
            if len(next_row) == 0:
                return timesheet_total
            timesheet_total += float(next_row[4])

    def get_month(self, dt):
        """ Accepts a month_name in the format YYYY-MM
            Returns month date in format for csv
        """
        for m in self.months:
            if m['month'] == dt:
                return m

    def __str__(self):
        return "Sla request for " + self.client_name


def get_sla_data(filename):
        slas = SlaSlurper(filename)
        pprint.pprint(slas)
        return slas


if __name__ == "__main__":
    slas = get_sla_data(sys.argv[1])
    pprint.pprint(slas.months)
