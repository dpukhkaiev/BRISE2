import logging
import os
import inspect
import importlib
import difflib
from functools import lru_cache


@lru_cache(maxsize=100, typed=True)
def reflective_class_import(class_name: str, folder_path: str, reduction_step: float = 0.1):
    """
    Importing a Class object according to its name. The Module file with a desired Class should have a same or
    at least similar (see docs for difflib.get_close_matches module) names.

    Recursive lookup does not supported. Yet.
    Relative folder path also is not supported, an absolute should is sufficient considering the main-node folder as a root.

    :param reduction_step: float [0..1] difflib.get_close_matches runs with decreasing 'requirements' for names similarity.
    :param class_name: String with a name of the desired Class.
            Example: 'Student Deviation'
    :param folder_path: A folder where Module with a Class is stored.
            Example: 'repeater'
    :return: Class object.
    """
    logger = logging.getLogger(__name__)

    # Finding a Module
    selected_module_file_name = ''
    cutoff = 1
    files = os.listdir(folder_path)
    if not files:
        # TODO: aspect weaving logging and debug info before every raise?
        #  Or maybe raising some specific Exception (with behavior) and catching it in API to handle expected errors:
        #  propagation to the front, dumping locals, saving stack (logger.error()and etc..
        msg = "Specified directory '%s' is empty." % folder_path
        logger.error(msg)
        raise NameError(msg)
    while not selected_module_file_name:
        selected_module_file_name = difflib.get_close_matches(class_name, files, n=1, cutoff=cutoff)
        cutoff -= reduction_step
    logger.debug("'%s' module was selected with cutoff=%f for name=%s." % (selected_module_file_name, cutoff, class_name))
    module_path = '%s.%s' % (folder_path.replace("./", "").replace("/", "."), selected_module_file_name[0][:-3])
    try:
        found_module = importlib.import_module(module_path)
    except ImportError as error:
        msg = "Unable to import module %s. Following exception occurred: %s" % (module_path, error)
        logger.error(msg)
        raise ImportError(msg)

    # Getting the Class
    classes_in_module = inspect.getmembers(found_module,
                                           lambda member: inspect.isclass(member) and member.__module__ == module_path)
    # classes_in_module is a tuple of lists (class_name:str, class_obj:class)
    if len(classes_in_module) == 1:
        selected_class_name = [pair[0] for pair in classes_in_module][0]
        selected_class = [pair[1] for pair in classes_in_module][0]
    elif len(classes_in_module) > 1:
        # If there is more than one class defined in a module, find a closest one by name.
        cutoff = 1
        selected_class_name = ''
        all_found_class_names = [x[0] for x in classes_in_module]
        while not selected_class_name:
            selected_class_name = difflib.get_close_matches(class_name, all_found_class_names, n=1, cutoff=cutoff)
            cutoff -= reduction_step
        selected_class_name = selected_class_name[0]
        selected_class = classes_in_module[all_found_class_names.index(selected_class_name)][1]
        logger.warning("In the Module '%s' more than one Class provided '%s'. Selected by the most similar name: '%s'."
                       % (found_module, all_found_class_names, selected_class_name))
    else:
        msg = "The Module file '%s' does not contain any classes!" % found_module
        logger.error(msg)
        raise NameError(msg)
    where_import_was_called = inspect.stack()[1].filename[inspect.stack()[1].filename.rfind("/"):] + ":" + \
                              inspect.stack()[1].function
    logger.info("The '%s' Class from the '%s' Module was imported into '%s'."
                % (selected_class_name, module_path, where_import_was_called))
    return selected_class




