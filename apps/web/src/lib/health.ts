export type WebHealthPayload = {
  status: "ok";
  service: "web";
};

export function createWebHealthPayload(): WebHealthPayload {
  return {
    status: "ok",
    service: "web",
  };
}
