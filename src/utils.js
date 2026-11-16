// Small helpers for showing dates and time.

export function formatDate(isoDate) {
  if (!isoDate) return "No date set";
  // Add a time so the browser does not shift the day because of time zones.
  return new Date(`${isoDate}T12:00:00`).toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function minutesLabel(minutes) {
  return `${minutes} min`;
}

// How a plan's planned time compares with its target, in words.
export function timeBalance(total, target) {
  const difference = target - total;
  if (difference === 0) return { tone: "good", text: "Right on target" };
  if (difference > 0) return { tone: "open", text: `${difference} min left to fill` };
  return { tone: "over", text: `${Math.abs(difference)} min over target` };
}

// Used to give each category its own colour class, e.g. "Team Play" -> "cat-team-play".
export function categoryClass(category) {
  return `cat-${category.toLowerCase().replace(/[^a-z]+/g, "-")}`;
}
