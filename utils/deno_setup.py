import os
import shutil
import subprocess
from pathlib import Path


def ensure_deno():
    deno = shutil.which("deno")

    if deno:
        return deno

    deno_dir = Path.home() / ".deno"
    deno_bin = deno_dir / "bin"
    deno_exe = deno_bin / "deno"

    if not deno_exe.exists():
        env = os.environ.copy()
        env["DENO_INSTALL"] = str(deno_dir)

        subprocess.run(
            [
                "sh",
                "-c",
                "curl -fsSL https://deno.land/install.sh | sh",
            ],
            check=True,
            env=env,
        )

    os.environ["PATH"] = (
        str(deno_bin) + os.pathsep + os.environ.get("PATH", "")
    )

    return str(deno_exe)
