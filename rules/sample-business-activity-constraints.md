### Rule: Business Activity must belong to a single Business Process and a single Business User Group

A Business Activity entry must reference exactly one Business Process (via `businessProcessId`) and exactly one Business User Group (via `businessUserGroupId`). Every Business Activity in this PR must satisfy this constraint.

**Severity:** error
