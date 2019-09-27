import datetime


def convert_to_seconds(time_unit, time_value):
    """
    :param time_unit: the time unit, which need to be converted to seconds
    :param time_value: time value in defined time units
    :return: converted into seconds input time value
    """
    time_converted = datetime.timedelta(**{time_unit: time_value}).total_seconds()
    
    return time_converted
