export function formatDate(value: string | null) {
  if (!value) return "";
  return new Intl.DateTimeFormat("de-DE").format(new Date(value));
}

export function formatNullableDate(value: string | null) {
  return value ? formatDate(value) : "Nicht gesetzt";
}

export function dateInputValue(value: string | null) {
  if (!value) return "";
  return new Date(value).toISOString().slice(0, 10);
}

export function dateInputToDateTime(value: string) {
  if (!value) return null;
  return new Date(`${value}T12:00:00`).toISOString();
}

export function daysSince(value: string | null) {
  if (!value) return 0;
  return Math.max(
    0,
    Math.floor((Date.now() - new Date(value).getTime()) / 86_400_000),
  );
}

export function daysSinceDate(value: string | null) {
  if (!value) return "Nicht gesetzt";
  const days = daysSince(value);
  if (days === 0) return "Heute";
  if (days === 1) return "1 Tag";
  return `${days} Tage`;
}

export function isFollowUpDue(value: string | null) {
  if (!value) return false;
  const followUpDate = new Date(value);
  const today = new Date();
  followUpDate.setHours(0, 0, 0, 0);
  today.setHours(0, 0, 0, 0);
  return followUpDate.getTime() <= today.getTime();
}

export function relativeDate(value: string) {
  const date = new Date(value);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / 86_400_000);
  if (diffDays <= 0) return "Heute";
  if (diffDays === 1) return "Gestern";
  return formatDate(value);
}
