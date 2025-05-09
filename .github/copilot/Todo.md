# Project Todo List

## Idea Dump
<!-- Place for dumping unorganized ideas -->

## Organized Tasks
<!-- Copilot will maintain this section -->

### High Priority
<!-- Critical bugs and important features -->

- #bug [Agent] Fix GitHub Actions tests that fail consistently
- #feature [Edit] Improve swipe detection on chore cards to require a minimum swipe distance before triggering actions, preventing accidental activation during scrolling
- #feature [Agent] Set up authentication using Dex with the k3s-config repo for proper user login/identity management
- #feature [Agent] The system of chores being "done today" is flawed - frontend checking if a chore can be done again today fails. Redesign this approach and move checks to server side
- #bug [Agent] Fix push notifications not firing - implementation appears incomplete
- #feature [Agent] Overhaul log functionality to be consistent across all users rather than using local storage - may require updating PRD documentation
- #feature [Agent] Move notifications settings to server side storage instead of local storage for cross-device consistency
- #documentation [Edit] Overhaul PRD.md and README.md to reflect current project state and goals
- #feature [Edit] Add a light theme to the app with a toggle switch in the settings menu
- #bug [Edit] Fix external links in about dialog being too long on small viewports causing dialog overflow
- #feature [Agent] Implement smart scheduling suggestions that analyze when chores are completed ahead of schedule and recommend interval adjustments
- #bug [Agent] Fix update mechanism after redeployment - currently requires multiple manual refreshes to properly show the update banner and load the new version

### Medium Priority
<!-- Enhancements and improvements -->
- #ui [Edit] Improve filter pills to make it clearer which ones are active
- #ui [Edit] Redesign chore card elements "due in" and "interval" to be more visually appealing and better utilize available space
- #feature [Agent] Add stats dashboard with calculated scores for each chore based on completion rate, on-time ratio, and adjustment frequency to provide insights into chore management patterns
- #maintenance [Agent] Perform "operation health" on current codebase - remove unused code, improve performance and readability, clean up dangling files, etc.
- #ci [Agent] Optimize GitHub workflows to trigger builds and deployments only when necessary (exclude changes to docs, todo lists, etc.)
- #ui [Edit] Overhaul animations throughout the app, especially focusing on return animations
- #documentation [Edit] Add API documentation
- #feature [Agent] Add comprehensive multi-language support
- #feature [Edit] Implement a dark/light theme toggle in the user settings
- #ui [Edit] Add visual indicators for private chores that are more intuitive than the current lock icon

### Low Priority
<!-- Nice-to-haves and maintenance tasks -->
- #feature [Agent] Re-implement AI assistant with proper functionality
- #feature [Agent] Create a mobile companion app or make the current UI more responsive for small screens

## In Progress
<!-- Tasks currently being worked on -->
- #bug [Agent] Add specific path for /reset.html in Traefik ingress to prevent redirection back to the app

## Completed
<!-- Finished tasks -->
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
