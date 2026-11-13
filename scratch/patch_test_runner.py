with open('scratch/run_comprehensive_tests.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_req = '''    async def receive():
        return {"type": "http.request", "body": body_bytes, "more_body": False}

    async def send(message):
        nonlocal response_started, status_code, resp_headers
        if message["type"] == "http.response.start":
            response_started = True
            status_code = message["status"]
            resp_headers = message.get("headers", [])
        elif message["type"] == "http.response.body":
            resp_body.write(message.get("body", b""))'''

new_req = '''    response_finished = asyncio.Event()
    request_sent = False

    async def receive():
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": body_bytes, "more_body": False}
        await response_finished.wait()
        return {"type": "http.disconnect"}

    async def send(message):
        nonlocal response_started, status_code, resp_headers
        if message["type"] == "http.response.start":
            response_started = True
            status_code = message["status"]
            resp_headers = message.get("headers", [])
        elif message["type"] == "http.response.body":
            resp_body.write(message.get("body", b""))
            if not message.get("more_body", False):
                response_finished.set()'''

if old_req in text:
    text = text.replace(old_req, new_req, 1)
    with open('scratch/run_comprehensive_tests.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated request() in scratch/run_comprehensive_tests.py")
else:
    # Try CRLF
    old_req_crlf = old_req.replace('\n', '\r\n')
    new_req_crlf = new_req.replace('\n', '\r\n')
    if old_req_crlf in text:
        text = text.replace(old_req_crlf, new_req_crlf, 1)
        with open('scratch/run_comprehensive_tests.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Updated request() in scratch/run_comprehensive_tests.py (CRLF)")
    else:
        print("WARNING: Could not find old_req in scratch/run_comprehensive_tests.py")

