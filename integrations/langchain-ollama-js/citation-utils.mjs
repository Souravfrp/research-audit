export function coversRange(passage, path, start, end) {
  return passage !== undefined &&
    start <= end &&
    passage.path === path &&
    passage.start <= start &&
    passage.end >= end;
}
