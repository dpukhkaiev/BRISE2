import plotly.graph_objs as go

def box_statistic(experiments):
    """ Statistical distribution for all and average results on each configuration in the experiment.

    Args:
        experiments (List): The list of Experiment instances.

    Returns:
        Dictionary: Plotly dictionary
    """

    # -- Composite traces
    data = []

    for exp in experiments:
        #-- Extract
        all_res = exp.get_all_repetition_tasks()
        avg_res = [conf.get_average_result()[0]
                   for conf in exp.all_configurations]

        #-- Aggregate
        trace = go.Box(
            y=all_res + avg_res,
            x=['all' for _ in all_res] + ['average' for _ in avg_res],
            name=exp.get_name(),
            boxpoints='suspectedoutliers',
            marker=dict(
                outliercolor='#85ef47',
                color=exp.color,
            )
        )
        data.append(trace)

    layout = dict(
        title='Statistical distribution of results',
        boxmode='group',
        yaxis=dict(zeroline=False, title='Result'),
        xaxis=dict(zeroline=False, title='Experiments'),
                legend=dict(x=0.029, y=-0.32, font=dict(size=10))
    )

    return dict(data=data, layout=layout)
