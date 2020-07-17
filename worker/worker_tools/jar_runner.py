import subprocess
from typing import List, Tuple


def jar_runner(jar_path, *call_args) -> Tuple[str, str, int]:
    """
    Calls the jar execution by running "java -jar *args" command as subprocess with provided arguments.
    :param jar_path: path to jar file
    :param call_args: arguments to call jar file
    :return: Lists of STD_OUT and STD_ERR messages, exit code of execution
    """
    try:
        process = subprocess.Popen(['java', '-jar', jar_path] + list(call_args),
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   close_fds=True)
        stdout_b, stderr_b = process.communicate()
        stdout = stdout_b.decode("UTF-8")
        stderr = stderr_b.decode("UTF-8")
        return_code = process.returncode

    except FileNotFoundError as error:
        stdout = ''
        stderr = str(error)
        return_code = 1

    return stdout, stderr, return_code
