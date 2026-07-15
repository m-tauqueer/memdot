import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { Button } from "./Button.js";

describe("Button", () => {
  it("renders an accessible button element", () => {
    const html = renderToStaticMarkup(<Button label="Continue" />);
    expect(html).toContain("<button");
    expect(html).toContain('type="button"');
    expect(html).toContain("Continue");
  });
});
