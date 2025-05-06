# Project Todo List

## Inbox
<!-- Add new ideas and todos anywhere in this section -->

## Organized Tasks
<!-- Copilot will maintain this section -->

### High Priority
<!-- Critical bugs and important features -->
- #bug Fix import functionality not actually importing data - appears to work in UI but after page refresh, everything reverts to pre-import state
- #bug Fix persistent issue where app breaks after redeployment (staging/prod) with non-descriptive error - currently requires clearing browser local storage as workaround
- #bug Fix GitHub Actions tests that fail consistently
- #feature Set up authentication using Dex with the k3s-config repo for proper user login/identity management

### Medium Priority
<!-- Enhancements and improvements -->
- #feature Overhaul log functionality to be consistent across all users rather than using local storage - may require updating PRD documentation
- #ui Update notification settings modal dialog - arrange cancel and save buttons vertically instead of horizontally for consistency

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
