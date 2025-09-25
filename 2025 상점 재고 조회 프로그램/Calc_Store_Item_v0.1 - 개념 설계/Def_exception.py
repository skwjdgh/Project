from flask import jsonify
from werkzeug.exceptions import NotFound, MethodNotAllowed, HTTPException

class BadRequestError(Exception):
    def __init__(self, msg): self.msg = msg

def register_error_handlers(app):
    @app.errorhandler(BadRequestError)
    def _badreq(e):
        return jsonify({"error":{"code":"BAD_REQUEST","message":e.msg}}), 400

    @app.errorhandler(NotFound)
    def _notfound(e):
        return jsonify({"error":{"code":"NOT_FOUND","message":"요청한 URL이 없습니다"}}), 404

    @app.errorhandler(MethodNotAllowed)
    def _method(e):
        return jsonify({"error":{"code":"METHOD_NOT_ALLOWED","message":"HTTP 메서드 오류"}}), 405

    @app.errorhandler(HTTPException)
    def _httpe(e):
        return jsonify({"error":{"code":e.name.upper().replace(' ','_'),"message":e.description}}), e.code

    @app.errorhandler(Exception)
    def _fallback(e):
        return jsonify({"error":{"code":"SERVER_ERROR","message":str(e)}}), 500
