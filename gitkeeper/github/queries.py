"""GitHub GraphQL query definitions."""

REVIEW_REQUESTS_QUERY = """
query GetReviewRequests($query: String!) {
  search(query: $query, type: ISSUE, first: 50) {
    issueCount
    nodes {
      ... on PullRequest {
        id
        number
        title
        body
        url
        isDraft
        state
        baseRefName
        headRefName
        createdAt
        updatedAt
        additions
        deletions
        changedFiles
        repository {
          nameWithOwner
          name
          owner {
            login
          }
        }
        author {
          login
        }
        reviewRequests(first: 20) {
          nodes {
            requestedReviewer {
              ... on User {
                login
              }
              ... on Team {
                name
                slug
              }
            }
          }
        }
        reviews(first: 30) {
          nodes {
            author {
              login
            }
            state
            submittedAt
          }
        }
        commits(last: 1) {
          nodes {
            commit {
              statusCheckRollup {
                state
              }
            }
          }
        }
        files(first: 100) {
          nodes {
            path
            additions
            deletions
            changeType
          }
        }
      }
    }
  }
}
"""

VIEWER_QUERY = """
query GetViewer {
  viewer {
    login
  }
}
"""
