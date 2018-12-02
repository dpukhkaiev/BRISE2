export class Task {
    id: string = '';
    run: Run;
    config: Configuration;
    meta: MetaData;
    constructor(item) {
        this.id = item.id;
        this.run = item.run;
        this.config = item.config;
        this.meta = item.meta_data;
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

