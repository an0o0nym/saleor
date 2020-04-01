#!/usr/bin/env python3
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")

    if (
        os.environ.get("RUN_MAIN") or os.environ.get("WERKZEUG_RUN_MAIN")
    ) and os.environ.get("VSCODE_DEBUGGER", False):
        import ptvsd

        ptvsd_port = os.environ.get("PORT_PTVSD", 5678)

        try:
            ptvsd.enable_attach(address=("0.0.0.0", ptvsd_port))
            print("Started ptvsd at port %s." % ptvsd_port)
        except OSError:
            print("ptvsd port %s already in use." % ptvsd_port)
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
