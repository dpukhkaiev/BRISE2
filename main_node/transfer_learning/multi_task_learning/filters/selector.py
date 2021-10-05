import logging

from tools.reflective_class_import import reflective_class_import
from transfer_learning.multi_task_learning.filters.decorator import FilterBase


def get_filter(filters: dict):
    """
    Construct instance of filters according to the experiment description.
    param filters: part of experiment description containing filter info.
    """
    filters_class = FilterBase()
    logger = logging.getLogger(__name__)
    for single_filter in filters.keys():
        current_filters = reflective_class_import(class_name=single_filter,
                                                  folder_path="transfer_learning/multi_task_learning/filters")
        filters_class = current_filters(filters_class)
        logger.info(f"Assigned {single_filter} filter.")

    return filters_class
