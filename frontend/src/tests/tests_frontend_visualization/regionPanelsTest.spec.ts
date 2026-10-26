import { mount, shallowMount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import { createPinia } from 'pinia'
import { ref } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { VCheckbox, VSelect } from 'vuetify/components'
import RegionTitle from '../../entities/experiment/ui/RegionTitle.vue'
import { Rank, RankRegionPanel } from '../../widgets/charts/rank'
import { Slice, SliceRegionPanel } from '../../widgets/charts/slice'
import { Contour, ContourRegionPanel } from '../../widgets/charts/contour'
import { ParaCoord, ParaCoordRegionPanel } from '../../widgets/charts/para-coord'
import { HypImp, HypImpRegionPanel } from '../../widgets/charts/hyp-imp'

const vuetify = createVuetify({ components, directives })

const ALPHA = 'Context.SearchSpace.Algorithm.A.alpha'
const FLAG = 'Context.SearchSpace.Algorithm.A.flag'
const BETA = 'Context.SearchSpace.Algorithm.A.beta'
const GAMMA = 'Context.SearchSpace.Algorithm.B.gamma'

// region A holds a float, a single-category nominal and an integer parameter, region B a single integer
const experiment_description = ref({
    Context: {
        TaskConfiguration: {},
        SearchSpace: {
            Algorithm: {
                Type: 'NominalHyperparameter',
                Level: 0,
                Categories: ['Context.SearchSpace.Algorithm.A', 'Context.SearchSpace.Algorithm.B'],
                A: {
                    Type: 'Category',
                    alpha: { Type: 'FloatHyperparameter', Level: 1, Lower: 0, Upper: 1 },
                    flag: {
                        Type: 'NominalHyperparameter',
                        Level: 1,
                        Categories: [`${FLAG}.on`],
                        on: { Type: 'Category' }
                    },
                    beta: { Type: 'IntegerHyperparameter', Level: 1, Lower: 1, Upper: 10 }
                },
                B: {
                    Type: 'Category',
                    gamma: { Type: 'IntegerHyperparameter', Level: 1, Lower: 1, Upper: 5 }
                }
            },
            Structure: { Hierarchical: {} }
        }
    }
})

vi.mock('../../entities/main', () => ({
    useMainEventStore: vi.fn(() => ({
        experiment_description
    }))
}))

const mountPanel = (panel: any, props: Record<string, unknown>) => shallowMount(panel, {
    props,
    global: {
        plugins: [vuetify, createPinia()]
    }
})

describe('Region panels', () => {
    it('slice panel selects the first parameter of its region', () => {
        const wrapper = mountPanel(SliceRegionPanel, {
            regionParameters: [ALPHA, BETA],
            showTitle: false,
            sliceObjective: 'runtime'
        })

        expect(wrapper.findComponent(Slice).props('sliceParam')).toBe(ALPHA)
    })

    it('slice panel selects the first parameter of a new region', async () => {
        const wrapper = mountPanel(SliceRegionPanel, {
            regionParameters: [ALPHA, BETA],
            showTitle: false,
            sliceObjective: 'runtime'
        })

        await wrapper.setProps({ regionParameters: [GAMMA] })

        expect(wrapper.findComponent(Slice).props('sliceParam')).toBe(GAMMA)
    })

    it('shows the region title only when asked to', async () => {
        const wrapper = mountPanel(SliceRegionPanel, {
            regionParameters: [ALPHA, BETA],
            showTitle: true,
            sliceObjective: 'runtime'
        })

        expect(wrapper.findComponent(RegionTitle).props('regionParameters')).toEqual([ALPHA, BETA])

        await wrapper.setProps({ showTitle: false })

        expect(wrapper.findComponent(RegionTitle).exists()).toBe(false)
    })

    it('contour panel selects the first two parameters of its region that can span an axis', () => {
        const wrapper = mountPanel(ContourRegionPanel, {
            regionParameters: [ALPHA, FLAG, BETA],
            showTitle: false,
            contourObjective: 'runtime'
        })

        const contour = wrapper.findComponent(Contour)
        expect(contour.props('contourParam1')).toBe(ALPHA)
        expect(contour.props('contourParam2')).toBe(BETA)
    })

    it('contour panel explains instead of plotting a region with fewer than two parameters', () => {
        const wrapper = mountPanel(ContourRegionPanel, {
            regionParameters: [GAMMA],
            showTitle: false,
            contourObjective: 'runtime'
        })

        expect(wrapper.findComponent(Contour).exists()).toBe(false)
        expect(wrapper.text()).toContain('Not enough parameters in this region for a contour plot.')
    })

    it('parallel coordinates panel selects all parameters of its region', () => {
        const wrapper = mountPanel(ParaCoordRegionPanel, {
            regionParameters: [ALPHA, FLAG, BETA],
            showTitle: false,
            paraCoordObjective: 'runtime'
        })

        expect(wrapper.findComponent(ParaCoord).props('paraCoordParams')).toEqual([ALPHA, FLAG, BETA])
    })

    it('hyperparameter importances panel selects all parameters of its region', () => {
        const wrapper = mountPanel(HypImpRegionPanel, {
            regionParameters: [ALPHA, FLAG, BETA],
            showTitle: false,
            hypImpObjective: 'runtime'
        })

        expect(wrapper.findComponent(HypImp).props('hypImpParams')).toEqual([ALPHA, FLAG, BETA])
    })

    it('rank panel selects the first two parameters of its region that can span an axis', () => {
        const wrapper = mountPanel(RankRegionPanel, {
            regionParameters: [ALPHA, FLAG, BETA],
            showTitle: false,
            rankObjective: 'runtime'
        })

        const rank = wrapper.findComponent(Rank)
        expect(rank.props('rankParam1')).toBe(ALPHA)
        expect(rank.props('rankParam2')).toBe(BETA)
    })

    it('rank panel never offers the parameter chosen for one axis on the other axis', () => {
        const wrapper = mountPanel(RankRegionPanel, {
            regionParameters: [ALPHA, FLAG, BETA],
            showTitle: false,
            rankObjective: 'runtime'
        })

        const [axis1, axis2] = wrapper.findAllComponents(VSelect)
        expect(axis1.props('items')).toEqual([ALPHA])
        expect(axis2.props('items')).toEqual([BETA])
    })

    it('rank panel explains instead of plotting a region with fewer than two parameters', () => {
        const wrapper = mountPanel(RankRegionPanel, {
            regionParameters: [GAMMA],
            showTitle: false,
            rankObjective: 'runtime'
        })

        expect(wrapper.findComponent(Rank).exists()).toBe(false)
        expect(wrapper.text()).toContain('Not enough parameters in this region for a rank plot.')
    })

    it('hyperparameter importances panel keeps the last selected parameter checked', async () => {
        // full mount, so that the checkboxes inside the list items are rendered; only the chart is stubbed
        const wrapper = mount(HypImpRegionPanel, {
            props: {
                regionParameters: [ALPHA, BETA],
                showTitle: false,
                hypImpObjective: 'runtime'
            },
            global: {
                plugins: [vuetify, createPinia()],
                stubs: { HypImp: true }
            }
        })

        const [alphaBox, betaBox] = wrapper.findAllComponents(VCheckbox)
        expect(alphaBox.props('disabled')).toBe(false)
        expect(betaBox.props('disabled')).toBe(false)

        await alphaBox.vm.$emit('update:modelValue', [ALPHA])

        expect(wrapper.findAllComponents(VCheckbox)[0].props('disabled')).toBe(true)
        expect(wrapper.findAllComponents(VCheckbox)[1].props('disabled')).toBe(false)
    })
})
