import time
import random
from string import ascii_lowercase
import os
import logging

from jinja2 import Environment, FileSystemLoader
from plotly.offline import plot

# Tools
from shared_tools import restore
# from shared_tools import export_plot

# Plots
from plots.table import table
from plots.repeat_vs_avg import repeat_vs_avg
from plots.improvements import improvements
from plots.box_statistic import box_statistic
from plots.exp_config import exp_description_highlight

# The size of the saved images
WIGHT = 1200
HEIGHT = 600

# Function for importing styles and scripts in the template
def get_resource_as_string(name, charset='utf-8'):
    with open(name, "r", encoding=charset) as f:
        return f.read()

def benchmark(exp_for_benchmark):
    """ Generate report files from the Experiment class instances.

    Args:
        exp_for_benchmark (List): List of file names with stored Experiments class instances. Name should include a file extension (e.g. .pkl).
    """
    # --- Generate template
    file_loader = FileSystemLoader("./volume/templates")
    env = Environment(loader=file_loader)
    env.globals['get_resource_as_string'] = get_resource_as_string
    template = env.get_template('index.html')

    # --- Restore experiments for benchmarking
    exp_list = restore(*exp_for_benchmark)

    # --- Generate plot's hooks
    tab = plot(table(exp_list), include_plotlyjs=False, output_type='div')
    impr = plot(improvements(exp_list),
                include_plotlyjs=False,
                output_type='div')
    all_results = plot(box_statistic(exp_list),
                       include_plotlyjs=False,
                       output_type='div')
    rep = ' '.join(plot(repeat_vs_avg(exp), include_plotlyjs=False,
                        output_type='div') for exp in exp_list)
    time_mark = time.strftime('%Y-%m-%d %A', time.localtime())

    # Compose HTML
    html = template.render(
        table=tab,
        impr=impr,
        repeat_vs_avg=rep,
        box_plot=all_results,
        time=time_mark,
        print_config=exp_description_highlight(exp_list)
    )

    # --- Save results
    # Write HTML report
    suffix = ''.join(random.choice(ascii_lowercase) for _ in range(10))
    with open("./volume/results/reports/report_{}.html".format(suffix), "w", encoding='utf-8') as outf:
        outf.write(html)

    # # Export plots
    # for plt in [table(exp_list), improvements(exp_list), box_statistic(exp_list)]:
    #     export_plot(plot=plt, wight=WIGHT, height=HEIGHT)

    # Using a host machine User ID to change the owner for the files(initially, the owner was a root).
    for root, dirs, files in os.walk("./volume/results/reports/"):
        for f in files:
            os.chown(os.path.abspath(os.path.join(root, f)),
                     int(os.environ['host_uid']), int(os.environ['host_gid']))
        break

if __name__ == "__main__":
    # ------- List with name experiment instances. Default from ./results/serialized/ folder
    selection = [f for f in os.listdir('./volume/results/serialized/') if (f[-4:] == '.pkl')]
    # -------

    if selection:
        print("selection = ", selection)
        benchmark(selection)
    else:
        logging.warning("Directory './volume/results/serialized/' is empty.")
