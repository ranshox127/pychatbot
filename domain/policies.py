# domain/policies.py
def needs_genai(latest: dict) -> bool:
    return latest and latest.get("penalty") != -1 and bool(latest.get("loss_kw"))
