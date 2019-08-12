import plotly.graph_objs as go
from plotly import tools

def repeat_vs_avg(exp):
    """ Compare average results and measurements repeats for one experiment.
    
    Args:
        exp (Experiment): Single Experiment instance.
    
    Returns:
        Dictionary: Plotly dictionary
    """
    #-- Extract
    x_param = [str(conf.get_parameters()) for conf in exp.all_configurations]
    y_repeat = [ len(conf.get_tasks()) for conf in exp.all_configurations]
    y_avg_res = [conf.get_average_result()[0] for conf in exp.all_configurations]
    y_deviation = [conf.get_standard_deviation()[0] for conf in exp.all_configurations]

    #-- Aggregate
    trace_repeat = go.Bar(
        x=y_repeat,
        y=x_param,
        marker=dict(color='lightgrey',line=dict(color='#160D0D',width=1)),
        name='repeat',
        orientation='h'
    )
    trace_avg = go.Scatter(
        x=y_avg_res,
        y=x_param,
        mode='lines+markers',
        line=dict(color=exp.color),
        marker=dict(symbol="diamond-cross"),
        name='avarage',
        error_x=dict(
            type='data',
            color='rgba(0,176,246,0.3)',
            array=y_deviation,
            visible=True
        )
    )
    trace_dev = go.Scatter(
        x=y_deviation,
        y=x_param,
        fill='tozerox',
        fillcolor='rgba(0,176,246,0.2)',
        line=dict(color='rgb(0,176,246)'),
        mode='lines',
        name='deviation',
    )
    layout = dict(
                    title=exp.name,
                    yaxis=dict(showticklabels=True,type='category',domain=[0, 0.85],automargin=True,),
                    yaxis2=dict(showline=True,showticklabels=False,linecolor='rgba(102, 102, 102, 0.5)',linewidth=2,domain=[0, 0.85]),
                    xaxis=dict(zeroline=False,showline=False,showticklabels=True,showgrid=True,domain=[0, 0.41],side='top'),
                    xaxis2=dict(zeroline=False,showline=False,showticklabels=True,showgrid=True,domain=[0.47, 1],side='top'),
                    legend=dict(x=0.029,y=1.042,font=dict(size=10) ),
                    margin=dict(l=200, r=20,t=70,b=70),
                    paper_bgcolor='rgb(248, 248, 255)',
                    plot_bgcolor='rgb(248, 248, 255)',
    )

    #-- Composite
    # Creating two subplots
    fig = tools.make_subplots(rows=1, cols=2, specs=[[{}, {}]], shared_xaxes=False, shared_yaxes=True)

    fig.append_trace(trace_repeat, 1, 1)
    fig.append_trace(trace_avg, 1, 2)
    fig.append_trace(trace_dev, 1, 2)

    fig['layout'].update(layout)

    return fig
