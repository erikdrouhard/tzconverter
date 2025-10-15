import air
from tzconverter.timezones import get_common_timezones, get_current_time_in_timezone

app = air.Air()

@app.get("/")
async def index():
  return air.Html(
    air.Head(
      air.Meta(charset="utf-8"),
      air.Meta(name="viewport", content="width=device-width, initial-scale=1"),
      air.Title("Timezone Meeting Scheduler"),
      air.Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"),
      air.Script(src="https://unpkg.com/htmx.org@1.9.10"),
    ),
    air.Body(
      air.Main(
        {"class": "container"},
        air.H1("Timezone Meeting Scheduler"),
        air.P("Select timezones to find optimal meeting times across the globe."),
        air.Article(
          air.H2("Quick Start"),
          air.P("✓ Created timezone utilities module"),
          air.P("✓ Added Pico CSS styling"),
          air.P("✓ Added HTMX for interactivity"),
          air.P("→ Next: Add timezone selector and cards")
        )
      )
    )
  )
