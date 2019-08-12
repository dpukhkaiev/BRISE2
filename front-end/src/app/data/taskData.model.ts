export class Task {
    id: string = '';
    run: Run;
    config: Configuration;
    meta: MetaData;
    constructor(item) {
        this.id = item.task[0].results["task id"];
        this.run = item.task[0].run;
        this.config = item.task[0].configurations;
        this.meta = item.task[0].results;
    }
}
interface MetaData {
    "accept": number,
    "appointment": String,
    "owner": String,
    "receive": number,
    "result": any
}

interface Configuration {
    ws_file: String
}

interface Run {
    "method": String,
    "param": any
}

interface Results {
    'threads': String,
    'frequency': String,
    'energy': number,
    'time': number
}

export interface Solution {
    configurations: Array<any>;
    results: Array<any>;
    'measured points': Array<Number>
    'performed_measurements': number
} 

