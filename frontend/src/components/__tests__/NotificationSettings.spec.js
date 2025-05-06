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
    await wrapper.find('button[aria-label="Save notification settings"]').trigger('click')
    expect(JSON.parse(localStorage.getItem('notificationSettings')).enabled).toBe(true)
    await checkbox.setValue(false)
    await wrapper.find('button[aria-label="Save notification settings"]').trigger('click')
    expect(JSON.parse(localStorage.getItem('notificationSettings')).enabled).toBe(false)
  })

  it('adds and removes notification times', async () => {
    const wrapper = mount(NotificationSettings)
    await wrapper.find('button[aria-label="Add notification time"]').trigger('click')
    expect(wrapper.vm.times.length).toBeGreaterThan(1)
    await wrapper.find('button[aria-label="Save notification settings"]').trigger('click')
    
    // Reload to verify persistence
    const reloadedWrapper = mount(NotificationSettings)
    expect(reloadedWrapper.vm.times.length).toBeGreaterThan(1)
    
    await reloadedWrapper.find('button[aria-label="Remove notification time"]').trigger('click')
    await reloadedWrapper.find('button[aria-label="Save notification settings"]').trigger('click')
    expect(reloadedWrapper.vm.times.length).toBe(1)
  })

  it('cancels changes when cancel button is clicked', async () => {
    const wrapper = mount(NotificationSettings)
    await wrapper.find('button[aria-label="Add notification time"]').trigger('click')
    const origLength = wrapper.vm.times.length
    await wrapper.find('button[aria-label="Add notification time"]').trigger('click')
    expect(wrapper.vm.times.length).toBeGreaterThan(origLength)
    
    // Cancel changes
    await wrapper.find('button[aria-label="Cancel changes"]').trigger('click')
    
    // Reopen settings - should have original values
    const reloadedWrapper = mount(NotificationSettings)
    expect(reloadedWrapper.vm.times.length).toBe(1) // Default value
  })

  it('requests permission when enabling notifications', async () => {
    window.Notification = { requestPermission: jest.fn(() => Promise.resolve('granted')) }
    const wrapper = mount(NotificationSettings)
    const checkbox = wrapper.find('input[type="checkbox"]')
    await checkbox.setValue(true)
    expect(window.Notification.requestPermission).toHaveBeenCalled()
  })
})
