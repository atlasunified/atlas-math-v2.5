from __future__ import annotations

from atlas_math.cli_commands import build_parser, dispatch_command
from atlas_math.cli_interactive import interactive_menu


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        return interactive_menu()
    return dispatch_command(args)


if __name__ == "__main__":
    raise SystemExit(main())

