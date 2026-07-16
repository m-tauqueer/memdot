import { describe, expect, it } from "vitest";

import { emptyMemdotDocument, plainTextFromMemdot, tipTapToMemdot } from "./memdot.js";

describe("memdot document helpers", () => {
  it("builds an empty envelope", () => {
    const doc = emptyMemdotDocument("11111111-1111-7111-8111-111111111111");
    expect(doc.schema).toBe("memdot-document");
    expect(doc.root.content[0]?.attrs.blockId).toBeTruthy();
  });

  it("maps tip tap paragraphs with block ids", () => {
    const doc = tipTapToMemdot("11111111-1111-7111-8111-111111111111", {
      type: "doc",
      content: [
        {
          type: "paragraph",
          content: [{ type: "text", text: "hello" }],
        },
      ],
    });
    expect(plainTextFromMemdot(doc)).toContain("hello");
    expect(doc.root.content[0]?.attrs.blockId).toMatch(/-/);
  });
});
