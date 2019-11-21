import plotly.graph_objs as go

def improvements(experiments):
    """ Improvements for the best result on each iteration of the experiment
    
    Args:
        experiments (List): The list of Experiment instances.
    
    Returns:
        Dictionary: Plotly dictionary
    """

    #-- Composite scatters
    data = []

    #-- Aggregate
    for exp in experiments:
        x = list(range(len(exp.measured_configurations)))
        trace = go.Scatter( # Relative solution to all experiments
            x=x, 
            y=[con.get_average_result()[0] for con in exp.measured_configurations], 
            mode='lines+markers', 
            name = '{} results'.format(exp.get_name()), 
            marker=dict(color=exp.color, size=6),
            line = dict(
                width = 2,
                dash = 'dot')
            )

        imp = []
        for i, con in enumerate(exp.measured_configurations):
            val = con.get_average_result()[0]
            prev = val if i==0 else imp[i-1]
            best = val if val < prev else prev # minimization
            imp.append(best)

        imp_trace = go.Scatter( # Best solution in scope of current experiment
            x=x, 
            y=imp, 
            mode='lines', 
            name = '{} best results'.format(exp.get_name()), 
            marker=dict(color=exp.color, size=4),
        )
        data.append(trace)
        data.append(imp_trace)

    
    layout = dict(
                title = 'Relatively improvements result',
                yaxis = dict(zeroline = False, title='Result'),
                xaxis = dict(zeroline = False, title='Iteration'),
                legend=dict(yanchor="top", font=dict(size=10))
            )

    return dict(data=data, layout=layout)
