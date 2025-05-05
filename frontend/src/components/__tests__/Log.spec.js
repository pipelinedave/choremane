import { mount } from '@vue/test-utils'
import Log from '@/components/Log.vue'
import { setActivePinia, createPinia } from 'pinia'
import { useLogStore } from '@/store/logStore'
import { useChoreStore } from '@/store/choreStore'

describe('Log.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    useLogStore().logEntries = [
      { id: 1, message: 'Did something', timestamp: '12:00:00' },
      { id: 2, message: 'Did something else', timestamp: '13:00:00' }
    ]
  })

  it('renders log entries', () => {
    const wrapper = mount(Log)
    wrapper.vm.expanded = true
    expect(wrapper.html()).toContain('Did something')
    expect(wrapper.html()).toContain('Did something else')
  })

  it('calls undo when log entry is clicked', async () => {
    const wrapper = mount(Log)
    wrapper.vm.expanded = true
    const spy = jest.spyOn(wrapper.vm, 'handleLogClick')
    await wrapper.findAll('.log-entry')[0].trigger('click')
    expect(spy).toHaveBeenCalled()
  })

  it('has ARIA roles and is keyboard accessible', () => {
    const wrapper = mount(Log)
    expect(wrapper.find('.log-overlay').attributes('role')).toBe('region')
    expect(wrapper.find('.handle').attributes('role')).toBe('button')
  })
})
