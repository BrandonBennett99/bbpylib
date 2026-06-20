def split_text_at_spaces(s, max_len):
   parts, cur = [], ""
   for w in s.split(" "):
        cand = w if not cur else cur + " " + w
        if len(cand) <= max_len:
            cur = cand
        else:
            if cur:
                parts.append(cur)
                cur = w
            else:
                parts.append(w)
   if cur:
        parts.append(cur)
   return parts

def wrap_string_as_code(s: str, max_len: int) -> str:
    parts = split_text_at_spaces(s, max_len )
    print(parts)
    return "(\n" + "\n ".join(f'    "{p}"' for p in parts) + "\n)"