// Ошибка fetch сессии с HTTP-статусом: чтобы страница отличала 404 от 5xx и не маскировала серверную ошибку под not-found.
export class SessionFetchError extends Error {
  constructor(
    readonly status: number,
    message?: string
  ) {
    super(message ?? `Не удалось загрузить сессию: ${status}`)
    this.name = "SessionFetchError"
  }
}
