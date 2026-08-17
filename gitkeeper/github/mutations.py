"""GitHub GraphQL mutation definitions."""

ADD_PULL_REQUEST_REVIEW_MUTATION = """
mutation AddPullRequestReview($input: AddPullRequestReviewInput!) {
  addPullRequestReview(input: $input) {
    pullRequestReview {
      id
      state
      url
    }
  }
}
"""
