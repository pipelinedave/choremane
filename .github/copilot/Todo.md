# Project Todo List

## Organized Tasks
<!-- Copilot will maintain this section -->

### High Priority
<!-- Critical bugs and important features -->

- #bug Fix GitHub Actions tests that fail consistently
- #feature Set up authentication using Dex with the k3s-config repo for proper user login/identity management
- #feature The system of chores being "done today" is flawed - frontend checking if a chore can be done again today fails. Redesign this approach and move checks to server side
- #bug Fix push notifications not firing - implementation appears incomplete
- #feature Overhaul log functionality to be consistent across all users rather than using local storage - may require updating PRD documentation
- #feature Move notifications settings to server side storage instead of local storage for cross-device consistency
- #documentation Overhaul PRD.md and README.md to reflect current project state and goals
- #feature Add a light theme to the app with a toggle switch in the settings menu
- #bug Fix external links in about dialog being too long on small viewports causing dialog overflow
- #ui Add buttons on either end of each chore card for non-mobile devices (done on left, edit on right) and hide them on mobile devices

### Medium Priority
<!-- Enhancements and improvements -->
- #ui Improve filter pills to make it clearer which ones are active
- #ui Remove the "archived" filter pill and hide a functionality to manage archived items in the upcoming header menu
- #ui Redesign chore card elements "due in" and "interval" to be more visually appealing and better utilize available space
- #maintenance Perform "operation health" on current codebase - remove unused code, improve performance and readability, clean up dangling files, etc.
- #ci Optimize GitHub workflows to trigger builds and deployments only when necessary (exclude changes to docs, todo lists, etc.)

### Low Priority
<!-- Nice-to-haves and maintenance tasks -->

## In Progress
<!-- Tasks currently being worked on -->
- #bug Add specific path for /reset.html in Traefik ingress to prevent redirection back to the app

## Completed
<!-- Finished tasks -->
- #ui Make chore card actions "marking done" and "enter edit mode" use material swipe-to-reveal action pattern
- #feature Add new filter pills for "due tomorrow" and "due this week" using similar logic to the "due today" pill
- #ui Add a menu to the header to contain about, notifications and import/export buttons
- #bug Fix settings->troubleshoot link to /reset.html - error "Cannot read properties of undefined (reading 'BASE_URL')" in Header.vue indicates missing environment configuration in staging environment
- #ui Move "cancel" button before "save" button in edit chore mode for UI consistency
- #ui Make "Done" button in about dialog gray instead of green to match the import/export dialog
- #ui Change label on notification settings modal from "Save Changes" to just "Save"
- #bug the page refreshes once per second in the staging environment but not in the local development setup - investigate and fix
- #bug Fix persistent issue where app breaks after redeployment (staging/prod) with non-descriptive error - currently requires clearing browser local storage as workaround
