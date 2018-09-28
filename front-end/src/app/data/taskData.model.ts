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
    "result": Results
}

interface Configuration {
    ws_file: String
}

interface Run {
    "method": String,
    "param": {
        "frequency": number,
        "threads": number,
        "ws_file": string
    }
}

interface Results {
    'threads': String,
    'frequency': String,
    'energy': number,
    'time': number
}

export interface Solution {
    configuration: any;
    result: any;
    'measured points': Array<Number>
    'performed measurements': number
} 

