import {
  createSearchParamsCache,
  parseAsInteger,
  parseAsString,
  parseAsStringEnum,
} from "nuqs/server"
import type { AdminUsersOrder, AdminUsersSort, UserRole } from "../types"

const roles: UserRole[] = ["student", "instructor", "admin"]
const sorts: AdminUsersSort[] = ["name", "email", "role"]
const orders: AdminUsersOrder[] = ["asc", "desc"]

export const parsers = {
  page: parseAsInteger.withDefault(1),
  pageSize: parseAsInteger.withDefault(20),
  sort: parseAsStringEnum<AdminUsersSort>(sorts).withDefault("name"),
  order: parseAsStringEnum<AdminUsersOrder>(orders).withDefault("asc"),
  search: parseAsString.withDefault(""),
  role: parseAsStringEnum<UserRole>(roles),
}

export const searchParamsCache = createSearchParamsCache(parsers)
