def split_features_and_labels(data, structure):
    """

    :param data:
    :param structure: list with
    :return:
    """
    # need to rewrite it in normal way..

    results = {"features": [],
               "labels": []
               }

    for point in data:
        to_features = []
        to_labels = []
        for index, type in enumerate(structure):
            if type == '1' or type == 'feature':
                to_features.append(point[index])
            else:
                to_labels.append(point[index])
        results['features'].append(to_features)
        results['labels'].append(to_labels)
    return results['features'], results['labels']