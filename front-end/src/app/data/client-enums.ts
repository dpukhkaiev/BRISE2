// Socket.io events
export enum Event {
    CONNECT = 'connect',
    DISCONNECT = 'disconnect'
}

export enum MainEvent {
    CONNECT = 'connect',
    DISCONNECT = 'disconnect',
    EXPERIMENT = 'experiment',
    DEFAULT= 'default',
    NEW = 'new',
    PREDICTIONS = 'predictions',
    FINAL = 'final',
    LOG = 'log'
}

export const SubEvent = {
    EXPERIMENT: ['description'],
    DEFAULT: ['configuration'],
    NEW: ['task', 'configuration'],
    PREDICTIONS: ['configurations'],
    FINAL: ['configuration'],
    LOG: ['info', 'debug', 'critical']
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


