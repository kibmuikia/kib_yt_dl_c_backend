import subprocess

def run_shell_command(cmd):
    """Run a shell command safely and return output."""
    try:
        result = subprocess.run(cmd, shell=True, check=True,
                                capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"

