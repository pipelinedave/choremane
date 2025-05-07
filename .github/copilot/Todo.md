# Project Todo List

## Inbox
- its kind of hard to tell if and which filter pills are active
- i dont think a filter pill for "archived" makes much sense. better to hide it in the upcoming menu we will add to the header
- lets add a menu to the header and hide the existing about, notifications and import/export buttons in there

- the entire system of chores being "done today" is flawed. currently the frontend checks if a chore can be done again today and it fails on many levels. brainstorm an entire new way to do it.
- lets make sure all the features are consistent to all users across all devices. log needs to be global as we already discussed, but the chores "done today" where they are unable to be marked as done again for the day should just be handled on server side probably or something. 
- lets visually redesign the chore card elements "due in" and "interval" to be more visually appealing and utilizing the available space in each card better.
- the notifications settings should also be stored server side for each user. currently they are stored in local storage and are not consistent across devices.

## Organized Tasks
<!-- Copilot will maintain this section -->

### High Priority
<!-- Critical bugs and important features -->
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
- #feature Add import and export API endpoints for consistency with the frontend
- #bug Fix import functionality not actually importing data - appears to work in UI but after page refresh, everything reverts to pre-import state
