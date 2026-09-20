export const MainEvent = {
    CONNECT: 'connect',
    DISCONNECT: 'disconnect',
    EXPERIMENT: 'experiment',
    DEFAULT: 'default',
    NEW: 'new',
    PREDICTIONS: 'predictions',
    FINAL: 'final',
    LOG: 'log'
} as const;
// eslint-disable-next-line no-redeclare
export type MainEvent = typeof MainEvent[keyof typeof MainEvent];

export const SubEvent = {
    EXPERIMENT: ['description'],
    DEFAULT: ['configuration'],
    NEW: ['task', 'configuration'],
    PREDICTIONS: ['configurations'],
    FINAL: ['configuration'],
    LOG: ['info', 'debug', 'critical']
}


