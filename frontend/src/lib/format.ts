export function initials(name: string): string {
  const words = name.split(/\s+/).filter((w) => /^\p{L}/u.test(w));
  const letters = words.slice(0, 2).map((w) => w[0].toLocaleUpperCase());
  return letters.length ? letters.join("") : "?";
}
