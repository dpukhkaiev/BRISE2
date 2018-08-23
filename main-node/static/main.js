(window["webpackJsonp"] = window["webpackJsonp"] || []).push([["main"],{

/***/ "./src/$$_lazy_route_resource lazy recursive":
/*!**********************************************************!*\
  !*** ./src/$$_lazy_route_resource lazy namespace object ***!
  \**********************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

function webpackEmptyAsyncContext(req) {
	// Here Promise.resolve().then() is used instead of new Promise() to prevent
	// uncaught exception popping up in devtools
	return Promise.resolve().then(function() {
		var e = new Error("Cannot find module '" + req + "'");
		e.code = 'MODULE_NOT_FOUND';
		throw e;
	});
}
webpackEmptyAsyncContext.keys = function() { return []; };
webpackEmptyAsyncContext.resolve = webpackEmptyAsyncContext;
module.exports = webpackEmptyAsyncContext;
webpackEmptyAsyncContext.id = "./src/$$_lazy_route_resource lazy recursive";

/***/ }),

/***/ "./src/app/app.component.html":
/*!************************************!*\
  !*** ./src/app/app.component.html ***!
  \************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<!--The content below is only a placeholder and can be replaced.-->\n<div>\n  <div class=\"wrapper\">\n    <h1>\n      [logo] BRISE 2.0\n    </h1>\n    <h4>Benchmark Reduction Via Adaptive Instance Selection</h4>\n    <mat-tab-group>\n      \n      <!-- TAB 1 -->\n      <mat-tab label=\"Heat map\">\n        <hm-2></hm-2>\n        <hm-reg></hm-reg>\n      </mat-tab>\n\n      <!-- TAB 2 -->\n      <mat-tab label=\"Info\">\n        <info-board></info-board>  \n      </mat-tab>\n\n      <!-- Tab 3 -->\n      <mat-tab label=\"Tasks\">\n        <app-task-list> </app-task-list>\n      </mat-tab>\n\n    </mat-tab-group>\n  </div>\n</div>\n\n\n"

/***/ }),

/***/ "./src/app/app.component.scss":
/*!************************************!*\
  !*** ./src/app/app.component.scss ***!
  \************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ".wrapper {\n  max-width: 1200px;\n  margin: 10px auto; }\n\nh1 {\n  color: #673AB7; }\n\nh4 {\n  color: #FF4081; }\n"

/***/ }),

/***/ "./src/app/app.component.ts":
/*!**********************************!*\
  !*** ./src/app/app.component.ts ***!
  \**********************************/
/*! exports provided: AppComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AppComponent", function() { return AppComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};

var AppComponent = /** @class */ (function () {
    function AppComponent() {
    }
    AppComponent.prototype.ngOnInit = function () { };
    AppComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-root',
            template: __webpack_require__(/*! ./app.component.html */ "./src/app/app.component.html"),
            styles: [__webpack_require__(/*! ./app.component.scss */ "./src/app/app.component.scss")]
        }),
        __metadata("design:paramtypes", [])
    ], AppComponent);
    return AppComponent;
}());



/***/ }),

/***/ "./src/app/app.module.ts":
/*!*******************************!*\
  !*** ./src/app/app.module.ts ***!
  \*******************************/
/*! exports provided: AppModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AppModule", function() { return AppModule; });
/* harmony import */ var _angular_platform_browser__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/platform-browser */ "./node_modules/@angular/platform-browser/fesm5/platform-browser.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_http__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/http */ "./node_modules/@angular/http/fesm5/http.js");
/* harmony import */ var _core_core_module__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./core/core.module */ "./src/app/core/core.module.ts");
/* harmony import */ var _shared_shared_module__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./shared/shared.module */ "./src/app/shared/shared.module.ts");
/* harmony import */ var _app_component__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./app.component */ "./src/app/app.component.ts");
/* harmony import */ var _components_charts_heat_map_heat_map_component__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./components/charts/heat-map/heat-map.component */ "./src/app/components/charts/heat-map/heat-map.component.ts");
/* harmony import */ var _components_charts_heat_map_reg_heat_map_reg_component__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./components/charts/heat-map-reg/heat-map-reg.component */ "./src/app/components/charts/heat-map-reg/heat-map-reg.component.ts");
/* harmony import */ var _components_task_list_task_list_component__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ./components/task-list/task-list.component */ "./src/app/components/task-list/task-list.component.ts");
/* harmony import */ var _components_info_board_info_board_component__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! ./components/info-board/info-board.component */ "./src/app/components/info-board/info-board.component.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};



// Modules


// Intro

/* Charts */




var AppModule = /** @class */ (function () {
    function AppModule() {
    }
    AppModule = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["NgModule"])({
            declarations: [
                _app_component__WEBPACK_IMPORTED_MODULE_5__["AppComponent"],
                _components_task_list_task_list_component__WEBPACK_IMPORTED_MODULE_8__["TaskListComponent"],
                _components_charts_heat_map_heat_map_component__WEBPACK_IMPORTED_MODULE_6__["HeatMapComponent"],
                _components_charts_heat_map_heat_map_component__WEBPACK_IMPORTED_MODULE_6__["HeatMapComponent"],
                _components_charts_heat_map_reg_heat_map_reg_component__WEBPACK_IMPORTED_MODULE_7__["HeatMapRegComponent"],
                _components_info_board_info_board_component__WEBPACK_IMPORTED_MODULE_9__["InfoBoardComponent"]
            ],
            imports: [
                _angular_platform_browser__WEBPACK_IMPORTED_MODULE_0__["BrowserModule"], _angular_http__WEBPACK_IMPORTED_MODULE_2__["HttpModule"],
                _core_core_module__WEBPACK_IMPORTED_MODULE_3__["CoreModule"],
                _shared_shared_module__WEBPACK_IMPORTED_MODULE_4__["SharedModule"]
            ],
            providers: [],
            bootstrap: [_app_component__WEBPACK_IMPORTED_MODULE_5__["AppComponent"]]
        })
    ], AppModule);
    return AppModule;
}());



/***/ }),

/***/ "./src/app/components/charts/heat-map-reg/heat-map-reg.component.css":
/*!***************************************************************************!*\
  !*** ./src/app/components/charts/heat-map-reg/heat-map-reg.component.css ***!
  \***************************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ""

/***/ }),

/***/ "./src/app/components/charts/heat-map-reg/heat-map-reg.component.html":
/*!****************************************************************************!*\
  !*** ./src/app/components/charts/heat-map-reg/heat-map-reg.component.html ***!
  \****************************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<mat-card *ngIf=y&&x>\n    <div class=\"select-box\">\n        <!-- select color -->\n        <mat-form-field>\n            <mat-select [(value)]=\"theme.color\" (selectionChange)=\"regrRender()\" placeholder=\"Color\">\n                <mat-option *ngFor=\"let col of colors\" [value]=\"col\">\n                    {{col}}\n                </mat-option>\n            </mat-select>\n        </mat-form-field>\n        <!-- select type -->\n        <mat-form-field>\n            <mat-select [(value)]=\"theme.type\" (selectionChange)=\"regrRender()\" placeholder=\"Type\">\n                <mat-option *ngFor=\"let t of type\" [value]=\"t\">\n                    {{t}}\n                </mat-option>\n            </mat-select>\n        </mat-form-field>\n        <!-- select smooth -->\n        <mat-form-field>\n            <mat-select [(value)]=\"theme.smooth\" (selectionChange)=\"regrRender()\" placeholder=\"Smooth\">\n                <mat-option *ngFor=\"let s of smooth\" [value]=\"s\">\n                    {{s}}\n                </mat-option>\n            </mat-select>\n        </mat-form-field>\n    </div>\n    <div #reg></div>\n</mat-card>"

/***/ }),

