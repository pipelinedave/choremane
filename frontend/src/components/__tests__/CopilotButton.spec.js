import { mount } from '@vue/test-utils'
import CopilotButton from '@/components/CopilotButton.vue'

describe('CopilotButton.vue', () => {
  it('renders floating button and opens modal', async () => {
    const wrapper = mount(CopilotButton)
    expect(wrapper.find('.copilot-fab').exists()).toBe(true)
    await wrapper.find('.copilot-fab').trigger('click')
    expect(wrapper.find('.copilot-modal').exists()).toBe(true)
  })

  it('submits input and displays response', async () => {
    const wrapper = mount(CopilotButton)
    await wrapper.find('.copilot-fab').trigger('click')
    const input = wrapper.find('input[type="text"]')
    await input.setValue('What chores are due?')
    await wrapper.find('form').trigger('submit.prevent')
    expect(wrapper.html()).toContain('You said:')
  })
})
