from fastapi import Request


def client_ip(request: Request) -> str:
    """The caller's IP.

    `X-Forwarded-For` is honoured only when TRUST_PROXY_HEADERS is on, and then only its LAST
    entry: that is the address our own trusted proxy appended. Everything to its left was supplied
    by the client and can be forged, so using the first entry would let an attacker dodge rate
    limits just by changing the header on every request.
    """
    if request.app.state.settings.TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"
