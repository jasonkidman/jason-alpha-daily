#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined

REQUIRED = ["meta","executive","scores","portfolio","global_markets","breadth","health_checks","drawdown","macro","technology","outlook","china_markets","china_summary","long_term_dashboard","actions"]

def main() -> int:
    p = argparse.ArgumentParser(description="Render Jason Alpha Daily V5 visual briefing")
    p.add_argument("--data", required=True)
    p.add_argument("--template", default=str(Path(__file__).with_name("template_v1.0.html.j2")))
    p.add_argument("--html", default="rendered_v1.0.html")
    p.add_argument("--png", default="rendered_v1.0.png")
    args = p.parse_args()

    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED if k not in data]
    if missing:
        raise ValueError("Missing required fields: " + ", ".join(missing))

    template_path = Path(args.template).resolve()
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        undefined=StrictUndefined,
        autoescape=True,
    )
    rendered = env.get_template(template_path.name).render(**data)

    html_path = Path(args.html).resolve()
    html_path.write_text(rendered, encoding="utf-8")
    png_path = Path(args.png).resolve()

    cmd = [
        "chromium", "--headless", "--disable-gpu", "--no-sandbox",
        "--hide-scrollbars", "--window-size=1440,1880",
        f"--screenshot={png_path}", html_path.as_uri(),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("HTML:", html_path)
    print("PNG: ", png_path)
    return 0

if __name__ == "__main__":
    sys.exit(main())
