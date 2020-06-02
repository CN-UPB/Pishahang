def create_error_response(message: str):
    return {"request_status": "ERROR", "message": message}


def create_completed_response(response={}):
    response.setdefault("request_status", "COMPLETED")
    return response
