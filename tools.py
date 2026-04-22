def mock_lead_capture(name: str, email: str, platform: str) -> str:
    message = f"Lead captured successfully: {name}, {email}, {platform}"
    print(message)
    return message
