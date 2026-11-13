import type { PlotlyInstance } from '../model/chart.types'
import type { PointExp } from '../../../entities/main/model/plot.store'
// import { ref } from 'vue'
import type { ParameterSpec } from "../../../entities/experiment/model/experiment.model";
import { cleanIdentifier } from "../../../shared/lib";
import {
    INACTIVE_INDEX,
    INACTIVE_LABEL,
    inactivePosition,
    numericTicksWithInactive
} from "../../../entities/experiment/lib/inactive";

function factoryDimension(
    parameter: string,
    allRes: PointExp[],
    specsByName: Record<string, ParameterSpec>
) {
    const values = allRes.map(
        point => point.configurations[parameter]
    );

    const dimension: any = {
        label: cleanIdentifier(parameter).replace(/_/g, " ")
    };

    const firstValue = values.find(v => v !== undefined);

    const spec = specsByName[parameter];

    // a trial without the parameter is one in which it is inactive
    const hasInactive = values.some(value => value === undefined);

    const isNumeric = spec
        ? spec.Type === "FloatHyperparameter" || spec.Type === "IntegerHyperparameter"
        : typeof firstValue === "number";

    if (isNumeric) {
        // without a description of the parameter there is no inactive position to draw at
        dimension.values = spec
            ? values.map(value => value ?? inactivePosition(spec))
            : values;

        const numericValues = dimension.values.filter(
            (value: unknown): value is number => typeof value === "number"
        );

        dimension.range = [
            Math.min(...numericValues),
            Math.max(...numericValues)
        ];

        if (spec && hasInactive) {
            Object.assign(dimension, numericTicksWithInactive(spec));
        }
    }
    else {
        let categories: string[];

        // Use the Categories order for ordinal parameters
        if (
            spec?.Type === "OrdinalHyperparameter" &&
            Array.isArray(spec.Categories)
        ) {
            categories = spec.Categories;
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

        dimension.tickvals = [
            ...(hasInactive ? [INACTIVE_INDEX] : []),
            ...categories.map(
                (_, index) => index
            )
        ];

        dimension.ticktext = [
            ...(hasInactive ? [INACTIVE_LABEL] : []),
            ...categories.map(
                category => {
                    // Make the labels more readable:
                    // Context.SearchSpace.frequency.fourteen_hundred_hertz
                    // -> fourteen hundred hertz
                    const lastPart = category.split(".").pop() ?? category;

                    return lastPart.replace(/_/g, " ");
                }
            )
        ];

        dimension.range = [hasInactive ? INACTIVE_INDEX : 0, categories.length - 1];
    }

    return dimension;
}

function dimensionsData(
    allRes: PointExp[],
    paraCoordParams: string[],
    paraCoordObjective: string,
    specsByName: Record<string, ParameterSpec>
) {
    const dimensions = paraCoordParams.map(
        parameter =>
            factoryDimension(
                parameter,
                allRes,
                specsByName
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
    plotly: PlotlyInstance,
    element: HTMLElement,
    allRes: PointExp[],
    paraCoordParams: string[],
    paraCoordObjective: string,
    specsByName: Record<string, ParameterSpec>
) {
    if (
        allRes.length === 0 ||
        paraCoordParams.length === 0 ||
        !paraCoordObjective
    ) {
        plotly.purge(element);
        return;
    }

    const objectiveValues = allRes.map(
        point => Number(point.results[paraCoordObjective])
    );

    const trace = [{
        type: 'parcoords' as const,

        line: {
            showscale: true,
            colorscale: 'Portland',
            color: objectiveValues
        },

        dimensions: dimensionsData(
            allRes,
            paraCoordParams,
            paraCoordObjective,
            specsByName
        )
    }];

    const layout = {
        autosize: true,
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

    plotly.react(element, trace, layout);
}