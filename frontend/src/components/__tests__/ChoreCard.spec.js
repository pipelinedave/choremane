import { mount } from '@vue/test-utils'
import ChoreCard from '@/components/ChoreCard.vue'

describe('ChoreCard.vue accessibility', () => {
  it('has ARIA attributes and is keyboard accessible', () => {
    const chore = {
      id: 1,
      name: 'Accessible Chore',
      due_date: '2025-04-28',
      interval_days: 3,
      done: false,
      archived: false,
      is_private: true
    }
    const wrapper = mount(ChoreCard, { props: { chore } })
    const card = wrapper.find('.chore-card')
    expect(card.attributes('role')).toBe('listitem')
    expect(card.attributes('tabindex')).toBe('0')
    expect(card.attributes('aria-label')).toContain('Private chore')
    // Lock icon should have aria-label and role
    expect(wrapper.html()).toContain('aria-label="Private chore"')
    expect(wrapper.html()).toContain('role="img"')
  })
})
