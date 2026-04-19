from mcp.server.fastmcp import FastMCP

from services import (
    get_anomalies_service,
    get_complaints_service,
    get_faults_service,
    get_metrics_service,
    get_station_service,
)

mcp = FastMCP("Telecom_AI_Agent")


@mcp.tool()
def get_metrics(cell_id: str, slice_type: str | None = None, since: str | None = None, limit: int = 10):
    return get_metrics_service(cell_id=cell_id, slice_type=slice_type, since=since, limit=limit)


@mcp.tool()
def get_anomalies(
    cell_id: str | None = None,
    severity: str | None = None,
    only_anomalies: bool = True,
    limit: int = 50,
):
    return get_anomalies_service(
        cell_id=cell_id,
        severity=severity,
        only_anomalies=only_anomalies,
        limit=limit,
    )


@mcp.tool()
def get_faults(
    cell_id: str | None = None,
    region: str | None = None,
    resolved: bool | None = None,
    limit: int = 50,
):
    return get_faults_service(cell_id=cell_id, region=region, resolved=resolved, limit=limit)


@mcp.tool()
def get_complaints(
    cell_id: str | None = None,
    region: str | None = None,
    since: str | None = None,
    limit: int = 50,
):
    return get_complaints_service(cell_id=cell_id, region=region, since=since, limit=limit)


@mcp.tool()
def get_station(
    cell_id: str | None = None,
    region: str | None = None,
    status: str | None = None,
    limit: int = 50,
):
    return get_station_service(cell_id=cell_id, region=region, status=status, limit=limit)


if __name__ == "__main__":
    mcp.run()
