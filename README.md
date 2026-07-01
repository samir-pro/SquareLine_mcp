# SquareLine Studio MCP

An [MCP](https://modelcontextprotocol.io) server that lets Claude (or any MCP
client) **design LVGL UIs and export them as SquareLine Studio `.spj` project
files** — preset for the **Elecrow CrowPanel 5.0"** (ESP32, 800×480) and the
exact **LVGL 8.3.11** toolchain used by the [Elecrow CrowPanel Arduino
library](https://github.com/Elecrow-RD/CrowPanel-5.0-HMI-ESP32-Display-800x480).

You describe the UI in natural language → the MCP builds screens, widgets,
styles and screen-to-screen navigation → it writes a `.spj` you open in
SquareLine Studio, tweak visually, and export to your Arduino sketch.

> The `.spj` writer was reverse-engineered from genuine SquareLine **1.4.2 /
> 1.5.x, LVGL 8.3.11** exports. Object/screen/style/event structure and the
> widget-specific properties for the verified widgets (label, panel, button,
> image, imagebutton, slider, switch, bar, arc, roller, spinbox, keyboard,
> tabview, textarea, chart) match those exports property-for-property. The
> remaining widgets reuse the same verified scaffolding; open + re-save once in
> SquareLine to normalise before exporting.

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
| `set_property(widget, x, y, width, height, value, align, hidden, clickable, checkable, disabled)` | Update geometry / value / core flags. |
| `configure_widget(widget, property, value)` | Set any widget-specific config (e.g. `Range=[0,255]`, `Mode`, `Options`). |
| `set_style(widget, part, state, bg_color, text_color, radius, …, props_json)` | Full styling on any **part** and **state**; `props_json` reaches every style key (shadow, gradient, outline, pad…). |
| `set_flag(widget, flag, value)` | Set any `OBJECT` flag (scrollable, floating, hidden, scrollbar_mode…). |
| `set_layout(widget, type, flow, wrap, *_align)` | Give a container a Flex or Grid layout. |
| `add_event(widget, action, trigger, target, value, params_json)` | Attach **any** event action (see below). |
| `add_navigation(widget, target_screen, trigger, fade, speed)` | Convenience *Change Screen* event. |
| `list_project()` / `list_widget_types()` / `list_actions()` / `list_styles()` | Introspection. |
| `export_project(path)` | Write `<Name>.spj`. |
| `get_board_info()` / `get_setup_guide()` | Reference helpers. |

### Supported widgets (27)

`panel`, `button`, `label`, `image`, `imagebutton`, `slider`, `switch`, `bar`,
`arc`, `checkbox`, `dropdown`, `roller`, `textarea`, `spinbox`, `keyboard`,
`tabview`, `tabpage`, `tileview`, `window`, `list`, `messagebox`, `chart`,
`table`, `calendar`, `meter`, `led`, `line`, `spinner`, `colorwheel`, `canvas`,
`animimg`, `buttonmatrix` — plus aliases (`btn`, `img`, `text`, `toggle`,
`gauge`, `progress`, `input`, `combobox`, …). Containers (panel, button,
tabview, tabpage, tileview, window, list, messagebox) hold child widgets.

### Event actions (21, verbatim from real exports)

`CHANGE SCREEN`, `DELETE SCREEN`, `BASIC_PROPERTY`, `LABEL_PROPERTY`,
`SLIDER_PROPERTY`, `BAR_PROPERTY`, `ROLLER_PROPERTY`, `SET OPACITY`,
`MODIFY FLAG`, `MODIFY STATE`, `INCREMENT ARC/BAR/SLIDER`, `STEP SPINBOX`,
`MOVE CURSOR`, `KEYBOARD SET TARGET`, `SET TEXT VALUE FROM ARC/SLIDER`,
`PLAY ANIMATION`, `SWITCH THEME`, `CALL FUNCTION`. Each carries SquareLine's
exact C call templates, so exported `ui_events` code is correct. All triggers
supported (CLICKED, VALUE_CHANGED, LONG_PRESSED, SCREEN_LOADED, …).

### Styling

Every style key — `bg_color`, `bg_grad_color`, `bg_grad_dir`, `radius`,
`border_color/width/side`, `outline_*`, `shadow_color/offset/params`,
`line_color`, `image_recolor`, `text_color/font/align`, `opacity`, `pad` — on
any part (`main`, `indicator`, `knob`, `selected`, `scrollbar`, `items`,
`cursor`, `ticks`, `placeholder`) and any state (`DEFAULT`, `PRESSED`,
`CHECKED`, `DISABLED`, `FOCUSED`, combinable with `|`).

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
  server.py         MCP server + 17 tools (FastMCP)
  project.py        in-memory UI model + .spj assembler
  spj.py            .spj property serialization (reverse-engineered schema)
  widgets.py        widget catalogue (config props + style parts)
  styles.py         full style-property catalogue, parts, states
  events.py         event/action builder (loads data/actions.json)
  board.py          CrowPanel presets + the project `info` block
  guide.py          the CrowPanel/SquareLine/Arduino setup guide
  data/actions.json verbatim action templates from real exports
docs/SETUP.md       the same setup guide, rendered
examples/           demo script + MCP config
tests/              schema tests
```

## License

MIT
