import plotly.graph_objs as go

def table(experiments):
    """ Key properties for comparing experiments.
    
    Args:
        experiments (List): The list of Experiment instances.
    
    Returns:
        Dictionary: Plotly dictionary
    """

    #-- Extract
    template = dict({
        'model': None,
        'default configuration': None,
        'solution configuration': None,
        'default result': None,
        'solution result': None,
        'result improvement': None,
        'number of measured configurations': None,
        'search space coverage': None,
        'number of repetitions': None,
        'execution time': None,
        'repeater': None
    })

    exp_data = []

    for exp in experiments:
        # copy template
        temp = template.copy()

        # extract information from the experiment
        search_space = 1
        for dim in exp.description['DomainDescription']['AllConfigurations']:
            search_space *= len(dim)

        temp['model'] = exp.description['ModelConfiguration']['ModelType']
        temp['default result'] = round(exp.default_configuration.get_average_result()[0], 2)
        temp['default configuration'] = [' '.join(str(v) for v in exp.default_configuration.get_parameters())]
        temp['solution result'] = round(exp.get_current_solution().get_average_result()[0], 2)
        temp['solution configuration'] = ' '.join(str(v) for v in exp.get_current_solution().get_parameters())
        temp['result improvement'] = str(round(exp.get_solution_relative_impr(), 1)) + '%'
        temp['number of measured configurations'] = len(exp.all_configurations)
        temp['search space coverage'] = str(round((len(exp.all_configurations)/search_space)*100)) + '%',
        temp['number of repetitions'] = len(exp.get_all_repetition_tasks())
        temp['execution time'] = str((exp.end_time - exp.start_time).seconds) + ' s'
        temp['repeater'] = exp.description['Repeater']['Type']

        exp_data.append(temp)
         

    #-- Aggregate
    header = ["<b> {name} </b>".format(name=e.get_name()) for e in experiments]
    header.insert(0, '<b> Description </b>')
    h_colors = [ exp.color for exp in experiments]
    h_colors.insert(0, '#a1c3d1')

    cells = [list(e.values()) for e in exp_data]
    cells.insert(0, list(template.keys()))

    trace = go.Table(
        header=dict(
            values=header,
            font=dict(color = '#2e2f30', size = 12),
            fill=dict(color=h_colors),
            align=['left'] * 5,
            height = 40
        ),
        cells=dict(
                values=cells,
                line=dict(color='#7D7F80'),
                fill=dict(color='#EDFAFF'),
                align=['left'] * 5)
        )

    #-- Composite
    data = [trace]

    return dict(data=data)
