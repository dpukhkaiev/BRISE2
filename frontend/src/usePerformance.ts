export function usePerformance(name: string) {
    const start = () => performance.mark(`${name}-start`);
    const end = () => {
        performance.mark(`${name}-end`);
        performance.measure(name, `${name}-start`, `${name}-end`);
        const measure = performance.getEntriesByName(name).pop();
        console.log(`Experiment "${name}" was: ${measure?.duration.toFixed(2)}ms`);
    };
    return { start, end };
}