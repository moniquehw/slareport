
from matplotlib import pyplot as plt
import matplotlib
import numpy as np
import os


def render_lifetime_graph(summary_data, current_month, contract_hours, short_name):
    """ Renders a lifetime summary graph for SLA hours.
        Saves it as a .png file into current directory.
    """
    months = []
    sla_hours = []
    extra_hours = []

    for month in summary_data:
        months.append(month['name'])
        sla_hours.append(month['sla'])
        extra_hours.append(month['non_sla'])
        if month['name'] == current_month:
            break

    def make_graph():
        """Makes a bar graph using matplotlib"""
        n_months = len(months)
        threshold = contract_hours

        ind = np.arange(n_months)    # the x locations for the groups
        width = 0.7      # the width of the bars: can also be len(x) sequence #old width is 6

        matplotlib.rc('font', family='sans-serif', size='10', weight='normal')
        #matplotlib.rcParams['font.sans-serif'] = 'Lato'
        #plt.xkcd()
        fig, ax = plt.subplots()
        fig.set_size_inches(15 / 2.54, 5 / 2.54)
        ax.margins(0.05, 0)
        plt.bar(ind, sla_hours, width, edgecolor='w', color='#5B9AA9', label='SLA Hours')
        plt.bar(ind, extra_hours, width, edgecolor='w', color='#E6AD30',
                bottom=sla_hours, label='Extra Hours')

        #plt.xlabel(threshold)
        plt.ylabel('Hours')
        #plt.title('SLA Lifetime Summary')
        plt.xticks(ind + width / 2, months)
        # yu = contract_hours
        yl, yu = ax.get_ylim()

        ax.set_ylim(yl, max(1.05*yu, 1.2 * threshold))

        plt.tight_layout()
        #box = ax.get_position()
        #ax.set_position([box.x0, box.y0 + box.height * 0.2, box.width, box.height * 0.8])
        #plt.legend(loc='lower center',
        #           ncol=2,
        #           bbox_to_anchor=(0.5, 0),
        #           bbox_transform=plt.gcf().transFigure,
        #           frameon=False)
        # plt.show()

        ax.plot([0., n_months - 0.3], [threshold, threshold], "k--")

        short_date = current_month[:3] + current_month[-2:]
        filename = os.getcwd() + "/" + short_name + "/" + short_name + "_" + short_date + "_summary_graph.png"

        plt.savefig(filename, dpi=200)
        return filename

    return make_graph()
