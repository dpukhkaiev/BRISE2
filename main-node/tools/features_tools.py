def split_features_and_labels(data, structure):
    """
        Splits mixture of features and labels according to provided structure.

    :param data: List of lists
            Mixture of features and labels. Could be like
        [[123.1, 32, 215.12], [123, 23, 124.1], [12.3, 124, 51]]

    :param structure: List of Strings.
            Description of features-labels mixture, what is what. E.g.
        ['feature, 'feature', 'label']

    :return: Two lists of lists.
    In this case split for example above will be
        ([[123.1, 32], [123, 23], [12.3, 124]], [[215.12], [124.1], [51]])
    """
    # need to rewrite it in normal way..

    results = {"features": [],
               "labels": []
               }

    for point in data:
        to_features = []
        to_labels = []
        for index, type in enumerate(structure):
            if type == '1' or 'feat' in type.lower():
                to_features.append(point[index])
            else:
                to_labels.append(point[index])
        results['features'].append(to_features)
        results['labels'].append(to_labels)
    return results['features'], results['labels']