import { api } from "@/lib/api"

export interface BackendUser {
  id: string
  email: string
  name: string | null
  image: string | null
  role: string
}

interface TokenResponse {
  access_token: string
  token_type: string
}

export async function backendLogin(email: string, password: string) {
  const { data } = await api.post<BackendUser>("/auth/login", {
    email,
    password,
  })
  return data
}

export async function backendRegister(
  email: string,
  password: string,
  name?: string
) {
  const { data } = await api.post<BackendUser>("/auth/register", {
    email,
    password,
    name,
  })
  return data
}

export async function backendUpsertGithubUser(user: {
  email: string
  name: string
  image: string | null | undefined
  provider_account_id: string
}) {
  const { data } = await api.post<BackendUser>("/auth/github-callback", user)
  return data
}

export async function backendExchangeToken(userId: string, email: string) {
  const { data } = await api.post<TokenResponse>("/auth/exchange", {
    user_id: userId,
    email,
  })
  return data.access_token
}