/***/ "./src/app/components/charts/heat-map-reg/heat-map-reg.component.ts":
/*!**************************************************************************!*\
  !*** ./src/app/components/charts/heat-map-reg/heat-map-reg.component.ts ***!
  \**************************************************************************/
/*! exports provided: HeatMapRegComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "HeatMapRegComponent", function() { return HeatMapRegComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _core_services_main_socket_service__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../../../core/services/main.socket.service */ "./src/app/core/services/main.socket.service.ts");
/* harmony import */ var _data_client_enums__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../../data/client-enums */ "./src/app/data/client-enums.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};

// Service


// Plot



var HeatMapRegComponent = /** @class */ (function () {
    function HeatMapRegComponent(ioMain) {
        this.ioMain = ioMain;
        // Variables
        this.prediction = new Map();
        this.solution = { 'x': undefined, 'y': undefined };
        this.measured = { 'x': [], 'y': [] };
        // Default theme
        this.theme = {
            type: _data_client_enums__WEBPACK_IMPORTED_MODULE_2__["PlotType"][0],
            color: _data_client_enums__WEBPACK_IMPORTED_MODULE_2__["Color"][0],
            smooth: _data_client_enums__WEBPACK_IMPORTED_MODULE_2__["Smooth"][0]
        };
        this.type = _data_client_enums__WEBPACK_IMPORTED_MODULE_2__["PlotType"];
        this.colors = _data_client_enums__WEBPACK_IMPORTED_MODULE_2__["Color"];
        this.smooth = _data_client_enums__WEBPACK_IMPORTED_MODULE_2__["Smooth"];
    }
    HeatMapRegComponent.prototype.ngOnInit = function () {
        this.initMainConnection();
    };
    // Rendering
    HeatMapRegComponent.prototype.regrRender = function () {
        console.log("Reg render>", this.prediction);
        var regresion = this.reg.nativeElement;
        var data = [
            {
                // z: [[1, 20, 30], [20, 1, 60], [30, 60, 1]],
                z: this.zParser(this.prediction),
                x: this.x.map(String),
                y: this.y.map(String),
                type: this.theme.type,
                colorscale: this.theme.color,
                zsmooth: this.theme.smooth
            },
            {
                type: 'scatter',
                mode: 'markers',
                marker: { color: 'Gold', size: 12, symbol: 'star-open-dot' },
                x: this.solution.x,
                y: this.solution.y
            },
            {
                type: 'scatter',
                mode: 'markers',
                marker: { color: 'grey', size: 9, symbol: 'cross' },
                x: this.measured.x,
                y: this.measured.y
            }
        ];
        var layout = {
            title: 'Regresion',
            xaxis: { title: "Frequency",
                type: 'category',
                autorange: true,
                range: [Math.min.apply(Math, this.x), Math.max.apply(Math, this.x)]
            },
            yaxis: { title: "Threads",
                type: 'category',
                autorange: true,
                range: [Math.min.apply(Math, this.y), Math.max.apply(Math, this.y)] }
        };
        Plotly.newPlot(regresion, data, layout);
    };
    HeatMapRegComponent.prototype.zParser = function (data) {
        var _this = this;
        var z = [];
        this.y.forEach(function (y) {
            var row = [];
            _this.x.forEach(function (x) {
                row.push(data.get(String([x, y])));
            });
            z.push(row);
        });
        return z;
    };
    // Init conection
    HeatMapRegComponent.prototype.initMainConnection = function () {
        var _this = this;
        this.ioMain.onEmptyEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_2__["MainEvent"].CONNECT)
            .subscribe(function () {
            console.log(' reg.main: reg connected');
        });
        this.ioMain.onEmptyEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_2__["MainEvent"].DISCONNECT)
            .subscribe(function () {
            console.log(' reg.main: reg disconnected');
        });
        // ---- Main events
        this.ioMain.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_2__["MainEvent"].BEST)
            .subscribe(function (obj) {
            console.log(' Socket: BEST', obj);
            _this.solution.x = obj['best point']['configuration'][0];
            _this.solution.y = obj['best point']['configuration'][1];
            _this.measured.x = obj['best point']['measured points'].map(function (arr) { return arr[0]; });
            _this.measured.y = obj['best point']['measured points'].map(function (arr) { return arr[1]; });
            console.log("Measured", _this.measured.x, _this.measured.y);
            _this.regrRender();
        });
        this.ioMain.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_2__["MainEvent"].MAIN_CONF)
            .subscribe(function (obj) {
            _this.globalConfig = obj['global_config'];
            _this.taskConfig = obj['task'];
            _this.x = obj['task']['DomainDescription']['AllConfigurations'][0]; // frequency
            _this.y = obj['task']['DomainDescription']['AllConfigurations'][1]; // threads
        });
        this.ioMain.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_2__["MainEvent"].REGRESION)
            .subscribe(function (obj) {
            console.log(' Socket: REGRESION', obj);
            obj['regression'].map(function (point) {
                _this.prediction.set(String(point['configuration']), point['prediction']);
            });
            _this.regrRender();
        });
    };
    __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["ViewChild"])('reg'),
        __metadata("design:type", _angular_core__WEBPACK_IMPORTED_MODULE_0__["ElementRef"])
    ], HeatMapRegComponent.prototype, "reg", void 0);
    HeatMapRegComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'hm-reg',
            template: __webpack_require__(/*! ./heat-map-reg.component.html */ "./src/app/components/charts/heat-map-reg/heat-map-reg.component.html"),
            styles: [__webpack_require__(/*! ./heat-map-reg.component.css */ "./src/app/components/charts/heat-map-reg/heat-map-reg.component.css")]
        }),
        __metadata("design:paramtypes", [_core_services_main_socket_service__WEBPACK_IMPORTED_MODULE_1__["MainSocketService"]])
    ], HeatMapRegComponent);
    return HeatMapRegComponent;
}());



/***/ }),

/***/ "./src/app/components/charts/heat-map/heat-map.component.html":
/*!********************************************************************!*\
  !*** ./src/app/components/charts/heat-map/heat-map.component.html ***!
  \********************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<mat-card>\n  <h3>Experiment:</h3>\n  <div class=\"button-row\">\n    <button mat-button (click)=\"startMain()\" [disabled]=\"isRuning\" color=\"primary\">Start</button>\n    <button mat-button (click)=\"stopMain()\" [disabled]=\"!isRuning\" color=\"warn\">Stop</button>\n    <mat-progress-bar mode=\"indeterminate\" *ngIf=isRuning></mat-progress-bar>\n  </div>\n\n  <div class=\"select-box\" *ngIf=y&&x>\n    <!-- select color -->\n    <mat-form-field>\n      <mat-select [(value)]=\"theme.color\" (selectionChange)=\"render()\" placeholder=\"Color\">\n        <mat-option *ngFor=\"let col of colors\" [value]=\"col\">\n          {{col}}\n        </mat-option>\n      </mat-select>\n    </mat-form-field>\n    <!-- select type -->\n    <mat-form-field>\n      <mat-select [(value)]=\"theme.type\" (selectionChange)=\"render()\" placeholder=\"Type\">\n        <mat-option *ngFor=\"let t of type\" [value]=\"t\">\n          {{t}}\n        </mat-option>\n      </mat-select>\n    </mat-form-field>\n    <!-- select smooth -->\n    <mat-form-field>\n      <mat-select [(value)]=\"theme.smooth\" (selectionChange)=\"render()\" placeholder=\"Smooth\">\n        <mat-option *ngFor=\"let s of smooth\" [value]=\"s\">\n          {{s}}\n        </mat-option>\n      </mat-select>\n    </mat-form-field>\n    <mat-card *ngIf=\"solution\" class=\"chart-solution\">\n      <mat-icon matListIcon>star</mat-icon>\n      <span>Solution: </span> <h3>{{solution.configuration}}</h3>\n      <span>Result deviation: </span> <h3>{{(solution.result/default_task.result-1)*100 | number:'2.0-0'}}%</h3>\n    </mat-card>\n  </div>\n  <!-- ================  Heat map  ================ -->\n  <div #map></div>\n  <!-- ============================================ -->\n</mat-card>\n\n\n\n\n"

/***/ }),

