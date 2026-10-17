const dateFormatter = new Intl.DateTimeFormat("es-MX", { day: "2-digit", month: "short", year: "numeric" });
const dateTimeFormatter = new Intl.DateTimeFormat("es-MX", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  return dateFormatter.format(new Date(value.length === 10 ? `${value}T00:00:00` : value));
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  return dateTimeFormatter.format(new Date(value));
}

function pad(n: number) {
  return String(n).padStart(2, "0");
}

/** ISO (UTC) → valor para <input type="datetime-local"> en hora local. */
export function toDateTimeInput(value: string | null | undefined): string {
  if (!value) return "";
  const d = new Date(value);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** Valor de <input type="datetime-local"> → ISO UTC para la API. */
export function fromDateTimeInput(value: string): string {
  return new Date(value).toISOString();
}
