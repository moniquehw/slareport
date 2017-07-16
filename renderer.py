import uno
import os
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.awt import Size
from graphs import render_lifetime_graph


class SLARenderer:
    def __init__(self, client):
        self.client = client

    def render(self):
        self.connect()

        self.render_lifetime_graph()

        self.find_replace("{{service_name}}", self.client.config["service_name"])
        self.find_replace("{{config_date}}", self.client.month_config["config_date"])
        self.find_replace("{{sla_start_date}}", self.client.config["sla_start_date"])
        self.find_replace("{{sla_end_date}}", self.client.config["sla_end_date"])
        self.find_replace("{{exec_summary}}", self.client.month_config["exec_summary"])

        active_month = self.client.get_active_month()

        self.find_replace("{{contract_hours}}", self.client.config["contract_hours"])
        self.find_replace("{{total_sla_hours}}", active_month.get_sla_total())
        self.find_replace("{{quoted_non_sla}}", active_month.get_non_sla_total())

        if self.client.config['hosting']:
            self.insert_platform_statistics_table()

        self.insert_text("Work Breakdown", "Catalyst - Heading 1")
        #insert wr tables for sla and non sla work
        if active_month.get_sla_total() > 0:
            self.insert_system_table(active_month.get_sla_wrs(), "SLA Hours", active_month.get_sla_total())
            self.insert_text("* No cost incurred this month for WR's with 0 hours", "Catalyst - Table Annotation")
        else:
            self.insert_text("SLA Hours", "Catalyst - Heading 2")
            self.insert_text("No SLA Hours were used this month", "Catalyst - Text Body")

        if active_month.get_non_sla_total() > 0:
            self.insert_system_table(active_month.get_non_sla_wrs(), "Additional Hours", active_month.get_non_sla_total())
            self.insert_text("* No cost incurred this month for WR's with 0 hours", "Catalyst - Table Annotation")
        else:
            self.insert_text("Additional Hours", "Catalyst - Heading 2")
            self.insert_text("No Additional Hours were used this month", "Catalyst - Text Body")

        self.insert_summary_table()
        self.find_replace("{{client_name}}", self.client.config["client_name"])

        #"\n".join(self.client.config['recipients'])
        self.find_replace("{{last_modified}}", self.client.get_last_modified())

        self.save()

    def bulleted_list(self, table, cell_name, blist):
        if len(blist) > 1:
            table_text = table.getCellByName(cell_name)
            cursor = table_text.createTextCursor()
            for item in blist:
                cursor.setPropertyValue("ParaStyleName", "Catalyst - Bullet List")
                table_text.insertString(cursor, item, 0)
                table_text.insertControlCharacter(cursor, PARAGRAPH_BREAK, 0)
            cursor.gotoEndOfParagraph(True)
            cursor.goLeft(1, True)
            cursor.String = ""
        else: #else enter with no bullets
            self.set_table_cell(table, cell_name, blist[0], {"ParaStyleName": "Catalyst - Table contents"})

    def render_lifetime_graph(self):
        """ Renders a lifetime summary graph """
        url = render_lifetime_graph(self.client.get_lifetime_summary(), self.client.date.strftime("%b %y"), self.client.config['contract_hours'], self.client.name)
        text = self.document.Text
        replace_desc = self.document.createReplaceDescriptor()
        replace_desc.setSearchString("{{lifetime_summary}}")

        find_iter = self.document.findFirst(replace_desc)
        c = text.createTextCursorByRange(find_iter.Start)
        find_iter.String = ""
        image = self.document.createInstance('com.sun.star.drawing.GraphicObjectShape')
        size = Size()
        image.GraphicURL = "file:///" + url
        size.Height = 5315
        size.Width = 16000
        image.setSize(size)
        text.insertTextContent(c, image, False)

    def insert_system_table(self, wr_list, title, total_hours):
        grey = 0xCCCCCC

        rows = len(wr_list) + 2

        table = self.insert_table_at_end(rows, 4, title) #(rows, columns)
        table_rows = table.Rows
        header_row = table_rows.getByIndex(0)
        header_row.setPropertyValue( "BackColor", grey)

        self.set_table_cell(table, "A1", 'WR', {"ParaStyleName": "Catalyst - Table header"})
        self.set_table_cell(table, "B1", 'Brief', {"ParaStyleName": "Catalyst - Table header"})
        self.set_table_cell(table, "C1", "Status", {"ParaStyleName": "Catalyst - Table header"})
        self.set_table_cell(table, "D1", "Sum - Amount", {"ParaStyleName": "Catalyst - Table header"})

        row = 2
        for wr in wr_list:
            self.set_table_cell(table, "A{}".format(row), wr['request_id'], {"ParaStyleName": "Catalyst - Table contents"})
            self.set_table_cell(table, "B{}".format(row), wr['brief'], {"ParaStyleName": "Catalyst - Table contents"})
            self.set_table_cell(table, "C{}".format(row), wr['status'], {"ParaStyleName": "Catalyst - Table contents"})
            self.set_table_cell(table, "D{}".format(row), wr['timesheets'], {"ParaStyleName": "Catalyst - Table contents"})
            row += 1

        new_row = table_rows.getByIndex(row - 1)
        new_row.setPropertyValue("BackColor", grey)

        self.set_table_cell(table, "A{}".format(row), 'Total Result', {"ParaStyleName": "Catalyst - Table header red"})
        self.set_table_cell(table, "D{}".format(row), total_hours, {"ParaStyleName": "Catalyst - Table header red"})


    def insert_summary_table(self):
        grey = 0xCCCCCC

        table = self.insert_table_at_end(3, 2, 'Document Information') #(rows, columns)
        for cell in (("A1", "Prepared for:"), ("A2", "Client Distribution:"), ("A3", "Created on:")):
            self.set_table_cell(table, cell[0], cell[1], {"ParaStyleName": "Catalyst - Table header"})
            table.getCellByName(cell[0]).setPropertyValue("BackColor", grey)
        for cell in (("B1", "{{client_name}}"), ("B3", "{{last_modified}}")):
            self.set_table_cell(table, cell[0], cell[1], {"ParaStyleName": "Catalyst - Table contents"})
        self.bulleted_list(table, 'B2', self.client.config['recipients'])

        sep = table.TableColumnSeparators
        sep[0].Position = 3000
        table.TableColumnSeparators = sep

    def insert_platform_statistics_table(self):
            grey = 0xCCCCCC

            table = self.insert_table_at_end(5, 2, 'Platform Statistics') #(rows, columns)

            #insert headings for table
            for cell in (("A1", "Number of active users"), ("A2", "Storage used"), ("A3", "Availability/uptime"), ("A4", "Out of hours events"), ("A5", "Production changes")):
                self.set_table_cell(table, cell[0], cell[1], {"ParaStyleName": "Catalyst - Table header"})
                table.getCellByName(cell[0]).setPropertyValue("BackColor", grey)

            self.bulleted_list(table, 'B2', self.client.month_config['storage_used'])
            self.bulleted_list(table, 'B4', self.client.month_config['ooh'])

            for cell in (("B1",self.client.month_config['number_active_users']), ("B3", self.client.month_config["uptime"])): #("B4", self.client["ooh"])):
                self.set_table_cell(table, cell[0], cell[1], {"ParaStyleName": "Catalyst - Table contents"})
            sep = table.TableColumnSeparators
            sep[0].Position = 3000
            table.TableColumnSeparators = sep
            table_text = table.getCellByName("B5")
            cursor = table_text.createTextCursor()

            production_changes = self.client.get_deployment_list()
            if len(production_changes) == 0:
                self.set_table_cell(table, "B5", "None", {"ParaStyleName": "Catalyst - Table contents"})
            else:
                for deployment in production_changes:
                    cursor.setPropertyValue("ParaStyleName", "Catalyst - Table header")

                    table_text.insertString(cursor, deployment['date'], 0)
                    table_text.insertControlCharacter(cursor, PARAGRAPH_BREAK, 0)

                    cursor.setPropertyValue("ParaStyleName", "Catalyst - Bullet List")

                    for wr in deployment["deployed_wrs"]:
                        new_cursor = table_text.createTextCursorByRange(cursor)
                        new_cursor.setString("WR: {}".format(wr["request_id"]))
                        new_cursor.HyperLinkURL = "https://wrms.catalyst.net.nz/wr.php?request_id={}".format(wr["request_id"])

                        table_text.insertString(cursor, "  " + wr["brief"], 0)
                        table_text.insertControlCharacter(cursor, PARAGRAPH_BREAK, 0)
                    cursor.gotoEndOfParagraph(True)
                    cursor.goLeft(1, True)
                    cursor.String = ""


    def set_table_cell(self, table, cell_name, text, properties = {}):
        table_text = table.getCellByName(cell_name)
        cursor = table_text.createTextCursor()
        for p, v in properties.items():
            cursor.setPropertyValue(p, v)
        table_text.setString(text)


    def connect(self):
        # soffice --writer --accept="socket,host=localhost,port=2002;urp;StarOffice.ServiceManager"
        #self.process = os.spawnlp(
        #    os.P_NOWAIT,
        #    "soffice",
        #    "--writer",
        #    '--accept="socket,host=localhost,port=2002;urp;StarOffice.ServiceManager"',
        #    "--headless")
        #print(self.process)
        #print("WTFBBQ?")
        #input()
        localContext = uno.getComponentContext()
        resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
        try:
            ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")

        except Exception as e:
            print(e)
            print('Failure to connect to soffice process.')
            print('In a new terminal, run soffice --writer --accept="socket,host=localhost,port=2002;urp;StarOffice.ServiceManager"')
            import sys
            sys.exit(-1)
        smgr = ctx.ServiceManager
        self.desktop = smgr.createInstanceWithContext( "com.sun.star.frame.Desktop",ctx)
        self.document = self.desktop.loadComponentFromURL("file:///" + os.getcwd() + "/reporttemplate.odt", "_blank", 0, ())


    def find_replace(self, search_string, replace_string):
        replace_desc = self.document.createReplaceDescriptor()
        replace_desc.setSearchString(search_string)

        find_iter = self.document.findFirst(replace_desc)
        while find_iter:
            find_iter.String = replace_string
            find_iter = self.document.findNext(find_iter.End, replace_desc)

    def insert_table_at_end(self, x, y, title=None):
        text = self.document.Text
        cursor = text.createTextCursor()
        cursor.gotoEnd(False)
        if title is not None:
            cursor.ParaStyleName = "Catalyst - Heading 2"
            text.insertString(cursor, title, 0)
        text.insertControlCharacter(cursor, PARAGRAPH_BREAK, 0)
        cursor.ParaStyleName = "Catalyst - Text Body"
        table = self.document.createInstance("com.sun.star.text.TextTable")
        table.initialize(x, y)
        text.insertTextContent(cursor, table, True)
        table.Split = False
        return table

    def insert_text(self, text_content, style=None):
        text = self.document.Text
        cursor = text.createTextCursor()
        cursor.gotoEnd(False)
        if style is not None:
            cursor.ParaStyleName = style
        else:
            cursor.ParaStyleName = "Catalyst - Text Body"
        text.insertString(cursor, text_content, 0)
        text.insertControlCharacter(cursor, PARAGRAPH_BREAK, 0)


    def save(self):
        """ Saves the file as a .odt file to the current directory"""
        filename = "file:///" + os.getcwd() + "/clients/" + self.client.name + "/" + \
                   self.client.name + "_" + self.client.month_config['config_date'] + ".odt"
        self.document.storeToURL(filename, ())
        self.document.close(True)
