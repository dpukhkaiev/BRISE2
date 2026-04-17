import {downloadDump} from '@/entities/main/api/main.client.store'
import { saveAs } from 'file-saver'


export async function downloadPopUp(format: string): Promise<any> {
  const response = await downloadDump(format)
  if(response['status'] === 'ok') {
       const byteString = response['body'];
       const arrayBuffer = new ArrayBuffer(byteString.length)
       const int8Array = new Uint8Array(arrayBuffer);
      for (let i = 0; i < byteString.length; i++) {
        int8Array[i] = byteString.charCodeAt(i);
      }
      const blob = new Blob([int8Array]);
      saveAs(blob, response['file_name']);
    }
  }
