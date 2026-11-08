# letscook-skills

Claude Code skills for the Let's Cook iOS app.

## letscook-dish

Give Claude a recipe page, pasted blog text, a YouTube, TikTok, or Instagram link, or a local video file. It writes the dish in Let's Cook's clipboard format, checks it, and copies it to your Mac clipboard. On your iPhone, open Cookbook and tap Paste. Universal Clipboard moves it across when both devices use the same Apple Account.

### Install

In Claude Code:

```
/plugin marketplace add ImNotDarren/letscook-skills
/plugin install letscook-dish@letscook-skills
```

Then ask something like "make a Let's Cook dish from https://..." or paste a recipe.

To install without the plugin system, copy `plugins/letscook-dish/skills/letscook-dish` into `~/.claude/skills/`.

### Requirements

- Python 3 for the format checker.
- macOS for automatic clipboard copy. On other systems the checker prints the JSON for you to copy.
- For video links and files: [uv](https://docs.astral.sh/uv/) and ffmpeg (`brew install uv ffmpeg`).

### Updating

```
/plugin marketplace update letscook-skills
```
