import sys
import pickle
import random
from string import ascii_lowercase

import plotly.io as pio

sys.path.append('/app')
from core_entities import configuration, experiment

# COLORS = [
    # '#1f77b4',  # muted blue
    # '#ff7f0e',  # safety orange
    # '#2ca02c',  # cooked asparagus green
    # '#d62728',  # brick red
    # '#9467bd',  # muted purple
    # '#8c564b',  # chestnut brown
    # '#e377c2',  # raspberry yogurt pink
    # '#7f7f7f',  # middle gray
    # '#bcbd22',  # curry yellow-green
    # '#17becf'   # blue-teal
# ]
COLORS = [
    '#ff8b6a',
    '#00d1cd',
    '#eac100',
    '#1f77b4',
    '#8c564b',
    '#621295',
    '#acdeaa',
    '#bcbd22',
    '#00fa9a',
    '#ff7f0e',
    '#f2c0ff',
    '#616f39',
    '#f17e7e'
]


def restore(*args, workdir="./volume/results/serialized/", **kwargs):
    """ De-serializing a Python object structure from binary files.
    
    Args:
        workdir (str, optional): Path to Experiment instances. Defaults to "./volume/results/serialized/".
    
    Returns:
        List: The list of Experiment instances.
    """

    exp = []
    for index, file_name in enumerate(args):
        with open(workdir + file_name, 'rb') as input:
            instance = pickle.load(input)
            instance.color = COLORS[index % len(COLORS)]
            exp.append(instance)
    return exp


def export_plot(plot, wight=600, height=400, path='./volume/results/reports/', file_format='.svg'):
    """ Export plot in another format. Support vector and raster - svg, pdf, png, jpg, webp.
    
    Args:
        plot (Plotly dictionary): Layout of plot with data
        wight (int, optional): Wight of output image. Defaults to 600.
        height (int, optional): Height of output image. Defaults to 400.
        path (str, optional): Path to export the file. Defaults to './volume/results/reports/'.
        file_format (str, optional): Export file format. Defaults to '.svg'.
    """
    name = ''.join(random.choice(ascii_lowercase) for _ in range(10)) + file_format
    pio.write_image(plot, path+name, width=wight, height=height)


