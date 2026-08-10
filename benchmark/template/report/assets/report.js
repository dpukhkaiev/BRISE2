// BRISE Benchmark Report - Interactive Features

function showTab(id, btn) {
    document.querySelectorAll('.tab-content').forEach(function(e) {
        e.style.display = 'none';
    });
    document.getElementById(id).style.display = 'block';
    document.querySelectorAll('.tab-btn').forEach(function(b) {
        b.classList.remove('active');
    });
    btn.classList.add('active');
    setTimeout(function() {
        document.querySelectorAll('.js-plotly-plot').forEach(function(p) {
            if(p.offsetParent !== null) Plotly.Plots.resize(p);
        });
    }, 50);
}

// Enhanced Export Configuration System
const currentExportConfig = {
    containerId: null,
    plotDiv: null,
    fileName: '',
    width: 1200,
    height: 600,
    legendPosition: null,
    legendColumns: 1
};

const legendPositions = {
    'top-left': {x: 0.02, y: 0.98, xanchor: 'left', yanchor: 'top'},
    'top-center': {x: 0.5, y: 0.98, xanchor: 'center', yanchor: 'top'},
    'top-right': {x: 0.98, y: 0.98, xanchor: 'right', yanchor: 'top'},
    'middle-left': {x: 0.02, y: 0.5, xanchor: 'left', yanchor: 'middle'},
    'middle-right': {x: 0.98, y: 0.5, xanchor: 'right', yanchor: 'middle'},
    'bottom-left': {x: 0.02, y: 0.02, xanchor: 'left', yanchor: 'bottom'},
    'bottom-center': {x: 0.5, y: 0.02, xanchor: 'center', yanchor: 'bottom'},
    'bottom-right': {x: 0.98, y: 0.02, xanchor: 'right', yanchor: 'bottom'},
    'outside-right': {x: 1.02, y: 1, xanchor: 'left', yanchor: 'top'},
    'outside-bottom': {x: 0.5, y: -0.2, xanchor: 'center', yanchor: 'top'}
};

function isOutsidePosition(position) {
    return typeof position === 'string' && position.indexOf('outside') === 0;
}

function updateDimensions() {
    const width = parseFloat(document.getElementById('export-width').value);
    const height = parseFloat(document.getElementById('export-height').value);

    currentExportConfig.width = Math.round(width);
    currentExportConfig.height = Math.round(height);
}

function applyPreset() {
    const presetKey = document.getElementById('preset-select').value;
    if (presetKey === 'current') {
        document.getElementById('export-width').value = 1200;
        document.getElementById('export-height').value = 600;
        currentExportConfig.width = 1200;
        currentExportConfig.height = 600;
    }
}

function selectLegendPosition(position, el) {
    document.querySelectorAll('.legend-pos').forEach(function(e) {
        e.classList.remove('selected');
    });
    el.classList.add('selected');
    currentExportConfig.legendPosition = position;
}

function toggleLegendColumns(btn) {
    const twoColumns = currentExportConfig.legendColumns !== 2;
    currentExportConfig.legendColumns = twoColumns ? 2 : 1;
    btn.classList.toggle('active', twoColumns);
}

function exportPlotAsSVG(containerId, fileName) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error('Container not found:', containerId);
        return;
    }
    const plotDiv = container.querySelector('.js-plotly-plot');
    if (!plotDiv) {
        console.error('Plotly plot not found in container:', containerId);
        return;
    }

    // Store current config
    currentExportConfig.containerId = containerId;
    currentExportConfig.plotDiv = plotDiv;
    currentExportConfig.fileName = fileName;
    currentExportConfig.width = 1200;
    currentExportConfig.height = 600;

    // Reset dialog
    document.getElementById('export-width').value = 1200;
    document.getElementById('export-height').value = 600;
    document.getElementById('preset-select').value = 'current';
    document.querySelectorAll('.legend-pos').forEach(function(el) {
        el.classList.remove('selected');
    });
    currentExportConfig.legendPosition = null;

    var columnsToggle = document.getElementById('legend-columns-toggle');
    if (columnsToggle) columnsToggle.classList.remove('active');
    currentExportConfig.legendColumns = 1;

    // Show dialog
    document.getElementById('export-dialog').classList.add('active');
}

