import {
  createSearchParamsCache,
  parseAsInteger,
  parseAsString,
  parseAsStringEnum,
} from "nuqs/server"
import type { AdminDataOrder } from "../types"

const orders: AdminDataOrder[] = ["asc", "desc"]

export const parsers = {
  page: parseAsInteger.withDefault(1),
  pageSize: parseAsInteger.withDefault(50),
  sort: parseAsString.withDefault(""),
  order: parseAsStringEnum<AdminDataOrder>(orders).withDefault("desc"),
  search: parseAsString.withDefault(""),
}

export const searchParamsCache = createSearchParamsCache(parsers)
