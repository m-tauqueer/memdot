import { createWebHealthPayload } from "@/src/lib/health";

export function GET(): Response {
  return Response.json(createWebHealthPayload());
}
