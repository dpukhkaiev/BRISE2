import { describe, it, expect, vi, beforeEach } from 'vitest'
import { downloadPopUp } from '../features/download-popup/api/download.api' 
import { downloadDump } from '../entities/main/api/main.client.store'
import { saveAs } from 'file-saver'
import type { Mock } from 'vitest'

vi.mock('../entities/main/api/main.client.store', () => ({
  downloadDump: vi.fn(),
}))

vi.mock('file-saver', () => ({
  saveAs: vi.fn(),
}))

describe('downloadPopUp', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should call saveAs with a correctly converted Blob when status is "ok"', async () => {
    const fakeByteString = 'abc' // charCodes: 97, 98, 99
    const fakeResponse = {
      status: 'ok',
      object: fakeByteString,
      file_name: 'test_dump.pkl',
    }

   
    vi.mocked(downloadDump).mockResolvedValue(fakeResponse)

   
    await downloadPopUp('pkl')

    expect(downloadDump).toHaveBeenCalledWith('pkl')

    expect(saveAs).toHaveBeenCalledOnce()

    const [passedBlob, passedFileName] = vi.mocked(saveAs).mock.calls[0]

    expect(passedFileName).toBe('test_dump.pkl')

    const blobInstance = passedBlob as Blob
    expect(passedBlob).toBeInstanceOf(Blob)
    
    const text = await blobInstance.text()
    expect(text).toBe('abc')
  })

  it('should NOT call saveAs when status is not "ok"', async () => {
   
    const errorResponse = {
      status: 'error',
      message: 'Something went wrong',
    }

    vi.mocked(downloadDump).mockResolvedValue(errorResponse)

    await downloadPopUp('csv')

    expect(downloadDump).toHaveBeenCalledWith('csv')
    
    expect(saveAs).not.toHaveBeenCalled()
  })
})