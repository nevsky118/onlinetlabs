import axios from "axios"
import { headers } from "next/headers"
import { backendExchangeToken } from "./api"
import { auth } from "@/auth"

/**
 * Транзиентный сбой обмена токена (429 / 5xx / сеть). Отличаем от «нет сессии»:
 * null ведёт пользователя на sign-in, эта ошибка — на 503 / error boundary.
 * Без этого различия любой кратковременный сбой backend разлогинивал бы юзера.
 */
export class BackendUnavailableError extends Error {
  constructor(public readonly reason?: unknown) {
    super("backend token exchange failed")
    this.name = "BackendUnavailableError"
  }
}

interface CachedToken {
  token: string
  expiresAtMs: number
}

// Кэш backend-JWT по better-auth userId. Токен живёт 5 мин, поэтому переобмен
// идёт раз в ~4 мин на юзера, а не «перед каждым запросом». Модульный кэш живёт
// в пределах инстанса Next; при горизонтальном масштабировании заменить хранилище
// на Redis — интерфейс get/set локализован здесь.
const tokenCache = new Map<string, CachedToken>()

// Single-flight: схлопывает параллельные обмены (strict-mode дубли, бёрст
// ws-token + backend-token + chat в один тик) в один сетевой вызов на юзера.
const inflight = new Map<string, Promise<string | null>>()

// Обновляем за 60с до истечения, чтобы не отдать токен, протухающий в полёте.
const REFRESH_SKEW_MS = 60_000

function decodeExpiryMs(jwt: string): number {
  const payload = jwt.split(".")[1]
  const decoded = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"))
  return decoded.exp * 1000
}

export async function getBackendToken(): Promise<string | null> {
  const session = await auth.api.getSession({ headers: await headers() })
  // Нет better-auth сессии → null. Вызывающий ведёт на sign-in.
  if (!session?.user?.id) return null

  const userId = session.user.id

  const cached = tokenCache.get(userId)
  if (cached && cached.expiresAtMs - REFRESH_SKEW_MS > Date.now()) {
    return cached.token
  }

  const existing = inflight.get(userId)
  if (existing) return existing

  const exchange = (async (): Promise<string | null> => {
    try {
      const token = await backendExchangeToken(
        session.user.id,
        session.user.email
      )
      tokenCache.set(userId, { token, expiresAtMs: decodeExpiryMs(token) })
      return token
    } catch (error) {
      // 401 = осиротевший cookie / нет юзера на backend → null → sign-in.
      // Остальное (429 / 5xx / сеть) = транзиент → не разлогиниваем.
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        return null
      }
      throw new BackendUnavailableError(error)
    } finally {
      inflight.delete(userId)
    }
  })()

  inflight.set(userId, exchange)
  return exchange
}