/***/ "./src/app/components/charts/heat-map/heat-map.component.scss":
/*!********************************************************************!*\
  !*** ./src/app/components/charts/heat-map/heat-map.component.scss ***!
  \********************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "h3 {\n  color: #212121; }\n\n.select-box {\n  display: flex;\n  flex-wrap: wrap;\n  justify-content: flex-start;\n  align-items: flex-start;\n  margin-top: 12px; }\n\n.select-box .chart-solution {\n    display: flex;\n    margin-left: 20px;\n    align-items: center;\n    padding: 15px 20px;\n    border-left: 3px solid #757575; }\n\n.select-box .chart-solution > mat-icon {\n      color: #757575; }\n\n.select-box .chart-solution span {\n      margin: 0 10px;\n      color: #212121; }\n\n.select-box .chart-solution h3 {\n      color: #FF4081;\n      margin: 0 4px; }\n"

/***/ }),

/***/ "./src/app/components/charts/heat-map/heat-map.component.ts":
/*!******************************************************************!*\
  !*** ./src/app/components/charts/heat-map/heat-map.component.ts ***!
  \******************************************************************/
/*! exports provided: HeatMapComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "HeatMapComponent", function() { return HeatMapComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _core_services_ws_socket_service__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../../../core/services/ws.socket.service */ "./src/app/core/services/ws.socket.service.ts");
/* harmony import */ var _core_services_main_socket_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../../core/services/main.socket.service */ "./src/app/core/services/main.socket.service.ts");
/* harmony import */ var _core_services_rest_service__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../../../core/services/rest.service */ "./src/app/core/services/rest.service.ts");
/* harmony import */ var _data_client_enums__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../../../data/client-enums */ "./src/app/data/client-enums.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};

// Service
// import { RestService } from '../../services/worker.service';





// Plot



var HeatMapComponent = /** @class */ (function () {
    function HeatMapComponent(mainREST, ioWs, ioMain) {
        this.mainREST = mainREST;
        this.ioWs = ioWs;
        this.ioMain = ioMain;
        // The experements results
        this.result = new Map();
        // The prediction results from model
        this.prediction = new Map();
        // Flag for runing main-node
        this.isRuning = false;
        // Measured points for the Regresion model from worker-service
        this.measPoints = [];
        this.default_task = { 'conf': '', 'result': 0 };
        // Default theme
        this.theme = {
            type: _data_client_enums__WEBPACK_IMPORTED_MODULE_4__["PlotType"][0],
            color: _data_client_enums__WEBPACK_IMPORTED_MODULE_4__["Color"][0],
            smooth: _data_client_enums__WEBPACK_IMPORTED_MODULE_4__["Smooth"][0]
        };
        this.type = _data_client_enums__WEBPACK_IMPORTED_MODULE_4__["PlotType"];
        this.colors = _data_client_enums__WEBPACK_IMPORTED_MODULE_4__["Color"];
        this.smooth = _data_client_enums__WEBPACK_IMPORTED_MODULE_4__["Smooth"];
    }
    HeatMapComponent.prototype.ngOnInit = function () {
        this.initWsEvents();
        this.initMainEvents();
    };
    HeatMapComponent.prototype.zParser = function (data) {
        var _this = this;
        // Parse the answears in to array of Y rows
        var z = [];
        this.y.forEach(function (y) {
            var row = [];
            _this.x.forEach(function (x) {
                row.push(data.get(String([x, y])));
            });
            z.push(row);
        });
        return z;
    };
    HeatMapComponent.prototype.render = function () {
        var element = this.map.nativeElement;
        var data = [
            {
                z: this.zParser(this.result),
                x: this.x.map(String),
                y: this.y.map(String),
                type: this.theme.type,
                colorscale: this.theme.color,
                zsmooth: this.theme.smooth
            },
            {
                type: 'scatter',
                mode: 'markers',
                marker: { color: 'Gold', size: 16, symbol: 'star-dot' },
                x: this.solution && [this.solution.configuration[0]],
                y: this.solution && [this.solution.configuration[1]]
            },
            {
                type: 'scatter',
                mode: 'markers',
                marker: { color: 'grey', size: 7, symbol: 'cross' },
                x: this.measPoints.map(function (arr) { return arr[0]; }),
                y: this.measPoints.map(function (arr) { return arr[1]; })
            }
        ];
        var layout = {
            title: 'Heat map results',
            showlegend: false,
            xaxis: {
                title: "Frequency",
                type: 'category',
                autorange: true,
                range: [Math.min.apply(Math, this.x), Math.max.apply(Math, this.x)],
                showgrid: true
            },
            yaxis: {
                title: "Threads",
                type: 'category',
                autorange: true,
                range: [Math.min.apply(Math, this.y), Math.max.apply(Math, this.y)],
                showgrid: true
            }
        };
        Plotly.newPlot(element, data, layout);
    };
    //                              WebSocket
    // --------------------------   Worker-service
    HeatMapComponent.prototype.initWsEvents = function () {
        var _this = this;
        this.ioWs.initSocket();
        // Fresh updates. Each time +1 task
        // this.ioConnection = this.io.onResults()
        //   .subscribe((obj: JSON) => {
        //     var fresh: Task = new Task(obj)
        //     var r = fresh.hasOwnProperty('meta') && fresh['meta']['result']
        //     var delta = !!r && [r['threads'], r['frequency'], r['energy']]
        //     !this.result.includes(delta, -1) && this.result.push(delta);
        //     // console.log("---- Delta", delta)
        //   });
        // Observer for stack and all results from workers service
        // this.ioConnection = this.io.onAllResults()
        //   .subscribe((obj: any) => {
        //     console.log("onAllResults ::", JSON.parse(obj))
        //     var data = JSON.parse(obj)
        //     this.result = (data.hasOwnProperty('res') && data['res'].length) ? data['res'].map((t) => new Task(t)) : [];
        //   });
        this.ioWs.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["Event"].CONNECT)
            .subscribe(function () {
            console.log(' hm2.workerService: connected');
            _this.ioWs.reqForAllRes();
        });
        this.ioWs.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["Event"].DISCONNECT)
            .subscribe(function () {
            console.log(' hm2.workerService: disconnected');
        });
    };
    //                              WebSocket
    // --------------------------   Main-node
    HeatMapComponent.prototype.initMainEvents = function () {
        var _this = this;
        this.ioMain.onEmptyEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["MainEvent"].CONNECT)
            .subscribe(function () {
            console.log(' hm.main: connected');
        });
        this.ioMain.onEmptyEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["MainEvent"].DISCONNECT)
            .subscribe(function () {
            console.log(' hm.main: disconnected');
        });
        // ----                     Main events
        this.ioMain.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["MainEvent"].DEFAULT_CONF)
            .subscribe(function (obj) {
            console.log(' Socket: DEFAULT_task', obj);
            _this.default_task.conf = obj['conf'];
            _this.default_task.result = obj['result'];
            _this.result.set(String(obj['conf']), obj['result']);
            _this.measPoints.push(obj['conf']);
            _this.render();
        });
        this.ioMain.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["MainEvent"].BEST)
            .subscribe(function (obj) {
            console.log(' Socket: BEST', obj);
            _this.solution = obj['best point'];
            _this.render();
        });
        this.ioMain.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["MainEvent"].INFO)
            .subscribe(function (obj) {
            console.log(' Socket: INFO', obj);
        });
        this.ioMain.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["MainEvent"].MAIN_CONF)
            .subscribe(function (obj) {
            _this.globalConfig = obj['global_config'];
            _this.taskConfig = obj['task'];
            _this.x = obj['task']['DomainDescription']['AllConfigurations'][0]; // frequency
            _this.y = obj['task']['DomainDescription']['AllConfigurations'][1]; // threads
            console.log(' Socket: MAIN_CONF', obj);
        });
        this.ioMain.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["MainEvent"].TASK_RESULT)
            .subscribe(function (obj) {
            _this.result.set(String(obj['configuration']), obj['result']);
            _this.measPoints.push(obj['configuration']);
            _this.render();
        });
    };
    // HTTP: Main-node
    HeatMapComponent.prototype.startMain = function () {
        var _this = this;
        if (this.isRuning == false) {
            this.mainREST.startMain()
                .subscribe(function (res) {
                console.log('Main start:', res);
                _this.isRuning = true;
            });
        }
    };
    HeatMapComponent.prototype.stopMain = function () {
        var _this = this;
        if (this.isRuning == true) {
            this.mainREST.stopMain()
                .subscribe(function (res) {
                console.log('Main stop:', res);
                _this.isRuning = false;
            });
        }
    };
    __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["ViewChild"])('map'),
        __metadata("design:type", _angular_core__WEBPACK_IMPORTED_MODULE_0__["ElementRef"])
    ], HeatMapComponent.prototype, "map", void 0);
    HeatMapComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'hm-2',
            template: __webpack_require__(/*! ./heat-map.component.html */ "./src/app/components/charts/heat-map/heat-map.component.html"),
            styles: [__webpack_require__(/*! ./heat-map.component.scss */ "./src/app/components/charts/heat-map/heat-map.component.scss")]
        }),
        __metadata("design:paramtypes", [_core_services_rest_service__WEBPACK_IMPORTED_MODULE_3__["RestService"],
            _core_services_ws_socket_service__WEBPACK_IMPORTED_MODULE_1__["WsSocketService"],
            _core_services_main_socket_service__WEBPACK_IMPORTED_MODULE_2__["MainSocketService"]])
    ], HeatMapComponent);
    return HeatMapComponent;
}());



