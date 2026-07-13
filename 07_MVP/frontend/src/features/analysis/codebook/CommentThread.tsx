import { FormEvent, useState } from "react";
import Button from "@/shared/components/Button";
import { analysisApi } from "../api";
import { CategoryComment } from "../types";

/** Hilo de comentarios de una categoría (colaboración del equipo). */
export default function CommentThread({ projectId, categoryId, comments, onChange, onError }: {
  projectId: string;
  categoryId: string;
  comments: CategoryComment[];
  onChange: () => void;
  onError: (msg: string) => void;
}) {
  const [commentText, setCommentText] = useState("");

  async function addComment(e: FormEvent) {
    e.preventDefault();
    if (!commentText.trim()) return;
    try {
      await analysisApi.addComment(projectId, categoryId, commentText.trim());
      setCommentText("");
      onChange();
    } catch (err) {
      onError((err as Error).message);
    }
  }

  return (
    <div style={{ marginTop: 6 }}>
      {comments.map((com) => (
        <div className="comment-box" key={com.id}>
          {com.text}
          <div className="meta">
            {com.author} · {new Date(com.timestamp).toLocaleString("es-CL")}
            <button className="btn btn-ghost btn-sm" style={{ padding: "0 6px", marginLeft: 6 }}
                    onClick={async () => { await analysisApi.deleteComment(projectId, categoryId, com.id); onChange(); }}>
              ✕
            </button>
          </div>
        </div>
      ))}
      <form onSubmit={addComment} style={{ display: "flex", gap: 6, marginTop: 8 }}>
        <input value={commentText} onChange={(e) => setCommentText(e.target.value)}
               placeholder="Nota para el equipo…" />
        <Button size="sm" type="submit" variant="secondary" disabled={!commentText.trim()}>Enviar</Button>
      </form>
    </div>
  );
}
