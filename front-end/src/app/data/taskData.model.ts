export class Task {
    id: string = '';
    run: object = {};
    conf: object = {};
    meta: object = {};
    constructor(item) {
        this.id = item.id;
        this.run = item.run;
        this.conf = item.conf;
        this.meta = item.meta;
    }

    clear() {
        this.id = '';
        this.run = {};
        this.conf = {};
        this.meta = {};
    }
}