/***/ }),

/***/ "./src/app/components/info-board/info-board.component.html":
/*!*****************************************************************!*\
  !*** ./src/app/components/info-board/info-board.component.html ***!
  \*****************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<mat-accordion>\n  <!-- Panel 1 -->\n  <mat-expansion-panel [disabled]=\"!news\">\n    <mat-expansion-panel-header>\n      <mat-panel-title>\n        Info messages\n      </mat-panel-title>\n      <mat-panel-description>\n         Basic information from the workflow of experiments ({{news ? news.size : '0'}})\n         <mat-icon \n          matBadge='news.size' \n          matBadgeColor=\"accent\" \n          matBadgePosition=\"above befor\">\n          input\n          </mat-icon>\n      </mat-panel-description>\n    </mat-expansion-panel-header>\n    <!-- Logs list  -->\n    <ng-template matExpansionPanelContent>\n      <mat-list dense role=\"list\" *ngIf=news>\n        <mat-list-item role=\"listitem\" *ngFor=\"let info of news\">\n          <mat-icon mat-list-icon>done</mat-icon>\n          <p mat-line>{{info.message}}</p>\n          <mat-divider></mat-divider>\n          <p class=\"time\" mat-line> {{info.time | date:'shortTime'}} </p>\n        </mat-list-item>\n      </mat-list>\n    </ng-template>\n  </mat-expansion-panel>\n\n  <!-- Panel 2 -->\n  <mat-expansion-panel [disabled]=\"!solution\">\n    <mat-expansion-panel-header>\n      <mat-panel-title>\n        Solution \n      </mat-panel-title>\n      <mat-panel-description>\n         A solution that is found by BRISE ({{solution ? 'Done' : 'Please stand by..'}})\n         <mat-icon>star_rate</mat-icon>\n      </mat-panel-description>\n    </mat-expansion-panel-header>\n    <ng-template matExpansionPanelContent>\n      <mat-list class=\"solution\">\n        <mat-list-item>\n          <mat-icon matListIcon>outlined_flag</mat-icon>\n          <span class=\"desc\">Configuration: </span> <span>{{solution.configuration}}</span>\n        </mat-list-item>\n        <mat-list-item>\n          <mat-icon matListIcon>grade</mat-icon>\n          <span class=\"desc\">Result: </span> <span>{{solution.result}}</span>\n        </mat-list-item>\n        <mat-list-item>\n          <mat-icon matListIcon>network_check</mat-icon>\n          <span class=\"desc\">Deviation result from default: </span> <span>{{100*(solution.result - default_task.result)/default_task.result | number:'2.0-0'}}%</span>\n        </mat-list-item>\n        <mat-list-item>\n          <mat-icon matListIcon>blur_on</mat-icon>\n          <span class=\"desc\">Measured points: </span> <span>{{solution['measured points'].length}}</span>\n        </mat-list-item>\n        <mat-list-item>\n          <mat-icon matListIcon>sentiment_satisfied_alt</mat-icon>\n          <span class=\"desc\">Saved efforts: </span> <span>\n            {{\n              (1 - solution['measured points'].length/(taskConfig['DomainDescription']['AllConfigurations'][0].length*taskConfig['DomainDescription']['AllConfigurations'][1].length))*100 |number:'2.0-0'\n            }}%\n        </span>\n        </mat-list-item>\n      </mat-list>\n    </ng-template>\n  </mat-expansion-panel>\n</mat-accordion>"

/***/ }),

/***/ "./src/app/components/info-board/info-board.component.scss":
/*!*****************************************************************!*\
  !*** ./src/app/components/info-board/info-board.component.scss ***!
  \*****************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ".time {\n  color: #BDBDBD; }\n\n.mat-expansion-panel-header-title,\n.mat-expansion-panel-header-description {\n  flex-basis: 0; }\n\n.mat-expansion-panel-header-description {\n  justify-content: space-between;\n  align-items: center; }\n\nmat-panel-title {\n  color: #512DA8; }\n\nmat-panel-description mat-icon {\n  color: #FF4081; }\n\nmat-list-item mat-icon {\n  color: #757575; }\n\n.solution mat-icon {\n  color: #FF4081; }\n\n.solution .desc {\n  color: rgba(33, 33, 33, 0.54);\n  font-size: .95em;\n  vertical-align: middle;\n  margin-right: 5px; }\n\n.solution .desc + span {\n    font-weight: 400; }\n"

/***/ }),

/***/ "./src/app/components/info-board/info-board.component.ts":
/*!***************************************************************!*\
  !*** ./src/app/components/info-board/info-board.component.ts ***!
  \***************************************************************/
