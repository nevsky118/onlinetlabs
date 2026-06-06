// Ошибка серверного запроса сессии с HTTP-статусом, чтобы страница могла
// отличить 404 (сессии нет, чужая или осиротевшая) от 5xx (ошибка сервера) и
// не маскировать серверную ошибку под not-found.
export class SessionFetchError extends Error {
  constructor(
    readonly status: number,
    message?: string
  ) {
    super(message ?? `Не удалось загрузить сессию: ${status}`)
    this.name = "SessionFetchError"
  }
}
