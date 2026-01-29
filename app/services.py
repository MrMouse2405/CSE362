def process_form(data: dict) -> dict:
    """
    Application-layer logic.
    Accepts raw inputs and returns a structured outcome for the UI.
    """
    required = ["field1", "field2"]
    missing = [k for k in required if not data.get(k, "").strip()]

    if missing:
        return {
            "ok": False,
            "message": f"Missing fields: {', '.join(missing)}",
            "result": None
        }

    return {
        "ok": True,
        "message": "Submitted successfully!",
        "result": {
            "field1": data["field1"].strip(),
            "field2": data["field2"].strip()
        }
    }