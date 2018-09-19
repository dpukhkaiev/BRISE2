// Socket.io events
export enum Event {
    CONNECT = 'connect',
    DISCONNECT = 'disconnect'
}

export enum MainEvent {
    CONNECT = 'connect',
    DISCONNECT = 'disconnect',
    BEST = 'best point',
    DEFAULT_CONF = 'default conf',
    MAIN_CONF = 'main_config',
    REGRESION = 'regression',
    TASK_RESULT = 'task result',
    INFO = 'info'
}

export const Color = ['Portland', 'Greens', 'Greys', 'YIGnBu',
    'RdBu', 'Jet', 'Hot', 'Picnic', 'Electric',
    'Bluered', 'YIOrRd', 'Blackbody', 'Earth']

export const PlotType = [
    'heatmap', 'contour', 'surface'
]

export const Smooth = [
    false, "fast", "best"
]


