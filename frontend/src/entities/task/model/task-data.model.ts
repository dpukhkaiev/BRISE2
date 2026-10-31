// represents raw server data (response) for a single task (item)
interface TaskData {
    run: Run,
    configurations: Configuration,
    results: MetaData,

}

export class Task {
    id: string = '';
    run: Run;
    config: Configuration;
    // missing in constructor in initial code, here: allowing undefined
    stub_config: Array<any> | undefined;
    meta: MetaData;
    // TODO: temporarily solution
    roundedResults: Record<string, any> = {};
    constructor(item: TaskData[]) {
        // Guard for checking if item[0] empty
        if (!item[0]) {
            throw new Error('Item array may not be empty');
        }
        this.id = item[0].results["task id"];
        this.run = item[0].run;
        this.config = item[0].configurations;
        this.meta = item[0].results;
        this.roundedResults = {};
        for (const [result_key, result_value] of Object.entries(item[0].results.result)) {
            this.roundedResults[result_key] = typeof result_value === 'number'
                ? result_value.toPrecision(3)
                : result_value
        }
    }
}



interface MetaData {
    //could not find them in the received events
    // "accept": number,
    //"appointment": String,
    "owner": String,
    "receive": number,
    "result": { [key: string]: number }
    "task id": any
    "worker": string,
}

interface Configuration {
    ws_file?: String
}

interface Run {
    "method": String,
    "param": any
}

export interface Solution {
    configurations: Array<any>;
    results: Array<any>;
    'measured points': Array<Number>
    'performed_measurements': number
}