function closeExportDialog() {
    document.getElementById('export-dialog').classList.remove('active');
}

// Larger fonts for the exported figure (the on-screen plot is left untouched).
const EXPORT_FONT_SIZE = 18;              // base font (plot title, annotations, fallback)
const EXPORT_TICK_FONT_SIZE = 20;         // axis tick numbers
const EXPORT_LEGEND_FONT_SIZE = 22;
const EXPORT_AXIS_TITLE_FONT_SIZE = 22;   // axis title labels ("x label" / "y label")
// Two-column layout tunables (px).
const LEGEND_NUM_COLUMNS = 2;       // entries are split across this many columns
const LEGEND_COLUMN_GAP_PX = 18;    // horizontal gap between columns
const LEGEND_MARKER_PX = 30;        // width of an entry's colour marker + padding
const LEGEND_PAD_PX = 10;           // padding between the entries and the box edge
const LEGEND_ROW_PX = Math.round(EXPORT_LEGEND_FONT_SIZE * 1.8);  // height of one entry
// Plotly legend coords are fractions of the plotting area, which is smaller than
// the full figure. These conservative ratios keep the columns from overlapping.
const PLOT_AREA_W_RATIO = 0.8;
const PLOT_AREA_H_RATIO = 0.8;

// Measure rendered text width in px, reusing a single canvas context.
let _measureCtx = null;
function measureTextWidthPx(text) {
    if (!_measureCtx) _measureCtx = document.createElement('canvas').getContext('2d');
    _measureCtx.font = EXPORT_LEGEND_FONT_SIZE + 'px "Open Sans", verdana, arial, sans-serif';
    return _measureCtx.measureText(String(text || '')).width;
}

// Lay the legend entries out as a single boxed grid of vertical columns. Each
// column is a separate (transparent) Plotly legend placed by measured width, and
// one rectangle shape is drawn behind them so it reads as one clean legend.
// Returns false when there is nothing to split. Mutates `data`, `layout`.
function applyColumnLegend(layout, data, base) {
    const indices = [];
    data.forEach(function(trace, i) {
        if (trace.showlegend !== false && trace.name) indices.push(i);
    });
    if (indices.length < LEGEND_NUM_COLUMNS) return false;

    const perColumn = Math.ceil(indices.length / LEGEND_NUM_COLUMNS);
    const columns = [];
    for (let c = 0; c < LEGEND_NUM_COLUMNS; c++) {
        columns.push(indices.slice(c * perColumn, (c + 1) * perColumn));
    }

    const areaW = currentExportConfig.width * PLOT_AREA_W_RATIO;
    const areaH = currentExportConfig.height * PLOT_AREA_H_RATIO;
    const columnWidthsPx = columns.map(function(col) {
        const widest = Math.max.apply(null, col.map(function(i) { return measureTextWidthPx(data[i].name); }));
        return widest + LEGEND_MARKER_PX;
    });
    const maxRows = Math.max.apply(null, columns.map(function(col) { return col.length; }));

    const contentWpx = columnWidthsPx.reduce(function(a, b) { return a + b; }, 0)
        + LEGEND_COLUMN_GAP_PX * (LEGEND_NUM_COLUMNS - 1);
    const boxW = (contentWpx + 2 * LEGEND_PAD_PX) / areaW;
    const boxH = (maxRows * LEGEND_ROW_PX + 2 * LEGEND_PAD_PX) / areaH;

    // Box top-left corner in paper coords, derived from the chosen anchor.
    const boxLeft = base.xanchor === 'right' ? base.x - boxW
                  : base.xanchor === 'center' ? base.x - boxW / 2 : base.x;
    const boxTop = base.yanchor === 'bottom' ? base.y + boxH
                 : base.yanchor === 'middle' ? base.y + boxH / 2 : base.y;

    layout.shapes = (layout.shapes || []).concat([{
        type: 'rect', xref: 'paper', yref: 'paper', layer: 'above',
        x0: boxLeft, x1: boxLeft + boxW, y0: boxTop - boxH, y1: boxTop,
        fillcolor: 'rgba(255,255,255,0.85)', line: {color: 'rgba(0,0,0,0.2)', width: 1}
    }]);

    // Anchor each column at the box's vertical centre so the entries stay
    // centred inside the box instead of overflowing past its bottom edge.
    const common = {
        font: {size: EXPORT_LEGEND_FONT_SIZE},
        bgcolor: 'rgba(0,0,0,0)', borderwidth: 0, tracegroupgap: 0,
        xanchor: 'left', yanchor: 'middle', y: boxTop - boxH / 2
    };
    let cursorX = boxLeft + LEGEND_PAD_PX / areaW;
    columns.forEach(function(col, c) {
        const key = c === 0 ? 'legend' : 'legend' + (c + 1);
        col.forEach(function(i) { data[i].legend = key; });
        layout[key] = Object.assign({}, common, {x: cursorX});
        cursorX += columnWidthsPx[c] / areaW + LEGEND_COLUMN_GAP_PX / areaW;
    });
    return true;
}

