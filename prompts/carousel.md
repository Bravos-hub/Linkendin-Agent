# Carousel Outline Template

Generate only on carousel days (see config/schedule.yaml) or when the topic is inherently list-like.

## Structure: 6–8 slides

- **Slide 1 (Cover):** Em-dash title + one-line promise of what the reader learns. No emoji.
- **Slides 2–6 (Body):** One idea per slide. Header (sentence case, max 6 words) + 2–3 short lines of supporting text with one precise figure per slide.
- **Slide 7 (Lesson):** The quotable takeaway, styled like the "The lesson?" line.
- **Slide 8 (CTA):** Engagement question + "Follow for more EV infrastructure analysis" + #Shuolex #EVZONE #bravostech.

## Output format
Return the outline as Markdown with one `## Slide N` section per slide, plus a `design_notes` line per slide describing the visual (diagram, map, chart, icon set) so the image prompt generator can use it.
