# SquareLine Studio MCP

An [MCP](https://modelcontextprotocol.io) server that lets Claude (or any MCP
client) **design LVGL UIs and export them as SquareLine Studio `.spj` project
files** — preset for the **Elecrow CrowPanel 5.0"** (ESP32, 800×480) and the
exact **LVGL 8.3.11** toolchain used by the [Elecrow CrowPanel Arduino
library](https://github.com/Elecrow-RD/CrowPanel-5.0-HMI-ESP32-Display-800x480).

You describe the UI in natural language → the MCP builds screens, widgets,
styles and screen-to-screen navigation → it writes a `.spj` you open in
SquareLine Studio, tweak visually, and export to your Arduino sketch.

> The `.spj` writer was reverse-engineered from a genuine SquareLine **1.4.2 /
> LVGL 8.3.11** CrowPanel export. The shared object/screen/label property blocks
> match that export byte-for-structure; other widget types reuse the same
> verified scaffolding, and SquareLine fills any widget-specific defaults on
> first open. Always open + re-save in SquareLine to normalise before exporting.

## Why this workflow

SquareLine Studio has no scripting API, but its project files are JSON. This MCP
generates that JSON directly, so you get AI-assisted layout while keeping
SquareLine in the loop for visual fine-tuning and its battle-tested LVGL code
export. See [`docs/SETUP.md`](docs/SETUP.md) for matching SquareLine + Arduino
versions to your CrowPanel.

## Install

```bash
pip install -e .          # from the repo root (installs the `mcp` dependency)
```

Requires Python ≥ 3.10.

## Register with an MCP client

**Claude Code / Claude Desktop** — add to your MCP config
(`claude_desktop_config.json` or `.mcp.json`):

```json
{
  "mcpServers": {
    "squareline": {
      "command": "python",
      "args": ["-m", "squareline_mcp"]
    }
  }
}
```

(Or use the installed console script `squareline-mcp` as the `command`.)
See [`examples/mcp-config.json`](examples/mcp-config.json).

## Tools

| Tool | What it does |
|------|--------------|
| `create_project(name, preset, width, height)` | Start a project. Presets: `crowpanel-5` (default), `crowpanel-7`, `crowpanel-4.3`, `crowpanel-2.8`. |
| `add_screen(name)` | Add a screen (first one is the start screen). |
| `add_widget(screen, type, name, x, y, width, height, value, parent, align)` | Add a widget, optionally nested in a container. |
| `set_style(widget, bg_color, radius, border_*, text_color, text_font, text_align, pad, …)` | Set common MAIN/DEFAULT style props. Colours accept `#RRGGBB` or `[r,g,b,a]`. |
| `set_property(widget, x, y, width, height, value, align, hidden, clickable, checkable, disabled)` | Update an existing widget. |
| `add_navigation(widget, target_screen, trigger, fade, speed)` | Add a *Change Screen* event. |
| `list_project()` | Print the screen/widget tree. |
| `export_project(path)` | Write `<Name>.spj`. |
| `list_widget_types()` / `get_board_info()` / `get_setup_guide()` | Reference helpers. |

### Supported widgets

`panel`, `label`, `button`, `image`, `slider`, `switch`, `bar`, `arc`,
`checkbox`, `dropdown`, `roller`, `textarea` — plus aliases like `btn`, `img`,
`text`, `toggle`, `progress`, `gauge`, `input`. `panel` and `button` are
containers (can hold child widgets).

## Example prompt

> Create a CrowPanel project called "Thermostat". Add a HomeScreen with a title
> label "Living Room", a big temperature label, a slider for the setpoint, and a
> Settings button that navigates to a SettingsScreen. Export it.

## Try it without an MCP client

```bash
python examples/demo_dashboard.py    # writes CrowDemo.spj
python tests/test_spj.py             # run the schema tests
```

## Layout

```
src/squareline_mcp/
  server.py    MCP server + tools (FastMCP)
  project.py   in-memory UI model + .spj assembler
  spj.py       .spj property serialization (reverse-engineered schema)
  widgets.py   widget catalogue + style records
  board.py     CrowPanel presets + the project `info` block
  guide.py     the CrowPanel/SquareLine/Arduino setup guide
docs/SETUP.md  the same setup guide, rendered
examples/      demo script + MCP config
tests/         schema tests
```

## License

MIT
