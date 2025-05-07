# Project Todo List

## Organized Tasks
<!-- Copilot will maintain this section -->

### High Priority
<!-- Critical bugs and important features -->
- #bug Fix persistent issue where app breaks after redeployment (staging/prod) with non-descriptive error - currently requires clearing browser local storage as workaround
- #bug Fix GitHub Actions tests that fail consistently
- #feature Set up authentication using Dex with the k3s-config repo for proper user login/identity management
- #feature The system of chores being "done today" is flawed - frontend checking if a chore can be done again today fails. Redesign this approach and move checks to server side
- #feature Overhaul log functionality to be consistent across all users rather than using local storage - may require updating PRD documentation
- #feature Move notifications settings to server side storage instead of local storage for cross-device consistency

### Medium Priority
<!-- Enhancements and improvements -->
- #ui Add a menu to the header to contain about, notifications and import/export buttons
- #ui Update notification settings modal dialog - arrange cancel and save buttons vertically instead of horizontally for consistency
- #ui Improve filter pills to make it clearer which ones are active
- #ui Remove the "archived" filter pill and hide it in the upcoming header menu
- #ui Redesign chore card elements "due in" and "interval" to be more visually appealing and better utilize available space
- #maintenance Perform "operation health" on current codebase - remove unused code, improve performance and readability, clean up dangling files, etc.

### Low Priority
<!-- Nice-to-haves and maintenance tasks -->
- #ui Change label on notification settings modal from "Save Changes" to just "Save"
- #ui Make "Done" button in about dialog gray instead of green to match the import/export dialog
- #ui Move "cancel" button before "save" button in edit chore mode for UI consistency

## In Progress
<!-- Tasks currently being worked on -->

## Completed
<!-- Finished tasks -->
- #bug Fix push notification times not being stored - only the first notification time persists after refresh
- #feature Add import and export API endpoints for consistency with the frontend
- #bug Fix import functionality not actually importing data - appears to work in UI but after page refresh, everything reverts to pre-import state
- #bug Fix import/export functionality errors - resolved 'coroutine' error and database null value constraint violation
