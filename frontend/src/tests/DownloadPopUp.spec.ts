import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import DownloadComponent from '../features/download-popup/ui/DownloadPopup.vue'
import { downloadPopUp } from '../features/download-popup/api/download.api.ts'

vi.mock('../features/download-popup/api/download.api.ts', () => ({
    downloadPopUp: vi.fn(),
}))

const vuetify = createVuetify({ components, directives })

describe('DownloadPopup.vue', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('calls API with pkl and emits close event on click', async () => {
        const wrapper = mount(DownloadComponent, {
            global: { plugins: [vuetify] }
        })
        const buttons = wrapper.findAll('button')
        await buttons[0].trigger('click')
        expect(downloadPopUp).toHaveBeenCalledWith('pkl')
        expect(wrapper.emitted()).toHaveProperty('close')
    })

    it('calls API with csv and emits close event on click', async () => {
        const wrapper = mount(DownloadComponent, {
            global: { plugins: [vuetify] }
        })
        const buttons = wrapper.findAll('button')
        await buttons[1].trigger('click')
        expect(downloadPopUp).toHaveBeenCalledWith('csv')
        expect(wrapper.emitted()).toHaveProperty('close')
    })

    it('renders correct button labels', () => {
        const wrapper = mount(DownloadComponent, {
            global: { plugins: [vuetify] }
        })
        expect(wrapper.text()).toContain('Experiment instance')
        expect(wrapper.text()).toContain('Basic metrics')
    })
})