/*! exports provided: InfoBoardComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "InfoBoardComponent", function() { return InfoBoardComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_material__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/material */ "./node_modules/@angular/material/esm5/material.es5.js");
/* harmony import */ var _core_services_ws_socket_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../core/services/ws.socket.service */ "./src/app/core/services/ws.socket.service.ts");
/* harmony import */ var _core_services_main_socket_service__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../../core/services/main.socket.service */ "./src/app/core/services/main.socket.service.ts");
/* harmony import */ var _data_client_enums__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../../data/client-enums */ "./src/app/data/client-enums.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};

// Material

// Service


// Constant

var InfoBoardComponent = /** @class */ (function () {
    function InfoBoardComponent(ioWs, ioMain, snackBar) {
        this.ioWs = ioWs;
        this.ioMain = ioMain;
        this.snackBar = snackBar;
        // Steps for expansion. Material.angular
        this.panelOpenState = false;
        // Information log
        this.news = new Set();
    }
    InfoBoardComponent.prototype.ngOnInit = function () {
        this.initMainEvents();
    };
    InfoBoardComponent.prototype.initMainEvents = function () {
        var _this = this;
        this.ioMain.onEmptyEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["MainEvent"].CONNECT)
            .subscribe(function () {
            console.log(' info.main: connected');
        });
        this.ioMain.onEmptyEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["MainEvent"].DISCONNECT)
            .subscribe(function () {
            console.log(' info.main: disconnected');
        });
        // ----                     Main events
        this.ioMain.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["MainEvent"].DEFAULT_CONF)
            .subscribe(function (obj) {
            _this.default_task = obj;
            var temp = { 'time': Date.now(), 'message': 'Measured default configuration' };
            _this.snackBar.open(temp['message'], '×', {
                duration: 3000
            });
            _this.news.add(temp);
        });
        this.ioMain.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["MainEvent"].BEST)
            .subscribe(function (obj) {
            _this.solution = obj['best point'];
            var temp = {
                'time': Date.now(),
                'message': '★★★ The optimum result is found. The best point is reached ★★★'
            };
            _this.snackBar.open(temp['message'], '×', {
                duration: 3000
            });
            _this.news.add(temp);
        });
        this.ioMain.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["MainEvent"].INFO)
            .subscribe(function (obj) {
            console.log(' Socket: INFO', obj);
            var temp = { 'time': Date.now(), 'message': obj['message'] };
            _this.snackBar.open(temp['message'], '×', {
                duration: 3000
            });
            _this.news.add(temp);
        });
        this.ioMain.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["MainEvent"].MAIN_CONF)
            .subscribe(function (obj) {
            _this.globalConfig = obj['global_config'];
            _this.taskConfig = obj['task'];
            var temp = {
                'time': Date.now(),
                'message': 'The main configurations of the experiment are obtained.Let\'s go!'
            };
            _this.snackBar.open(temp['message'], '×', {
                duration: 3000
            });
            _this.news.add(temp);
        });
        this.ioMain.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["MainEvent"].TASK_RESULT)
            .subscribe(function (obj) {
            var temp = {
                'time': Date.now(),
                'message': 'New results for ' + String(obj['configuration'])
            };
            _this.snackBar.open(temp['message'], '×', {
                duration: 3000
            });
            _this.news.add(temp);
        });
        this.ioMain.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["MainEvent"].REGRESION)
            .subscribe(function (obj) {
            var temp = {
                'time': Date.now(),
                'message': 'Regression obtained. ' + obj['regression'].length + ' predictions'
            };
            _this.snackBar.open(temp['message'], '×', {
                duration: 3000
            });
            _this.news.add(temp);
        });
    };
    InfoBoardComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'info-board',
            template: __webpack_require__(/*! ./info-board.component.html */ "./src/app/components/info-board/info-board.component.html"),
            styles: [__webpack_require__(/*! ./info-board.component.scss */ "./src/app/components/info-board/info-board.component.scss")]
        }),
        __metadata("design:paramtypes", [_core_services_ws_socket_service__WEBPACK_IMPORTED_MODULE_2__["WsSocketService"],
            _core_services_main_socket_service__WEBPACK_IMPORTED_MODULE_3__["MainSocketService"],
            _angular_material__WEBPACK_IMPORTED_MODULE_1__["MatSnackBar"]])
    ], InfoBoardComponent);
    return InfoBoardComponent;
}());



/***/ }),

/***/ "./src/app/components/task-list/task-list.component.html":
/*!***************************************************************!*\
  !*** ./src/app/components/task-list/task-list.component.html ***!
  \***************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div class=\"box\">\n  <mat-card class=\"stack\">                                     <!-- STACK list -->\n    <mat-card-header>\n      <h3>Stack {{stack?.length}}</h3>\n    </mat-card-header> \n    <mat-card-content>\n      <mat-list dense role=\"list\" *ngIf=stack>\n        <mat-list-item *ngFor=\"let task of stack\" \n          (click)=\"taskInfo(task.id)\" role=\"listitem\" \n          [class.selected]=\"task.id === this.focus?.id\">\n          <mat-icon matListIcon>folder</mat-icon>\n          <h3 matLine> {{task.id.substr(0, 5)}} </h3>\n          <p matLine>\n            <span> {{task.run.param.frequency}} </span>\n            <span class=\"demo-2\"> -- {{task.run.param.threads}} </span>\n          </p>\n          <button mat-icon-button (click)=\"taskInfo(task.id)\">\n            <mat-icon>info</mat-icon>\n          </button>\n        </mat-list-item>\n      </mat-list>\n    </mat-card-content>\n  </mat-card>  <!-- end stack -->\n\n  <!-- RESULT list -->\n  <mat-card class=\"result\">   \n    <mat-card-header>\n      <h3>Result {{result?.length}}</h3>\n    </mat-card-header> \n    <mat-card-content>\n      <mat-list dense role=\"list\">\n        <mat-list-item *ngFor=\"let item of result\" \n            (click)=\"taskInfo(item.id)\" \n            role=\"listitem\"\n            [class.selected]=\"item.id === this.focus?.id\">\n            <mat-icon matListIcon>folder</mat-icon>\n            <h3 matLine> {{item.id.substr(0, 5)}} </h3>\n            <p matLine>\n              <span> {{item.run.param.frequency}} </span>\n              <span class=\"demo-2\"> -- {{item.run.param.threads}} </span>\n            </p>\n            <button mat-icon-button (click)=\"taskInfo(item.id)\">\n              <mat-icon>info</mat-icon>\n            </button>\n        </mat-list-item>\n      </mat-list>\n    </mat-card-content>\n  </mat-card>  <!-- end results -->\n\n  <mat-card class=\"focus\" *ngIf=focus>\n    <!-- FOCUS task. select from lists -->\n    <mat-card-actions>\n      <button mat-icon-button (click)=\"clearFocus()\">\n        <mat-icon>close</mat-icon>\n      </button>\n    </mat-card-actions>\n    <mat-card-title color=\"primary\">ID: {{focus.id.substr(0, 5)}}</mat-card-title>\n    <mat-tab-group>\n      <mat-tab label=\"Result\">\n        <mat-list role=\"list\">\n          <mat-list-item role=\"listitem\">\n            <mat-icon>gradient</mat-icon>\n            <span>Method: </span>\n            <span> {{focus.run.method}}</span>\n          </mat-list-item>\n          <mat-list-item role=\"listitem\">\n            <mat-icon>whatshot</mat-icon>\n            <span>Energy: </span>\n            <span> {{focus.meta_data.result.energy}}</span>\n          </mat-list-item>\n          <mat-list-item role=\"listitem\">\n            <mat-icon>memory</mat-icon>\n            <span>Frequency: </span>\n            <span> {{focus.meta_data.result.frequency}}</span>\n          </mat-list-item>\n          <mat-list-item role=\"listitem\">\n            <mat-icon>layers</mat-icon>\n            <span>Threads: </span>\n            <span> {{focus.meta_data.result.threads}}</span>\n          </mat-list-item>\n          <mat-list-item role=\"listitem\">\n            <mat-icon>timer</mat-icon>\n            <span>Time: </span>\n            <span> {{focus.meta_data.result.time}}</span>\n          </mat-list-item>\n        </mat-list>\n      </mat-tab>\n      <mat-tab label=\"Meta data\">\n        <mat-list role=\"list\">\n          <mat-list-item role=\"listitem\">\n            <mat-icon>rowing</mat-icon>\n            <span>Worker:</span>\n            <span>{{focus.meta_data.appointment}}</span>\n          </mat-list-item>\n          <mat-list-item role=\"listitem\">\n            <mat-icon>list</mat-icon>\n            <span>Accept:</span>\n            <span>{{focus.meta_data.accept}}</span>\n          </mat-list-item>\n          <mat-list-item role=\"listitem\">\n            <mat-icon>directions</mat-icon>\n            <span>Receive:</span>\n            <span>{{focus.meta_data.receive}}</span>\n          </mat-list-item>\n        </mat-list>\n      </mat-tab>\n    </mat-tab-group>\n  </mat-card>\n      <!-- end focus -->\n\n</div>\n"

/***/ }),

