# Project Todo List

## Idea Dump
<!-- Place for dumping unorganized ideas -->
<!-- No pending items here; move processed ideas into Organized Tasks -->
- blocked (marked as done) chores should still be editable. currently also the edit mode gets blocked...
- we need to make it so the backend and frontend tests are run within github actions before the deployment to staging
- we need to make sure backend tests and frontend tests have as much coverage as possible
- remove the superfluous "Due" in the pill titles so its just "Today" and not "Due Today"


## Inbox
<!-- Place for new ideas before processing -->

## Organized Tasks
<!-- Copilot will maintain this section -->

### High Priority
<!-- Critical bugs and important features -->


- #bug [UI] Fix private toggle in edit mode so setting a chore to private or public actually updates the chore state.
- #bug [Agent] Fix push notifications not firing - implementation appears incomplete
- #feature [Agent] Overhaul log functionality to be consistent across all users rather than using local storage - may require updating PRD documentation
- #feature [Agent] Move notifications settings to server side storage instead of local storage for cross-device consistency
- #documentation [Edit] Overhaul PRD.md and README.md to reflect current project state and goals
- #bug [Edit] Fix external links in about dialog being too long on small viewports causing dialog overflow
- #feature [Agent] Implement smart scheduling suggestions that analyze when chores are completed ahead of schedule and recommend interval adjustments
- #bug [Agent] Fix update mechanism after redeployment - currently requires multiple manual refreshes to properly show the update banner and load the new version
- #bug [UI] Fix modal dialogs that still allow scrolling of the background page


### Medium Priority
<!-- Enhancements and improvements -->
- #ui [Edit] Redesign chore card elements "due in" and "interval" to be more visually appealing and better utilize available space
- #feature [Agent] Add stats dashboard with calculated scores for each chore based on completion rate, on-time ratio, and adjustment frequency to provide insights into chore management patterns
- #maintenance [Agent] Perform "operation health" on current codebase - remove unused code, improve performance and readability, clean up dangling files, etc.
- #ci [Agent] Optimize GitHub workflows to trigger builds and deployments only when necessary (exclude changes to docs, todo lists, etc.)
- #documentation [Edit] Add API documentation
- #feature [Agent] Add comprehensive multi-language support
- #ui [Edit] Add visual indicators for private chores that are more intuitive than the current lock icon

### Low Priority
<!-- Nice-to-haves and maintenance tasks -->
- #feature [Agent] Re-implement AI assistant with proper functionality

## In Progress
<!-- Tasks currently being worked on -->
- #ci [Agent] Temporarily disabled GitHub Actions tests that fail consistently - need to be fixed later

## Completed
<!-- Finished tasks -->
- #feature [Edit] Improve swipe detection on chore cards to require a minimum swipe distance before triggering actions, preventing accidental activation during scrolling
- #ui [Edit] Create custom illustrations for empty states (no chores, no archived chores, etc.)
- #ui Make chore card actions "marking done" and "enter edit mode" use material swipe-to-reveal action pattern
- #feature Add new filter pills for "due tomorrow" and "due this week" using similar logic to the "due today" pill
- #ui Add a menu to the header to contain about, notifications and import/export buttons
- #bug Fix settings->troubleshoot link to /reset.html - error "Cannot read properties of undefined (reading 'BASE_URL')" in Header.vue indicates missing environment configuration in staging environment
- #ui Move "cancel" button before "save" button in edit chore mode for UI consistency
- #ui Make "Done" button in about dialog gray instead of green to match the import/export dialog
- #ui Change label on notification settings modal from "Save Changes" to just "Save"
- #bug the page refreshes once per second in the staging environment but not in the local development setup - investigate and fix
- #bug Fix persistent issue where app breaks after redeployment (staging/prod) with non-descriptive error - currently requires clearing browser local storage as workaround
- #ui Remove the "archived" filter pill and add functionality to manage archived items in the header menu
- #feature [Edit] Add pagination to the chores list view and archived chores view with infinite scroll and a scroll-to-top button
- #feature [Agent] Set up authentication using Dex with the k3s-config repo for proper user login/identity management
- there is no "done" or "close" button in the "archived chores" modal dialog. it can only be closed by clicking in the background. this is inconsistent with the other dialogs and should be brought in line.
- #bug [UI] its impossible to scroll on chorecards in a normal state using touch. you have to hit the margin left and right of the chorecards to scroll the page, or hit a chorecard thats in disabled state for the page to scroll. this is very unintuitive.
- #bug [UI] Fix inconsistent scrolling behavior in chore list on mobile - list becomes unscrollable upon initial load and swipe actions become unreliable after applying filters or marking chores as done
- #bug [Agent] Preserve “done today” status after refresh by keeping the server/client state consistent when the last completion date is today.
- #feature [Agent] The system of chores being "done today" is flawed - frontend checking if a chore can be done again today fails. Redesign this approach and move checks to server side
- #bug [UI] the filter pills amounts displayed is false sometimes. for example it might show "8 Due this week" while there are only 4 chores in that filter category
- #ui [Edit] Overhaul animations throughout the app, especially focusing on return animations
