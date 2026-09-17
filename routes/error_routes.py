from flask import Blueprint, render_template, jsonify, request

error_bp = Blueprint('errors', __name__)

@error_bp.app_errorhandler(400)
def bad_request_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'code': 400, 'message': 'Bad Request'}), 400
    return render_template('errors/404.html', error_title='400 - Bad Request', error_msg='The request could not be processed due to invalid parameters.'), 400

@error_bp.app_errorhandler(401)
def unauthorized_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'code': 401, 'message': 'Unauthorized'}), 401
    return render_template('errors/404.html', error_title='401 - Authentication Required', error_msg='Please log in to access this academic workload module.'), 401

@error_bp.app_errorhandler(403)
def forbidden_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'code': 403, 'message': 'Forbidden'}), 403
    return render_template('errors/404.html', error_title='403 - Access Denied', error_msg='You do not have permission to access another student\'s data.'), 403

@error_bp.app_errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'code': 404, 'message': 'Resource Not Found'}), 404
    return render_template('errors/404.html', error_title='404 - Page Not Found', error_msg='The requested page or record could not be found.'), 404

@error_bp.app_errorhandler(500)
def internal_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'code': 500, 'message': 'Internal Server Error'}), 500
    return render_template('errors/500.html'), 500
