import { createAccessControl } from "better-auth/plugins/access"

const statements = {
  course: ["view", "create", "update", "delete"],
  lab: ["view", "create", "update", "delete"],
  session: ["view", "join", "manage"],
  user: ["view", "manage"],
  model: ["select"],
} as const

export const ac = createAccessControl(statements)

export const roles = {
  student: ac.newRole({
    course: ["view"],
    lab: ["view"],
    session: ["view", "join"],
  }),
  instructor: ac.newRole({
    course: ["view", "create", "update"],
    lab: ["view", "create", "update"],
    session: ["view", "join", "manage"],
    model: ["select"],
  }),
  admin: ac.newRole({
    course: ["view", "create", "update", "delete"],
    lab: ["view", "create", "update", "delete"],
    session: ["view", "join", "manage"],
    user: ["view", "manage"],
    model: ["select"],
  }),
}

export type Role = keyof typeof roles
