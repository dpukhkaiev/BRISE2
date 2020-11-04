export class Task {
    id: string = '';
    run: Run;
    config: Configuration;
    stub_config: Array<any>;
    meta: MetaData;
    roundedResults: Object;
    constructor(item) {
      this.id = item[0].results["task id"];
      this.run = item[0].run;
      this.config = item[0].configurations;
      this.meta = item[0].results;
      // Suggested in https://github.com/dpukhkaiev/BRISEv2/pull/145#discussion_r440138361
      // Calculates precision class to properly round and display results.
      this.roundedResults = new Object();
      for (let [result_key, result_value] of Object.entries(item[0].results.result)){
        if(typeof result_value == 'number'){
          result_value = result_value.toPrecision(3);
        }
        this.roundedResults[result_key] = result_value;
      }
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

