export class Task {
    id: string = '';
    run: object = {};
    conf: object = {};
    meta: object = {};
    constructor(item) {
        this.id = item.id;
        this.run = item.run;
        this.conf = item.config;
        this.meta = item.meta_data;
    }

    clear() {
        this.id = '';
        this.run = {};
        this.conf = {};
        this.meta = {};
    }
}