/***/ "./src/app/components/task-list/task-list.component.scss":
/*!***************************************************************!*\
  !*** ./src/app/components/task-list/task-list.component.scss ***!
  \***************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ".box {\n  display: flex;\n  flex-direction: row;\n  flex-wrap: wrap;\n  justify-content: space-around;\n  align-items: flex-start; }\n\n.stack, .result {\n  flex-grow: 2;\n  min-width: 250px; }\n\n/* Selected item */\n\n.selected {\n  font-weight: 700;\n  border-left: 2px solidr rgba(255, 64, 129, 0.9);\n  background: #00000014; }\n\n.selected .mat-list-icon {\n  color: rgba(0, 0, 0, 0.9); }\n\nmat-tab-body mat-grid-tile {\n  height: 100%; }\n\n/* Icons */\n\n.mat-list-icon {\n  color: rgba(189, 189, 189, 0.5); }\n\n.mat-icon {\n  color: rgba(189, 189, 189, 0.5); }\n\n.mat-icon + span {\n  color: rgba(189, 189, 189, 0.5);\n  font-size: .95em;\n  vertical-align: middle;\n  margin-right: 5px; }\n"

/***/ }),

/***/ "./src/app/components/task-list/task-list.component.ts":
/*!*************************************************************!*\
  !*** ./src/app/components/task-list/task-list.component.ts ***!
  \*************************************************************/
/*! exports provided: TaskListComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "TaskListComponent", function() { return TaskListComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _core_services_rest_service__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../../core/services/rest.service */ "./src/app/core/services/rest.service.ts");
/* harmony import */ var _core_services_ws_socket_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../core/services/ws.socket.service */ "./src/app/core/services/ws.socket.service.ts");
/* harmony import */ var _data_taskData_model__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../../data/taskData.model */ "./src/app/data/taskData.model.ts");
/* harmony import */ var _data_client_enums__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../../data/client-enums */ "./src/app/data/client-enums.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};

// Service




// import { resolve } from 'path';
var TaskListComponent = /** @class */ (function () {
    function TaskListComponent(ws, io) {
        this.ws = ws;
        this.io = io;
        this.stack = [];
        this.result = [];
    }
    TaskListComponent.prototype.ngOnInit = function () {
        this.initIoConnection();
    };
    TaskListComponent.prototype.clearFocus = function () {
        this.focus = null;
    };
    // --------------------- SOCKET ---------------
    TaskListComponent.prototype.initIoConnection = function () {
        var _this = this;
        this.io.initSocket();
        // Fresh updates. Each time +1 task
        this.ioConnection = this.io.onResults()
            .subscribe(function (obj) {
            var fresh = new _data_taskData_model__WEBPACK_IMPORTED_MODULE_3__["Task"](obj);
            !_this.result.includes(fresh, -1) && _this.result.push(fresh);
            // console.log(' Object:', obj);
        });
        // Rewrite task stack
        this.ioConnection = this.io.stack()
            .subscribe(function (obj) {
            _this.stack = obj;
            // console.log(' Stack:', obj);
        });
        // Observer for stack and all results from workers service
        this.ioConnection = this.io.onAllResults()
            .subscribe(function (obj) {
            console.log("onAllResults ::", JSON.parse(obj));
            var data = JSON.parse(obj);
            _this.result = (data.hasOwnProperty('res') && data['res'].length) ? data['res'].map(function (t) { return new _data_taskData_model__WEBPACK_IMPORTED_MODULE_3__["Task"](t); }) : [];
            _this.stack = (data.hasOwnProperty('stack') && data['stack'].length) ? data['stack'].map(function (t) { return new _data_taskData_model__WEBPACK_IMPORTED_MODULE_3__["Task"](t); }) : [];
        });
        this.io.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["Event"].CONNECT)
            .subscribe(function () {
            console.log(' task-list: connected');
            // get init data
            _this.io.reqForAllRes();
        });
        this.io.onEvent(_data_client_enums__WEBPACK_IMPORTED_MODULE_4__["Event"].DISCONNECT)
            .subscribe(function () {
            console.log(' task-list: disconnected');
        });
    };
    // ____________________________ HTTP _____
    TaskListComponent.prototype.taskInfo = function (id) {
        var _this = this;
        this.ws.getTaskById(id)
            .subscribe(function (res) {
            _this.focus = res["result"];
            _this.focus.time = res["time"];
        });
    };
    TaskListComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-task-list',
            template: __webpack_require__(/*! ./task-list.component.html */ "./src/app/components/task-list/task-list.component.html"),
            styles: [__webpack_require__(/*! ./task-list.component.scss */ "./src/app/components/task-list/task-list.component.scss")]
        }),
        __metadata("design:paramtypes", [_core_services_rest_service__WEBPACK_IMPORTED_MODULE_1__["RestService"], _core_services_ws_socket_service__WEBPACK_IMPORTED_MODULE_2__["WsSocketService"]])
    ], TaskListComponent);
    return TaskListComponent;
}());



/***/ }),

/***/ "./src/app/core/core.module.ts":
/*!*************************************!*\
  !*** ./src/app/core/core.module.ts ***!
  \*************************************/
/*! exports provided: CoreModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "CoreModule", function() { return CoreModule; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _services_rest_service__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./services/rest.service */ "./src/app/core/services/rest.service.ts");
/* harmony import */ var _services_ws_socket_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./services/ws.socket.service */ "./src/app/core/services/ws.socket.service.ts");
/* harmony import */ var _services_main_socket_service__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./services/main.socket.service */ "./src/app/core/services/main.socket.service.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
var __param = (undefined && undefined.__param) || function (paramIndex, decorator) {
    return function (target, key) { decorator(target, key, paramIndex); }
};

/* Shared Service */



