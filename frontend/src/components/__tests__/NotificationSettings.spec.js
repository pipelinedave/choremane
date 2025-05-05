import { mount } from '@vue/test-utils'
import NotificationSettings from '@/components/NotificationSettings.vue'

describe('NotificationSettings.vue', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('enables and disables notifications', async () => {
    const wrapper = mount(NotificationSettings)
    const checkbox = wrapper.find('input[type="checkbox"]')
    await checkbox.setValue(true)
    expect(JSON.parse(localStorage.getItem('notificationSettings')).enabled).toBe(true)
    await checkbox.setValue(false)
    expect(JSON.parse(localStorage.getItem('notificationSettings')).enabled).toBe(false)
  })

  it('adds and removes notification times', async () => {
    const wrapper = mount(NotificationSettings)
    await wrapper.find('button[aria-label="Add notification time"]').trigger('click')
    expect(wrapper.vm.times.length).toBeGreaterThan(1)
    await wrapper.find('button[aria-label="Remove notification time"]').trigger('click')
    expect(wrapper.vm.times.length).toBe(1)
  })

  it('requests permission when enabling notifications', async () => {
    window.Notification = { requestPermission: jest.fn(() => Promise.resolve('granted')) }
    const wrapper = mount(NotificationSettings)
    const checkbox = wrapper.find('input[type="checkbox"]')
    await checkbox.setValue(true)
    expect(window.Notification.requestPermission).toHaveBeenCalled()
  })
})
