"""Exercise installed MCP companion with archived internal data. No provider calls."""
import asyncio
import json
from pathlib import Path
import sys
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    started = time.monotonic()
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "examples/browseract/accepted/mcp-input.json").read_text(encoding="utf-8"))
    original = (root / "examples/browseract/accepted/result.csv").read_text(encoding="utf-8")
    if payload["payload"]["csv_text"] != original:
        raise RuntimeError("Example differs from preserved CSV")
    async with stdio_client(StdioServerParameters(command=sys.executable, args=["-m", "resultgate.browseract_demo"])) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            names = {t.name for t in (await session.list_tools()).tools}
            if not {"assess_browseract_fit", "validate_browseract_csv"} <= names:
                raise RuntimeError("Required tools unavailable")
            fit = await session.call_tool("assess_browseract_fit", {"request": {
                "product_urls": payload["payload"]["expected_urls"], "sources_permitted": True,
                "local_execution_sufficient": True}})
            if fit.isError or json.loads(fit.content[0].text)["decision"] != "free_first":
                raise RuntimeError("Free-first assessment failed")
            result = await session.call_tool("validate_browseract_csv", payload)
            if result.isError:
                raise RuntimeError("CSV tool failed")
            value = json.loads(result.content[0].text)
            check = value["validation"]
            if not check["all_successful"] or check["received_unique"] != 20 or value["raw_rows"][0]["price"] != "£51.77":
                raise RuntimeError("Internal fixture validation failed")
            print(json.dumps({"status":"passed", "origin":"internal", "rows":20,
                "decision":"free_first", "raw_values_preserved":True,
                "raw_csv_sha256":value["raw_csv_sha256"], "provider_run_started":False,
                "commission_approved":False, "elapsed_seconds":round(time.monotonic()-started,3)}, indent=2))

if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(main(), timeout=60))