var CoreModule = /** @class */ (function () {
    /* make sure CoreModule is imported only by one NgModule the AppModule */
    function CoreModule(parentModule) {
        if (parentModule) {
            throw new Error('CoreModule is already loaded. Import only in AppModule');
        }
    }
    CoreModule = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["NgModule"])({
            imports: [],
            providers: [
                { provide: _services_rest_service__WEBPACK_IMPORTED_MODULE_1__["RestService"], useClass: _services_rest_service__WEBPACK_IMPORTED_MODULE_1__["RestService"] },
                { provide: _services_ws_socket_service__WEBPACK_IMPORTED_MODULE_2__["WsSocketService"], useClass: _services_ws_socket_service__WEBPACK_IMPORTED_MODULE_2__["WsSocketService"] },
                { provide: _services_main_socket_service__WEBPACK_IMPORTED_MODULE_3__["MainSocketService"], useClass: _services_main_socket_service__WEBPACK_IMPORTED_MODULE_3__["MainSocketService"] }
            ],
            declarations: []
        }),
        __param(0, Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Optional"])()), __param(0, Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["SkipSelf"])()),
        __metadata("design:paramtypes", [CoreModule])
    ], CoreModule);
    return CoreModule;
}());



/***/ }),

/***/ "./src/app/core/services/main.socket.service.ts":
/*!******************************************************!*\
  !*** ./src/app/core/services/main.socket.service.ts ***!
  \******************************************************/
/*! exports provided: MainSocketService */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "MainSocketService", function() { return MainSocketService; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var rxjs_Observable__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! rxjs/Observable */ "./node_modules/rxjs-compat/_esm5/Observable.js");
/* harmony import */ var socket_io_client__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! socket.io-client */ "./node_modules/socket.io-client/lib/index.js");
/* harmony import */ var socket_io_client__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(socket_io_client__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _environments_environment__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../../../environments/environment */ "./src/environments/environment.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};




var SERVER_URL = _environments_environment__WEBPACK_IMPORTED_MODULE_3__["environment"].mainNode;
var MainSocketService = /** @class */ (function () {
    function MainSocketService() {
        this.socket = socket_io_client__WEBPACK_IMPORTED_MODULE_2__(SERVER_URL);
    }
    MainSocketService.prototype.onEvent = function (event) {
        var _this = this;
        return new rxjs_Observable__WEBPACK_IMPORTED_MODULE_1__["Observable"](function (observer) {
            _this.socket.on(event, function (data) { return observer.next(data); });
        });
    };
    MainSocketService.prototype.onEmptyEvent = function (event) {
        var _this = this;
        return new rxjs_Observable__WEBPACK_IMPORTED_MODULE_1__["Observable"](function (observer) {
            _this.socket.on(event, function () { return observer.next(); });
        });
    };
    MainSocketService = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Injectable"])({
            providedIn: 'root',
        }),
        __metadata("design:paramtypes", [])
    ], MainSocketService);
    return MainSocketService;
}());



/***/ }),

/***/ "./src/app/core/services/rest.service.ts":
/*!***********************************************!*\
  !*** ./src/app/core/services/rest.service.ts ***!
  \***********************************************/
/*! exports provided: RestService */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "RestService", function() { return RestService; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_http__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/http */ "./node_modules/@angular/http/fesm5/http.js");
/* harmony import */ var rxjs_Observable__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! rxjs/Observable */ "./node_modules/rxjs-compat/_esm5/Observable.js");
/* harmony import */ var rxjs_add_operator_map__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! rxjs/add/operator/map */ "./node_modules/rxjs-compat/_esm5/add/operator/map.js");
/* harmony import */ var rxjs_add_operator_catch__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! rxjs/add/operator/catch */ "./node_modules/rxjs-compat/_esm5/add/operator/catch.js");
/* harmony import */ var rxjs_add_observable_throw__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! rxjs/add/observable/throw */ "./node_modules/rxjs-compat/_esm5/add/observable/throw.js");
/* harmony import */ var _environments_environment__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ../../../environments/environment */ "./src/environments/environment.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};







var SERVICE_URL = _environments_environment__WEBPACK_IMPORTED_MODULE_6__["environment"].workerService;
var MAIN_URL = _environments_environment__WEBPACK_IMPORTED_MODULE_6__["environment"].mainNode;
var RestService = /** @class */ (function () {
    function RestService(http) {
        this.http = http;
        this.tasks = [];
    }
    RestService.prototype.handleError = function (error) {
        console.error('Handle Error:', error);
        return rxjs_Observable__WEBPACK_IMPORTED_MODULE_2__["Observable"].throw(error);
    };
    // ---------------------------------
    //                    Worker Service
    // GET /stack /* Observable<Task[]> */
    RestService.prototype.getStack = function () {
        return this.http
            .get(SERVICE_URL + '/stack')
            .map(function (response) {
            var tasks = response.json();
            return tasks /*.map((t) => new Task(t))*/;
        })
            .catch(this.handleError);
    };
    // GET /result/:id
    RestService.prototype.getTaskById = function (id) {
        return this.http
            .get(SERVICE_URL + '/result/' + id)
            .map(function (response) {
            var task = response.json();
            return task /*.map((t) => new Task)/*/;
        })
            .catch(this.handleError);
    };
    // GET all result
    RestService.prototype.getAllResult = function () {
        return this.http
            .get(SERVICE_URL + '/result/all')
            .map(function (response) {
            var res = response.json();
            return res /*.map((t) => new Task)/*/;
        })
            .catch(this.handleError);
    };
    // -----------------------------
    //                    Main-node
    RestService.prototype.startMain = function () {
        return this.http
            .get(MAIN_URL + '/main_start')
            .map(function (response) {
            var res = response.json();
            return res;
        })
            .catch(this.handleError);
    };
    RestService.prototype.getMainStatus = function () {
        return this.http
            .get(MAIN_URL + '/status')
            .map(function (response) {
            var res = response.json();
            return res;
        })
            .catch(this.handleError);
    };
    RestService.prototype.stopMain = function () {
        return this.http
            .get(MAIN_URL + '/main_stop')
            .map(function (response) {
            var res = response.json();
            return res;
        })
            .catch(this.handleError);
    };
    RestService = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Injectable"])(),
        __metadata("design:paramtypes", [_angular_http__WEBPACK_IMPORTED_MODULE_1__["Http"]])
    ], RestService);
    return RestService;
}());



/***/ }),

/***/ "./src/app/core/services/ws.socket.service.ts":
/*!****************************************************!*\
  !*** ./src/app/core/services/ws.socket.service.ts ***!
  \****************************************************/
/*! exports provided: WsSocketService */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "WsSocketService", function() { return WsSocketService; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var rxjs_Observable__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! rxjs/Observable */ "./node_modules/rxjs-compat/_esm5/Observable.js");
/* harmony import */ var socket_io_client__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! socket.io-client */ "./node_modules/socket.io-client/lib/index.js");
/* harmony import */ var socket_io_client__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(socket_io_client__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _environments_environment__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../../../environments/environment */ "./src/environments/environment.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};


// import { Observer } from 'rxjs/Observer';

// Variables

var SERVER_URL = _environments_environment__WEBPACK_IMPORTED_MODULE_3__["environment"].workerService;
var NAME_SPACE = _environments_environment__WEBPACK_IMPORTED_MODULE_3__["environment"].nameSpace;
var WsSocketService = /** @class */ (function () {
    function WsSocketService() {
    }
    WsSocketService.prototype.initSocket = function () {
        this.socket = socket_io_client__WEBPACK_IMPORTED_MODULE_2__(SERVER_URL + NAME_SPACE);
        this.socket.emit('join', { 'room': NAME_SPACE });
    };
    WsSocketService.prototype.reqForAllRes = function () {
        this.socket.emit('all result');
    };
    WsSocketService.prototype.onResults = function () {
        var _this = this;
        return new rxjs_Observable__WEBPACK_IMPORTED_MODULE_1__["Observable"](function (observer) {
            _this.socket.on('result', function (data) { return observer.next(data); });
        });
    };
    WsSocketService.prototype.stack = function () {
        var _this = this;
        return new rxjs_Observable__WEBPACK_IMPORTED_MODULE_1__["Observable"](function (observer) {
            _this.socket.on('stack', function (data) { return observer.next(data); });
        });
    };
    WsSocketService.prototype.onAllResults = function () {
        var _this = this;
        return new rxjs_Observable__WEBPACK_IMPORTED_MODULE_1__["Observable"](function (observer) {
            _this.socket.on('all result', function (data) { return observer.next(data); });
        });
    };
    WsSocketService.prototype.onEvent = function (event) {
        var _this = this;
        return new rxjs_Observable__WEBPACK_IMPORTED_MODULE_1__["Observable"](function (observer) {
            _this.socket.on(event, function () { return observer.next(); });
        });
    };
    WsSocketService = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Injectable"])({
            providedIn: 'root',
        }),
        __metadata("design:paramtypes", [])
    ], WsSocketService);
    return WsSocketService;
}());



