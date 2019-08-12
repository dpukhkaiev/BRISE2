import { Component, OnInit } from '@angular/core';

import { MatBottomSheet, MatBottomSheetRef } from '@angular/material';
import { RestService as mainREST } from '../../core/services/rest.service';


@Component({
    selector: 'download-pop-up',
    templateUrl: './download-pop-up.html',
    styleUrls: ['./download-pop-up.scss']
})
export class DownloadPopUp {
    constructor(
        private bottomSheetRef: MatBottomSheetRef<DownloadPopUp>,
        private REST: mainREST
        ) { }

    downDump(format): any {
        this.REST.downloadDump(format)
            .subscribe((res) => {
                var a = document.createElement('a');
                document.body.appendChild(a);
                a.setAttribute('style', 'display: none');
                a.href = res.url;
                a.target = "_blank"
                a.click();
                a.remove();
                this.bottomSheetRef.dismiss();        
            }
            );    
    }
}