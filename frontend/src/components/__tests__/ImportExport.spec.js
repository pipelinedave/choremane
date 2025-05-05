import { mount } from '@vue/test-utils'
import ImportExport from '@/components/ImportExport.vue'
import { setActivePinia, createPinia } from 'pinia'
import { useChoreStore } from '@/store/choreStore'
import { useLogStore } from '@/store/logStore'

describe('ImportExport.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    useChoreStore().chores = [
      { id: 1, name: 'Test Chore', due_date: '2025-04-28', interval_days: 3, done: false, archived: false }
    ]
    useLogStore().logEntries = [
      { id: 1, message: 'Test log', timestamp: '12:00:00' }
    ]
  })

  it('exports data as JSON', async () => {
    const wrapper = mount(ImportExport)
    // Mock URL.createObjectURL and anchor click
    global.URL.createObjectURL = jest.fn(() => 'blob:url')
    const clickSpy = jest.spyOn(document.body, 'appendChild').mockImplementation(() => {})
    wrapper.find('button').trigger('click')
    expect(global.URL.createObjectURL).toHaveBeenCalled()
    clickSpy.mockRestore()
  })

  it('shows error on invalid import', async () => {
    const wrapper = mount(ImportExport)
    const file = new Blob(['{"bad":true}'], { type: 'application/json' })
    Object.defineProperty(wrapper.vm.$refs.importInput, 'files', { value: [file] })
    const event = { target: { files: [file] } }
    wrapper.vm.importData(event)
    await wrapper.vm.$nextTick()
    expect(wrapper.html()).toContain('Import failed')
  })
})
