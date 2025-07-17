async def process_upload(shipment, receive, yard):
    # ここにファイル読み込み、DB保存などの処理を書く
    results = {}
    for csv_type, file in [
        ("shipment", shipment),
        ("receive", receive),
        ("yard", yard),
    ]:
        if file:
            content = await file.read()
            results[csv_type] = {"filename": file.filename, "size": len(content)}
        else:
            results[csv_type] = None
    return {"received": results}
