export class Task {
    id: string = '';
    run: Run;
    config: Configuration;
    stub_config: Array<any>;
    meta: MetaData;
    constructor(item) {
      this.id = item[0].results["task id"];
      this.run = item[0].run;
      this.config = item[0].configurations;
      this.meta = item[0].results;
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

export interface Solution {
    configurations: Array<any>;
    results: Array<any>;
    'measured points': Array<Number>
    'performed_measurements': number
}

