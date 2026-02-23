/**
 * Remote control key mappings for TV environment.
 * Use these constants instead of hardcoded strings to ensure consistency.
 */
export const KEY_CODES = {
  ARROW_UP: "ArrowUp",
  ARROW_DOWN: "ArrowDown",
  ARROW_LEFT: "ArrowLeft",
  ARROW_RIGHT: "ArrowRight",
  ENTER: "Enter",
  ESCAPE: "Escape",
  BACKSPACE: "Backspace",
} as const;

export type KeyCode = (typeof KEY_CODES)[keyof typeof KEY_CODES];
