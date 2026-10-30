import { InputHTMLAttributes, TextareaHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export default function Input({ label, error, id, ...rest }: InputProps) {
  const inputId = id ?? (label ? `in_${label.replace(/\W/g, "_")}` : undefined);
  return (
    <div>
      {label && <label className="field-label" htmlFor={inputId}>{label}</label>}
      <input id={inputId} aria-invalid={error ? true : undefined}
             aria-describedby={error && inputId ? `${inputId}_err` : undefined} {...rest} />
      {error && <div className="field-error" id={inputId ? `${inputId}_err` : undefined}>{error}</div>}
    </div>
  );
}

interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export function TextArea({ label, error, id, ...rest }: TextAreaProps) {
  const inputId = id ?? (label ? `ta_${label.replace(/\W/g, "_")}` : undefined);
  return (
    <div>
      {label && <label className="field-label" htmlFor={inputId}>{label}</label>}
      <textarea id={inputId} {...rest} />
      {error && <div className="field-error">{error}</div>}
    </div>
  );
}
