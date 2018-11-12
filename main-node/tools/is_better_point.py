def is_better_point(is_minimization_experiment, solution_candidate_label, best_solution_label):
    if is_minimization_experiment is True:
        if solution_candidate_label < best_solution_label:
            return True
        elif solution_candidate_label > best_solution_label:
            return False
    elif is_minimization_experiment is False:
        if solution_candidate_label > best_solution_label:
            return True
        elif solution_candidate_label < best_solution_label:
            return False