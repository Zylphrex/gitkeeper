## MODIFIED Requirements

### Requirement: Submit Pull Request Review
The system SHALL allow users to submit pull request reviews with an approval, change request, or general comment status including any authored inline comments. No single-key or other permissionless action SHALL submit a review; every review submission SHALL require the user to explicitly trigger and confirm submission.

#### Scenario: Submit review approval
- **WHEN** the user triggers the approve review action and confirms submission
- **THEN** the system SHALL submit the review mutation to GitHub with an APPROVE decision and clear the reviewed PR or update its status

#### Scenario: Submit review with requested changes
- **WHEN** the user triggers the request changes action, enters required feedback, and confirms
- **THEN** the system SHALL submit the review mutation to GitHub with a REQUEST_CHANGES decision and include all pending comments

#### Scenario: Approve requires confirmation
- **WHEN** the user has not explicitly confirmed an approval submission
- **THEN** the system SHALL NOT submit an APPROVE review to GitHub
