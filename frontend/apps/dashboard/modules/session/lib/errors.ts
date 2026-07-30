// Session fetch error carrying the HTTP status, so the page can tell 404 from 5xx and does not mask a server error as not-found.
export class SessionFetchError extends Error {
  constructor(
    readonly status: number,
    message?: string
  ) {
    super(message ?? `Session fetch failed with status ${status}`)
    this.name = "SessionFetchError"
  }
}
