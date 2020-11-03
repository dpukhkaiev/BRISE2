import json

from jinja2 import Environment, FileSystemLoader


def exp_description_highlight(experiments):
    """ Return highlighted JSON syntax in accordance tabs with experiment instances
    Args:
        experiments (List): The list of Experiment instances.
    Returns:
        HTML: Markup component with related styles and scripts.
    """
    # Component template
    file_loader = FileSystemLoader("./templates")
    env = Environment(loader=file_loader)
    template = env.get_template('config_tabs.html')

    # Extract configurations
    conf_colection = []
    for exp in experiments:
        parsed_config = exp.description
        temp = {
            "config": "undefined",
            "name": "undefined"
        }
        temp['config'] = json.dumps(parsed_config).replace('"', "'")
        temp['name'] = exp.get_name()
        conf_colection.append(temp)

    # Compose HTML
    html = template.render(experiments=conf_colection)

    return html
