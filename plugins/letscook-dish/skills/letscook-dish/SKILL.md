---
name: letscook-dish
description: This skill should be used when the user asks to "extract a dish", "turn this recipe into a Let's Cook dish", "make a dish JSON", "copy this recipe to my clipboard for the app", "get the recipe from this video", or pastes a recipe description, blog text, YouTube, TikTok, or Instagram link, or a local video file and wants it imported into the Let's Cook iOS app. It writes the app's clipboard dish format and copies it to the macOS clipboard.
version: 0.1.0
---

# Let's Cook dish extraction

The Let's Cook app imports dishes from the clipboard. In the Cookbook tab, the Paste button reads a JSON string, saves each dish to the household's iCloud zone, and opens it. This skill turns a recipe source into that string, validates it, and copies it to the Mac clipboard. Universal Clipboard then makes it available on an iPhone signed in to the same Apple Account.

## The format

```json
{
  "letscook": 1,
  "name": "Chicken Adobo",
  "category": "Mains",
  "serves": 4,
  "steps": [
    "Brown [800 g|chicken thighs] in a heavy pot for {8 min}.",
    "Add [6 cloves|garlic] and [3|bay leaves]. Cook {1 min}.",
    "Pour in [80 ml|soy sauce] and [80 ml|cane vinegar]. Cover and simmer {30 min}.",
    "Uncover and reduce the sauce for {10 min}. Serve over [300 g|rice]."
  ]
}
```

A JSON array of these objects imports several dishes at once. Fields:

| Field | Rule |
|-------|------|
| `letscook` | Always `1`. The app ignores anything else. |
| `name` | Short dish name in title case, without the creator's name or clickbait. |
| `category` | `Mains`, `Sides`, or `Sweets`. Anything else becomes Mains. |
| `serves` | Integer 1 to 24. Use the source's yield; estimate from quantities if absent. |
| `steps` | Ordered strings. Ingredients and times live inside the step that uses them. |

There is no separate ingredient list. The app derives the ingredient totals, the shopping list, and Cook Mode timers from two inline tokens.

**Ingredient token** `[amount unit|item]`, for example `[2 tbsp|olive oil]`, `[1/2 cup|milk]`, `[3|eggs]`. The amount must be a plain number (`2`, `0.5`) or a simple fraction (`1/2`). Write `1.5` instead of `1½` or `1 1/2`. A range such as `2-3` does not parse, so pick the midpoint or the lower bound. Prefer the units the editor offers: `g`, `kg`, `ml`, `L`, `tsp`, `tbsp`, `cup`, `cloves`, `pinch`, or no unit for whole items. Grams and millilitres get the nicest rounding when scaled. For "salt to taste", write plain text or `[1 pinch|salt]`.

**Timer token** `{N min}`, for example `{25 min}`. Whole minutes only, so convert hours (`1 h 30` becomes `{90 min}`). Cook Mode uses the first timer in a step, so split a step that has two timed stretches.

Rules that keep the derived lists correct:

- Use the same item name every time an ingredient appears (`olive oil`, not `olive oil` then `EVOO`). The shopping list merges by exact name.
- When an ingredient is split across steps, token each portion with its own amount so the totals add up to the recipe's full quantity. Never repeat the full amount in a second step. Mention a reused ingredient without a token when no new quantity is added.
- Put prep in the item only when it changes what to buy (`[400 g|crushed tomatoes]`). Otherwise keep prep in the prose (`[1|onion], diced`).
- Keep steps short and action-led, one cooking stage each. Oven temperatures stay as plain text.

## Workflow

Video sources need `uv` and `ffmpeg`. If either is missing, tell the user how to install it (`brew install uv ffmpeg` on macOS) and fall back to any text the user can paste.

1. **Gather the source text.**
   - Pasted description or blog text: use it directly.
   - Web page URL: fetch it with WebFetch and pull out the ingredient list and method.
   - YouTube, TikTok, or Instagram URL: fetch the description and captions with yt-dlp through uv, writing into the session scratchpad:
     ```bash
     uvx yt-dlp --skip-download --write-description --write-subs --write-auto-subs \
       --sub-langs "en.*" --sub-format vtt -o "<scratchpad>/video" "<url>"
     ```
     Read `video.description` and the `.vtt` file. Many creators put the full recipe in the description or a pinned link; follow that link when present.
   - Local video file, or a video whose captions are missing: sample frames for on-screen text and ingredient shots, then view them with Read.
     ```bash
     ffmpeg -i "<video>" -vf "fps=1/3,scale=720:-1" "<scratchpad>/frame_%03d.jpg"
     ```
     Transcribing speech needs Whisper, which downloads a large model. Ask before running `uvx --from openai-whisper whisper "<video>" --model base --output_format txt --output_dir "<scratchpad>"`.
2. **Reconcile.** Merge the ingredient list with the method. Convert loose quantities ("a splash", "a handful") into a sensible number and unit, and tell the user which quantities were estimated.
3. **Write the JSON** to `<scratchpad>/dish.json` following the rules above.
4. **Validate and copy:**
   ```bash
   python3 "<skill dir>/scripts/check_dish.py" "<scratchpad>/dish.json"
   ```
   `<skill dir>` is the base directory shown when this skill loads. Use the session scratchpad if there is one, otherwise a temporary directory.
   Fix every reported problem and rerun until it prints `OK`. The script copies compact JSON to the clipboard on success; pass `--no-copy` to only validate.
5. **Report** the dish name, serves, step count, and any estimated quantities in a few lines. Tell the user to open Cookbook on the phone and tap Paste. Also print the JSON in a code block, since the app also accepts it when copied from chat with the fence included.

## Resources

- **`scripts/check_dish.py`** validates the format against the same rules as the app's importer, then copies it with `pbcopy`. Off macOS it prints the compact JSON instead, for the user to copy by hand.
