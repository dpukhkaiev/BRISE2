from core_entities.experiment import Experiment
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
        temp['model'] = exp.description['ModelConfiguration']['ModelType']
        temp['default result'] = round(exp.search_space.get_default_configuration().get_average_result()[0], 2)
        temp['default configuration'] = [' '.join(str(v) for v in exp.search_space.get_default_configuration().get_parameters())]
        temp['solution result'] = round(exp.get_current_solution().get_average_result()[0], 2)
        temp['solution configuration'] = ' '.join(str(v) for v in exp.get_current_solution().get_parameters())
        temp['result improvement'] = str(round(get_relative_improvement(exp), 1)) + '%'
        temp['number of measured configurations'] = len(exp.measured_configurations)
        temp['search space coverage'] = str(round((len(exp.measured_configurations)/exp.description["ModelConfiguration"]["SamplingSize"])*100)) + '%',
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


def get_relative_improvement(experiment: Experiment) -> float:
    """Division of a Solution Configuration result to the Default Configuraiton.
    :param experiment: Experiment - Instance of Experiment Class.
    Returns:
        [Float] -- Round number in percent. If Default Configuration is 0 - returns 'inf'
    """
    default_avg_result = experiment.search_space.get_default_configuration().get_average_result()[0]
    solution_avg_result = experiment.get_current_solution().get_average_result()[0]
    if default_avg_result == 0:
        return float('inf')
    else:
        return (default_avg_result - solution_avg_result) / default_avg_result * 100