// Build the export-only legend/font overrides. Mutates the passed-in clones
// (rendered off-screen) so the on-screen plot is untouched.
function enlargeAxisTitle(layout, key) {
    const axis = Object.assign({}, layout[key]);
    // Plotly title can be a bare string or a {text, font} object; normalise it.
    const title = typeof axis.title === 'string' ? {text: axis.title}
                                                 : Object.assign({}, axis.title);
    title.font = Object.assign({}, title.font, {size: EXPORT_AXIS_TITLE_FONT_SIZE});
    axis.title = title;
    // Tick numbers otherwise inherit the global font; give them a dedicated size.
    axis.tickfont = Object.assign({}, axis.tickfont, {size: EXPORT_TICK_FONT_SIZE});
    layout[key] = axis;
}

function applyExportOverrides(layout, data) {
    layout.font = Object.assign({}, layout.font, {size: EXPORT_FONT_SIZE});
    enlargeAxisTitle(layout, 'xaxis');
    enlargeAxisTitle(layout, 'yaxis');

    const legend = Object.assign({}, layout.legend);
    legend.font = Object.assign({}, legend.font, {size: EXPORT_LEGEND_FONT_SIZE});

    const position = currentExportConfig.legendPosition;
    const hasPosition = position && position !== 'current';
    const base = hasPosition ? legendPositions[position]
                             : {x: 1.02, y: 1, xanchor: 'left', yanchor: 'top'};

    if (currentExportConfig.legendColumns === 2 && applyColumnLegend(layout, data, base)) {
        return;
    }

    if (hasPosition) {
        Object.assign(legend, base);
        // Inside-the-plot legends need a backdrop so they stay readable over data.
        if (!isOutsidePosition(position)) {
            legend.bgcolor = 'rgba(255,255,255,0.8)';
            legend.bordercolor = 'rgba(0,0,0,0.2)';
            legend.borderwidth = 1;
        }
    }

    layout.legend = legend;
}

function performExport() {
    const filename = currentExportConfig.fileName;
    const width = Math.round(currentExportConfig.width);
    const height = Math.round(currentExportConfig.height);

    // Render the export off-screen from clones so the on-screen plot is untouched.
    const data = JSON.parse(JSON.stringify(currentExportConfig.plotDiv.data));
    const layout = JSON.parse(JSON.stringify(currentExportConfig.plotDiv.layout));
    applyExportOverrides(layout, data);

    const stage = document.createElement('div');
    stage.style.cssText = 'position:absolute;left:-9999px;top:0;width:' + width + 'px;height:' + height + 'px;';
    document.body.appendChild(stage);

    const cleanup = function() {
        Plotly.purge(stage);
        stage.remove();
    };

    Plotly.newPlot(stage, data, layout, {staticPlot: true})
        .then(function() {
            return Plotly.downloadImage(stage, {format: 'svg', width: width, height: height, filename: filename});
        })
        .then(function() {
            cleanup();
            closeExportDialog();
        })
        .catch(function(err) {
            console.error('Export failed:', err);
            cleanup();
        });
}

window.addEventListener('load', function() {
    setTimeout(function() {
        document.querySelectorAll('.js-plotly-plot').forEach(function(p) {
            Plotly.Plots.resize(p);
        });
    }, 100);
});

