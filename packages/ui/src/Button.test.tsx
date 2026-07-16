import { describe, expect, it } from "vitest";

import { Button } from "./Button.js";

describe("Button", () => {
  it("exposes a callable component", () => {
    expect(typeof Button).toBe("function");
    const element = Button({ label: "Save" });
    expect(element?.props.children).toBe("Save");
  });
});
