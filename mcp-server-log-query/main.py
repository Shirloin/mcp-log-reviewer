from dotenv import load_dotenv
import os
import time

from mcp.server.fastmcp import FastMCP
from log_query import query_loki_logs
import json
from datetime import datetime, timedelta

load_dotenv()

mcp = FastMCP(
    name="mcp-log-query",
)


@mcp.tool()
def log_query() -> str:
    """
    Query logs from Loki using LogQL.

    Returns:
        JSON string containing query results with logs and metadata
    """

    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=5)
    limit = 100
    query = '{service="easy-buy-backend"}'
    loki_url = os.getenv("LOKI_URL")

    # Query logs
    result = query_loki_logs(
        loki_url=loki_url,
        query=query,
        limit=limit,
        start_time=start_time,
        end_time=end_time
    )

    return json.dumps(result, indent=2)



if __name__ == "__main__":
    mcp.run(transport="stdio")