/***/ }),

/***/ "./src/app/data/client-enums.ts":
/*!**************************************!*\
  !*** ./src/app/data/client-enums.ts ***!
  \**************************************/
/*! exports provided: Event, MainEvent, Color, PlotType, Smooth */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "Event", function() { return Event; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "MainEvent", function() { return MainEvent; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "Color", function() { return Color; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "PlotType", function() { return PlotType; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "Smooth", function() { return Smooth; });
// Socket.io events
var Event;
(function (Event) {
    Event["CONNECT"] = "connect";
    Event["DISCONNECT"] = "disconnect";
})(Event || (Event = {}));
var MainEvent;
(function (MainEvent) {
    MainEvent["CONNECT"] = "connect";
    MainEvent["DISCONNECT"] = "disconnect";
    MainEvent["BEST"] = "best point";
    MainEvent["DEFAULT_CONF"] = "default conf";
    MainEvent["MAIN_CONF"] = "main_config";
    MainEvent["REGRESION"] = "regression";
    MainEvent["TASK_RESULT"] = "task result";
    MainEvent["INFO"] = "info";
})(MainEvent || (MainEvent = {}));
var Color = ['Portland', 'Greens', 'Greys', 'YIGnBu',
    'RdBu', 'Jet', 'Hot', 'Picnic', 'Electric',
    'Bluered', 'YIOrRd', 'Blackbody', 'Earth'];
var PlotType = [
    'heatmap', 'contour', 'surface'
];
var Smooth = [
    false, "fast", "best"
];


/***/ }),

/***/ "./src/app/data/taskData.model.ts":
/*!****************************************!*\
  !*** ./src/app/data/taskData.model.ts ***!
  \****************************************/
/*! exports provided: Task */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "Task", function() { return Task; });
var Task = /** @class */ (function () {
    function Task(item) {
        this.id = '';
        this.run = {};
        this.conf = {};
        this.meta = {};
        this.id = item.id;
        this.run = item.run;
        this.conf = item.config;
        this.meta = item.meta_data;
    }
    Task.prototype.clear = function () {
        this.id = '';
        this.run = {};
        this.conf = {};
        this.meta = {};
    };
    return Task;
}());



/***/ }),

/***/ "./src/app/shared/shared.module.ts":
/*!*****************************************!*\
  !*** ./src/app/shared/shared.module.ts ***!
  \*****************************************/
/*! exports provided: SharedModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "SharedModule", function() { return SharedModule; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_common__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/common */ "./node_modules/@angular/common/fesm5/common.js");
/* harmony import */ var _angular_platform_browser_animations__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/platform-browser/animations */ "./node_modules/@angular/platform-browser/fesm5/animations.js");
/* harmony import */ var _angular_material__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @angular/material */ "./node_modules/@angular/material/esm5/material.es5.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};


// Animation

// Material

var SharedModule = /** @class */ (function () {
    function SharedModule() {
    }
    SharedModule = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["NgModule"])({
            imports: [
                _angular_common__WEBPACK_IMPORTED_MODULE_1__["CommonModule"],
                _angular_platform_browser_animations__WEBPACK_IMPORTED_MODULE_2__["BrowserAnimationsModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatButtonModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatCheckboxModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatCardModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatListModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatIconModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatTabsModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatTooltipModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatGridListModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatProgressBarModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatSelectModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatSnackBarModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatExpansionModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatBadgeModule"]
            ],
            declarations: [],
            exports: [
                _angular_common__WEBPACK_IMPORTED_MODULE_1__["CommonModule"],
                _angular_platform_browser_animations__WEBPACK_IMPORTED_MODULE_2__["BrowserAnimationsModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatButtonModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatCheckboxModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatCardModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatListModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatIconModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatTabsModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatTooltipModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatGridListModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatProgressBarModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatSelectModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatSnackBarModule"],
                _angular_material__WEBPACK_IMPORTED_MODULE_3__["MatExpansionModule"]
            ]
        })
    ], SharedModule);
    return SharedModule;
}());



/***/ }),

/***/ "./src/environments/environment.ts":
/*!*****************************************!*\
  !*** ./src/environments/environment.ts ***!
  \*****************************************/
/*! exports provided: environment */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "environment", function() { return environment; });
// The file contents for the current environment will overwrite these during build.
// The build system defaults to the dev environment which uses `environment.ts`, but if you do
// `ng build --env=prod` then `environment.prod.ts` will be used instead.
// The list of which env maps to which file can be found in `.angular-cli.json`.
var environment = {
    production: false,
    workerService: 'http://0.0.0.0:80',
    mainNode: 'http://0.0.0.0:9000',
    nameSpace: '/front-end'
};


/***/ }),

/***/ "./src/main.ts":
/*!*********************!*\
  !*** ./src/main.ts ***!
  \*********************/
/*! no exports provided */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_platform_browser_dynamic__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/platform-browser-dynamic */ "./node_modules/@angular/platform-browser-dynamic/fesm5/platform-browser-dynamic.js");
/* harmony import */ var _app_app_module__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./app/app.module */ "./src/app/app.module.ts");
/* harmony import */ var _environments_environment__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./environments/environment */ "./src/environments/environment.ts");
/* harmony import */ var hammerjs__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! hammerjs */ "./node_modules/hammerjs/hammer.js");
/* harmony import */ var hammerjs__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(hammerjs__WEBPACK_IMPORTED_MODULE_4__);




// Material

if (_environments_environment__WEBPACK_IMPORTED_MODULE_3__["environment"].production) {
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["enableProdMode"])();
}
Object(_angular_platform_browser_dynamic__WEBPACK_IMPORTED_MODULE_1__["platformBrowserDynamic"])().bootstrapModule(_app_app_module__WEBPACK_IMPORTED_MODULE_2__["AppModule"])
    .catch(function (err) { return console.log(err); });


/***/ }),

/***/ 0:
/*!***************************!*\
  !*** multi ./src/main.ts ***!
  \***************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

module.exports = __webpack_require__(/*! /home/oleksandr/Documents/hal/benchmark/front-end/src/main.ts */"./src/main.ts");


/***/ }),

/***/ 1:
/*!********************!*\
  !*** ws (ignored) ***!
  \********************/
/*! no static exports found */
/***/ (function(module, exports) {

/* (ignored) */

/***/ })

},[[0,"runtime","vendor"]]]);
//# sourceMappingURL=main.js.map