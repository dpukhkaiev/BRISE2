import { Component, OnInit } from '@angular/core';

import {MatBottomSheet, MatBottomSheetRef} from '@angular/material';
import {MainClientService} from "../../core/services/main.client.service";
import {saveAs} from 'file-saver';


@Component({
  selector: 'download-pop-up',
  templateUrl: './download-pop-up.html',
  styleUrls: ['./download-pop-up.scss']
})
export class DownloadPopUp {
  constructor(
    private bottomSheetRef: MatBottomSheetRef<DownloadPopUp>,
    private eventService: MainClientService
  ) {
  }

  async downDump(format): Promise<any> {
    const res = await this.eventService.downloadDump(format)
    if (res['status'] === 'ok') {
      const byteString = res['body'];
      const arrayBuffer = new ArrayBuffer(byteString.length);
      const int8Array = new Uint8Array(arrayBuffer);
      for (let i = 0; i < byteString.length; i++) {
        int8Array[i] = byteString.charCodeAt(i);
      }
      const blob = new Blob([int8Array]);
      saveAs(blob, res['file_name']);
      let a = document.createElement('a');
      document.body.appendChild(a);
      a.setAttribute('style', 'display: none');
      a.target = '_blank'
      a.click();
      a.remove();
      this.bottomSheetRef.dismiss();
    }
  }
}
