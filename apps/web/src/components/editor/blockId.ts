import Heading from "@tiptap/extension-heading";
import Paragraph from "@tiptap/extension-paragraph";

/** Preserve MemdotDocument blockId attrs through TipTap round-trips. */
const blockIdAttribute = {
  blockId: {
    default: null as string | null,
    parseHTML: (element: HTMLElement) => element.getAttribute("data-block-id"),
    renderHTML: (attributes: { blockId?: string | null }) => {
      if (!attributes.blockId) {
        return {};
      }
      return { "data-block-id": attributes.blockId };
    },
  },
};

export const ParagraphWithBlockId = Paragraph.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      ...blockIdAttribute,
    };
  },
});

export const HeadingWithBlockId = Heading.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      ...blockIdAttribute,
    };
  },
});
