// Socket.io events
export enum Event {
    CONNECT = 'connect',
    DISCONNECT = 'disconnect'
}

export enum MainEvent {
    CONNECT = 'connect',
    DISCONNECT = 'disconnect',
    EXPERIMENT = 'experiment',
    TASK = 'task',
    LOG = 'log'
}

export const SubEvent = {
    EXPERIMENT: ['configuration'],
    TASK: ['default', 'new', 'predictions', 'final'],
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


