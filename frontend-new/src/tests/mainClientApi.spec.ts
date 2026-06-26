import { describe, it, expect, beforeEach, vi } from 'vitest';
import { of } from 'rxjs';

//  registry using vi.hoisted so Vitest has time to prepare it before the mocks run
const { eventCallbacks } = vi.hoisted(() => {
  return { eventCallbacks: {} as Record<string, Function> };
});

// mock the stomp rxjs
vi.mock('@stomp/rx-stomp', () => {
  return {
    RxStompRPC: function () {
      return {
        rpc: vi.fn().mockImplementation(({ destination, body, headers }) => {
          if (eventCallbacks[destination]) {
            const simulatedResponse = eventCallbacks[destination](body, headers);
            return of(simulatedResponse);
          }
          return of({ body: '{}' });
        }),
      };
    },
  };
});

// isolated top-level mock with a clean trailing semicolon
vi.mock('../shared/api/stomp.client', () => ({ stompClient: {} }));

// import main.client.store below the hoisting setup
import { startMain, getMainStatus, stopMain, downloadDump } from '../entities/main/api/main.client.store';

describe('MainClientApi - Full Test Suite', () => {
  
  beforeEach(() => {
    // clear out the properties inside the hoisted object
    for (const key in eventCallbacks) {
      delete eventCallbacks[key];
    }
  });

  // getMainStatus
  it('should trigger the status queue with an empty body', async () => {
    let calledWithBody = null;
    
    eventCallbacks['main_status_queue'] = (body: string) => {
      calledWithBody = body;
      return { body: '{"status": "running"}' }; 
    };

    getMainStatus();
    expect(calledWithBody).toBe('');
  });

  // stopMain
  it('should trigger the stop queue with an empty body', async () => {
    let queueWasHit = false;
    let calledWithBody = null;

    eventCallbacks['main_stop_queue'] = (body: string) => {
      queueWasHit = true;
      calledWithBody = body;
      return { body: '{}' };
    };

    stopMain();
    expect(queueWasHit).toBe(true);
    expect(calledWithBody).toBe('');
  });

  // startMain
  it('should send description payload to start queue', () => {
    let capturedPayload = '';
    
    eventCallbacks['main_start_queue'] = (body: string) => {
      capturedPayload = JSON.parse(body);
      return { body: '{}' };
    };

    startMain('Run Test Suite');

    expect(capturedPayload).toEqual({
      Method: 'GET',
      Description: 'Run Test Suite'
    });
  });

  //  downloadDump
  it('should return decoded data from download queue', async () => {
    eventCallbacks['main_download_dump_queue'] = () => {
      return {
        body: JSON.stringify({ status: 'ok', body: btoa('dump_data') })
      };
    };

    const result = await downloadDump('pkl');
    expect(result.object).toBe('dump_data');
  });
});