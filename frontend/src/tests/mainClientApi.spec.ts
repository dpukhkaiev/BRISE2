import { describe, it, expect, beforeEach, vi } from 'vitest';
import { of } from 'rxjs';
import { parseJsonWithInfinity } from '../shared/lib';

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
import { startMain, getMainStatus, stopMain, downloadDump, calculatePlot } from '../entities/main/api/main.client.store';

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
    
    eventCallbacks['/queue/main_status_queue'] = (body: string) => {
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

    eventCallbacks['/queue/main_stop_queue'] = (body: string) => {
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
    
    eventCallbacks['/queue/main_start_queue'] = (body: string) => {
      capturedPayload = JSON.parse(body);
      return { body: '{}' };
    };

    startMain('Run Test Suite');

    expect(capturedPayload).toEqual({
      Method: 'GET',
      Description: 'Run Test Suite'
    });
  });

  // startMain with unbounded objective boundaries
  it('should preserve Infinity/-Infinity values in the description sent to the start queue', () => {
    let capturedBody = '';

    eventCallbacks['/queue/main_start_queue'] = (body: string) => {
      capturedBody = body;
      return { body: '{}' };
    };

    startMain({ MinExpectedValue: -Infinity, MaxExpectedValue: Infinity });

    // the raw wire payload must carry literal Infinity/-Infinity tokens, not null
    expect(capturedBody).toContain('"MinExpectedValue":-Infinity');
    expect(capturedBody).toContain('"MaxExpectedValue":Infinity');

    const capturedPayload = parseJsonWithInfinity(capturedBody);
    expect(capturedPayload).toEqual({
      Method: 'GET',
      Description: { MinExpectedValue: -Infinity, MaxExpectedValue: Infinity }
    });
  });

  // startMain with an undefined result
  it('should preserve NaN values in the description sent to the start queue', () => {
    let capturedBody = '';

    eventCallbacks['/queue/main_start_queue'] = (body: string) => {
      capturedBody = body;
      return { body: '{}' };
    };

    startMain({ result: NaN });

    // the raw wire payload must carry a literal NaN token, not null
    expect(capturedBody).toContain('"result":NaN');

    const capturedPayload = parseJsonWithInfinity(capturedBody);
    expect(capturedPayload).toEqual({
      Method: 'GET',
      Description: { result: NaN }
    });
  });

  //  downloadDump
  it('should return decoded data from download queue', async () => {
    eventCallbacks['/queue/main_download_dump_queue'] = () => {
      return {
        body: JSON.stringify({ status: 'ok', body: btoa('dump_data') })
      };
    };

    const result = await downloadDump('pkl');
    expect(result.object).toBe('dump_data');
  });

  // downloadDump with Infinity/NaN in the dumped data
  it('should parse a download response body containing Infinity/-Infinity/NaN instead of throwing', async () => {
    eventCallbacks['/queue/main_download_dump_queue'] = () => {
      return {
        body: '{"status": "ok", "body": "eyJvayI6IHRydWV9", "MinExpectedValue": -Infinity, "MaxExpectedValue": Infinity, "result": NaN}'
      };
    };

    const result = await downloadDump('pkl');
    expect(result.status).toBe('ok');
    expect(result.MinExpectedValue).toBe(-Infinity);
    expect(result.MaxExpectedValue).toBe(Infinity);
    expect(result.result).toBeNaN();
  });

  // calculatePlot
  it('should send the plot request as JSON to the plot queue', async () => {
    let calledHeaders: Record<string, string> | null = null;
    let calledBody = '';

    eventCallbacks['/queue/main_plot_queue'] = (body: string, headers: Record<string, string>) => {
      calledBody = body;
      calledHeaders = headers;
      return { body: '{}' };
    };

    await calculatePlot('contour', { objective: 'runtime' });

    expect(calledHeaders).toEqual({ body_type: 'json' });
    expect(parseJsonWithInfinity(calledBody)).toEqual({
      plot: 'contour',
      payload: { objective: 'runtime' }
    });
  });

  // calculatePlot with unbounded payload values
  it('should preserve Infinity/-Infinity/NaN values in the plot payload', async () => {
    let calledBody = '';

    eventCallbacks['/queue/main_plot_queue'] = (body: string) => {
      calledBody = body;
      return { body: '{}' };
    };

    await calculatePlot('contour', { MinExpectedValue: -Infinity, MaxExpectedValue: Infinity, result: NaN });

    expect(calledBody).toContain('"MinExpectedValue":-Infinity');
    expect(calledBody).toContain('"MaxExpectedValue":Infinity');
    expect(calledBody).toContain('"result":NaN');
  });

  // calculatePlot with Infinity/NaN in the response
  it('should parse a plot response body containing Infinity/NaN instead of throwing', async () => {
    eventCallbacks['/queue/main_plot_queue'] = () => {
      return {
        body: '{"contour": {"x": [1, 2], "MinExpectedValue": -Infinity, "MaxExpectedValue": Infinity, "result": NaN}}'
      };
    };

    const result = await calculatePlot('contour', { objective: 'runtime' });
    expect(result.contour.MinExpectedValue).toBe(-Infinity);
    expect(result.contour.MaxExpectedValue).toBe(Infinity);
    expect(result.contour.result).toBeNaN();
  });
});