"use client";

import Placeholder from "@tiptap/extension-placeholder";
import { EditorContent, useEditor, type JSONContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { useEffect } from "react";

import { Button } from "@memdot/ui";

import {
  memdotToTipTap,
  tipTapToMemdot,
  type MemdotDocument,
} from "@/src/lib/document/memdot";

export function DocumentEditor({
  documentId,
  initial,
  onSave,
  busy,
}: {
  documentId: string;
  initial: MemdotDocument;
  onSave: (doc: MemdotDocument) => void;
  busy?: boolean;
}) {
  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit,
      Placeholder.configure({ placeholder: "Write with provenance in mind…" }),
    ],
    content: memdotToTipTap(initial) as JSONContent,
    editorProps: {
      attributes: {
        class:
          "min-h-[280px] rounded-2xl border border-border bg-card px-4 py-3 text-sm leading-relaxed focus:outline-none",
      },
    },
  });

  useEffect(() => {
    if (!editor) {
      return;
    }
    editor.commands.setContent(memdotToTipTap(initial) as JSONContent);
  }, [documentId, editor]); // eslint-disable-line react-hooks/exhaustive-deps -- reload only on document change

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2" role="toolbar" aria-label="Formatting">
        <Button
          size="sm"
          variant="secondary"
          label="Bold"
          disabled={!editor}
          onClick={() => editor?.chain().focus().toggleBold().run()}
        />
        <Button
          size="sm"
          variant="secondary"
          label="Italic"
          disabled={!editor}
          onClick={() => editor?.chain().focus().toggleItalic().run()}
        />
        <Button
          size="sm"
          variant="secondary"
          label="H2"
          disabled={!editor}
          onClick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()}
        />
        <Button
          size="sm"
          variant="secondary"
          label="List"
          disabled={!editor}
          onClick={() => editor?.chain().focus().toggleBulletList().run()}
        />
        <Button
          size="sm"
          label={busy ? "Saving…" : "Save revision"}
          disabled={!editor || busy}
          onClick={() => {
            if (!editor) {
              return;
            }
            onSave(tipTapToMemdot(documentId, editor.getJSON()));
          }}
        />
      </div>
      <EditorContent editor={editor} />
    </div>
  );
}
