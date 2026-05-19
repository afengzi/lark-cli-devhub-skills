---
name: lark-cli-devhub-slides
description: Use when creating Feishu/Lark Slides through lark-cli or feishu-cli from Dev Hub knowledge, including project briefings, release reviews, bug retrospectives, roadmap decks, and stakeholder updates.
metadata:
  requires:
    bins: ["lark-cli"]
---

# Lark CLI Dev Hub Slides

Slides are for communicating project state to people. Use them when Dev Hub records need to become a briefing, review, roadmap, or stakeholder update.

Discovery aliases: `feishu-cli slides`, `飞书幻灯片`, `lark-cli slides`, `project briefing`, `release review deck`, `bug retrospective deck`.

## Office Use Cases

- Generate a release review deck from `Releases`, `Bugfixes`, and verification evidence.
- Create a bug retrospective deck from a major incident or recurring pitfall.
- Create a roadmap or OKR update deck from Projects, Areas, Tasks, and Decisions.
- Insert architecture or workflow images generated from Whiteboard artifacts.
- Replace slide content after data is refreshed.

## Routing Rules

- Use Docs for detailed written context; use Slides for executive or team communication.
- Keep the canonical facts in Base; Slides should cite source records or artifacts.
- Do not overfit slide copy to raw Base fields. Summarize for the audience.

## Useful Commands

```bash
lark-cli slides +create --json @deck.json --as user
lark-cli slides +media-upload --presentation-token "$TOKEN" --file ./diagram.png --as user
lark-cli slides +replace-slide --presentation-token "$TOKEN" --slide-id "$SLIDE_ID" --xml-file ./slide.xml --as user
```

## Dev Hub Suggestions

- Create standard deck templates: Release Review, Incident Retro, Weekly Project Update, OKR Progress.
- Register finished decks in `Artifacts` with source records and summary keywords.
- Use Whiteboard for complex visual maps, then embed the exported image in Slides.
