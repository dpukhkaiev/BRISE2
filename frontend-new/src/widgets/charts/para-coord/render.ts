import Plotly from 'plotly.js-dist-min'
import type { PointExp } from '../../../entities/main/model/plot.store'
import { ref } from 'vue'
import type { ExperimentDescription } from "../../../entities/experiment/model/experiment.model";

function factoryDimension(
    parameter: string,
    allRes: PointExp[],
    experiment_description: ExperimentDescription
) {
    const values = allRes.map(
        point => point.configurations[parameter]
    );

    const dimension: any = {
        label: parameter.replace(/_/g, " ")
    };

    const firstValue = values.find(v => v !== undefined);

    if (typeof firstValue === "number") {
        dimension.values = values;

        const numericValues = values.filter(
            (value): value is number => typeof value === "number"
        );

        dimension.range = [
            Math.min(...numericValues),
            Math.max(...numericValues)
        ];
    }
    else {
        const searchSpace =
            experiment_description.Context?.SearchSpace?.[parameter];

        let categories: string[];

        // Use the Categories order for ordinal parameters
        if (
            searchSpace?.Type === "OrdinalHyperparameter" &&
            Array.isArray(searchSpace.Categories)
        ) {
            categories = searchSpace.Categories;
        }
        else {
            // Normal categorical parameter:
            // preserve the order in which values occur
            categories = Array.from(
                new Set(
                    values.filter(
                        (value): value is string =>
                            value !== undefined
                    )
                )
            );
        }

        dimension.values = values.map(
            value => categories.indexOf(value)
        );

        dimension.tickvals = categories.map(
            (_, index) => index
        );

        dimension.ticktext = categories.map(
            category => {
                // Make the labels more readable:
                // Context.SearchSpace.frequency.fourteen_hundred_hertz
                // -> fourteen hundred hertz
                const lastPart = category.split(".").pop() ?? category;

                return lastPart.replace(/_/g, " ");
            }
        );

        dimension.range = [0, categories.length - 1];
    }

    return dimension;
}

function dimensionsData(
    allRes: PointExp[],
    paraCoordParams: string[],
    paraCoordObjective: string,
    experiment_description: ExperimentDescription
) {
    const dimensions = paraCoordParams.map(
        parameter =>
            factoryDimension(
                parameter,
                allRes,
                experiment_description
            )
    );

    const objectiveValues = allRes.map(
        point => Number(point.results[paraCoordObjective])
    );

    dimensions.push({
        label: paraCoordObjective,
        values: objectiveValues
    });

    return dimensions;
}

export function renderParaCoord(
    element: HTMLElement,
    allRes: PointExp[],
    paraCoordParams: string[],
    paraCoordObjective: string,
    experiment_description: ExperimentDescription
) {
    if (
        allRes.length === 0 ||
        paraCoordParams.length === 0 ||
        !paraCoordObjective
    ) {
        Plotly.purge(element);
        return;
    }

    const objectiveValues = allRes.map(
        point => Number(point.results[paraCoordObjective])
    );

    const trace = [{
        type: 'parcoords' as const,

        line: {
            showscale: true,
            colorscale: 'Jet',
            color: objectiveValues
        },

        dimensions: dimensionsData(
            allRes,
            paraCoordParams,
            paraCoordObjective,
            experiment_description
        )
    }];

    const layout = {
        margin: {
            l: 150,
        },

        title: {
            text: 'Parallel Coordinates',
            font: {
                size: 20
            },
            xref: 'paper' as const,
            x: 0.05,
        }
    };

    Plotly.react(element, trace, layout);
}