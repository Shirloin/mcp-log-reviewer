import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def query_loki_logs(
    loki_url: str,
    query: str,
    limit: int = 100,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Query logs from Loki and return formatted results.

    This is the main function to be used as an MCP tool.

    Args:
        loki_url: URL to Loki instance (e.g., 'http://localhost:3100')
        query: LogQL query string (e.g., '{job="my-app"} |~ "error"')
        limit: Maximum number of log entries to return (default: 100)
        start_time: Optional start time for the query (default: 5 minutes ago)
        end_time: Optional end time for the query (default: now)

    Returns:
        Dictionary containing query results with logs and metadata
    """
    try:
        loki_url = loki_url.rstrip('/')

        # Set default time range if not provided
        if end_time is None:
            end_time = datetime.now()
        if start_time is None:
            start_time = end_time - timedelta(minutes=5)

        # Convert to nanoseconds (Loki uses nanoseconds)
        start_ns = int(start_time.timestamp() * 1e9)
        end_ns = int(end_time.timestamp() * 1e9)

        params = {
            'query': query,
            'start': start_ns,
            'end': end_ns,
            'limit': limit,
            'direction': 'forward'
        }

        response = requests.get(
            f'{loki_url}/loki/api/v1/query_range',
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        # Process the logs
        logs = []
        results = data.get('data', {}).get('result', [])

        for stream in results:
            values = stream.get('values', [])
            stream_labels = stream.get('stream', {})

            for timestamp_str, log_line in values:
                timestamp = int(timestamp_str)
                logs.append({
                    'timestamp': datetime.fromtimestamp(timestamp / 1e9).isoformat(),
                    'message': log_line,
                    'labels': stream_labels
                })

        # Sort logs by timestamp
        logs.sort(key=lambda x: x['timestamp'])

        return {
            'success': True,
            'query': query,
            'count': len(logs),
            'logs': logs,
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            }
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to query Loki: {e}")
        return {
            'success': False,
            'error': str(e),
            'query': query,
            'count': 0,
            'logs': []
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            'success': False,
            'error': str(e),
            'query': query,
            'count': 0,
            'logs': []
        }

