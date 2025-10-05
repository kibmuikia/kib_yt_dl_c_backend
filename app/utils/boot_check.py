import sys
from app.utils.tool_check import check_tool_exists, get_tool_version

REQUIRED_TOOLS = ["yt-dlp", "ffmpeg", "ffprobe"]

def perform_boot_check():
    """Ensures all required tools are installed before the server starts."""
    print("\n🚀 Boot Check: Verifying required tools...\n")

    all_present = True
    for tool in REQUIRED_TOOLS:
        exists = check_tool_exists(tool)
        if exists:
            version = get_tool_version(tool)
            print(f"✅ {tool} found → {version}")
        else:
            print(f"❌ {tool} missing — please install before running.")
            all_present = False

    if not all_present:
        print("\n💥 Boot check failed: Missing dependencies detected.\n")
        print("🔧 On macOS, install via:")
        print("   brew install yt-dlp ffmpeg\n")
        sys.exit(1)
    else:
        print("\n🎉 All dependencies verified — starting server...\n")
