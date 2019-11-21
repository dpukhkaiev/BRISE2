def correct_values(bandwidth, minimum_bandwidth, number_of_kernels, application_grid_size):
    # round bandwidth
    try:
        bandwidth = float(bandwidth)
        corrected_bandwidth = bandwidth
        if (bandwidth > 0.001 and bandwidth < 0.1):
            corrected_bandwidth = 0.001
        if (bandwidth > 0.1 and bandwidth < 0.5):
            corrected_bandwidth = 0.5
        if (bandwidth > 0.5 and bandwidth < 10):
            corrected_bandwidth = 10
        if (bandwidth > 10 and bandwidth < 100):
            corrected_bandwidth = 100
        if (bandwidth > 100):
            corrected_bandwidth = 1000
    except Exception:
        corrected_bandwidth = 0.5

    # round minimum bandwidth
    try:
        minimum_bandwidth = float(minimum_bandwidth)
        corrected_min_bandwidth = minimum_bandwidth
        if (minimum_bandwidth > 0.001 and minimum_bandwidth < 0.1):
            corrected_min_bandwidth = 0.001
        if (minimum_bandwidth > 0.1 and minimum_bandwidth < 0.5):
            corrected_min_bandwidth = 0.5
        if (minimum_bandwidth > 0.5 and minimum_bandwidth < 10):
            corrected_min_bandwidth = 10
        if (minimum_bandwidth > 10 and minimum_bandwidth < 100):
            corrected_min_bandwidth = 100
        if (minimum_bandwidth > 100):
            corrected_min_bandwidth = 1000
    except Exception:
        corrected_min_bandwidth = "None"

    # round number of kernels
    try:
        number_of_kernels = int(number_of_kernels)
        corrected_num_kernels = number_of_kernels
        if (number_of_kernels > 1 and number_of_kernels < 3):
            corrected_num_kernels = 1
        if (number_of_kernels > 3 and number_of_kernels < 50):
            corrected_num_kernels = 4
        if (number_of_kernels > 50 and number_of_kernels < 100):
            corrected_num_kernels = 100
        if (number_of_kernels > 100 and number_of_kernels < 500):
            corrected_num_kernels = 500
        if (number_of_kernels > 500):
            corrected_num_kernels = 1000
    except Exception:
        corrected_num_kernels = "None"

    # round app grid size
    try:
        application_grid_size = int(application_grid_size)
        corrected_app_grid_size = application_grid_size
        if (application_grid_size > 10 and application_grid_size < 30):
            corrected_app_grid_size = 10
        if (application_grid_size > 30 and application_grid_size < 50):
            corrected_app_grid_size = 50
        if (application_grid_size > 50 and application_grid_size < 100):
            corrected_app_grid_size = 100
        if (application_grid_size > 100 and application_grid_size < 500):
            corrected_app_grid_size = 500
        if (application_grid_size > 500):
            corrected_app_grid_size = 1000
    except Exception:
        corrected_app_grid_size = "None"
    return corrected_bandwidth, corrected_min_bandwidth, corrected_num_kernels, corrected_app_grid_size
