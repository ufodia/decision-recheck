"""Public command-line interface. Partial work remains explicitly labeled."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from . import __version__
from .demo import build_demo,example_brief
from .engine import run_case
from .models import BriefError
from .render import render_report
from .storage import load_bundle,write_json
from .validate import validate_bundle

def parser():
    p=argparse.ArgumentParser(prog="decision-recheck",description="Scoped product evidence, three decision views and explicit rechecks.")
    p.add_argument("--version",action="version",version=__version__)
    commands=p.add_subparsers(dest="command",required=True)
    demo=commands.add_parser("demo",help="Generate the fictional model-free A/B/C and footer control.")
    demo.add_argument("--output",type=Path,required=True)
    init=commands.add_parser("init",help="Write an editable fictional brief.")
    init.add_argument("--output",type=Path,default=Path("brief.json"))
    for command in ("run","recheck"):
        runner=commands.add_parser(command)
        runner.add_argument("--brief",type=Path,required=True)
        runner.add_argument("--output",type=Path,required=True)
        runner.add_argument("--live-model",action="store_true")
        if command=="recheck":
            runner.add_argument("--baseline",type=Path,required=True)
    report=commands.add_parser("report",help="Render validated stored evidence as a historical report.")
    report.add_argument("--bundle",type=Path,required=True)
    report.add_argument("--view",choices=("owner","buyer","marketing"),default="owner")
    report.add_argument("--output",type=Path,required=True)
    validate=commands.add_parser("validate")
    validate.add_argument("--bundle",type=Path,required=True)
    return p

def main(argv=None):
    args=parser().parse_args(argv)
    try:
        if args.command=="init":
            if args.output.exists():
                raise BriefError("Refusing to overwrite an existing brief.")
            write_json(args.output,example_brief("A"))
            print(f"Editable fictional brief: {args.output}")
        elif args.command=="demo":
            summary=build_demo(args.output)
            print(json.dumps({"status":"complete","fictional":True,"snapshots":len(summary["snapshots"]),"output":str(args.output)}))
        elif args.command in ("run","recheck"):
            bundle=run_case(args.brief,args.output,baseline=getattr(args,"baseline",None),live_model=args.live_model)
            print(json.dumps({"status":bundle["status"],"freshness":bundle["freshness"]["state"],"output":str(args.output),"warnings":bundle["warnings"]}))
        elif args.command=="validate":
            errors=validate_bundle(args.bundle)
            print(json.dumps({"valid":not errors,"errors":errors},indent=2))
            return 1 if errors else 0
        elif args.command=="report":
            errors=validate_bundle(args.bundle)
            if errors:
                raise BriefError("Evidence validation failed: "+"; ".join(errors))
            bundle,root=load_bundle(args.bundle)
            if args.output.resolve().parent!=root.resolve():
                raise BriefError("Place the report in the bundle directory so evidence links stay valid.")
            if args.output.exists():
                raise BriefError("Refusing to overwrite an existing report.")
            bundle["freshness"]={**bundle.get("freshness",{}),"state":"HISTORICAL","meaning":"Rendered from stored evidence; no current-source validation was performed by this command."}
            args.output.write_text(render_report(bundle,args.view),encoding="utf-8")
            print(f"Historical {args.view} report: {args.output}")
        return 0
    except (BriefError,ValueError,OSError,RuntimeError) as error:
        print(f"decision-recheck: {error}",file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
