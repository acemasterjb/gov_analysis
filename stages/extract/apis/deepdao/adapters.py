def get_snapshot_id(raw_dao_data: list[dict], index: int = 0) -> str | None:
    snapshot_object: dict = raw_dao_data[index]
    if "Snapshot" not in snapshot_object.get("platformTitle"):
        if len(raw_dao_data) <= index + 1:
            return None
        return get_snapshot_id(raw_dao_data, index + 1)
    return (
        snapshot_object["website"].split("/")[-1]
        if snapshot_object["website"]
        else None
    )
