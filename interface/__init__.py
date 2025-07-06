from .linebot import linebot_bp

def register_blueprints(app):

    app.register_blueprint(linebot_bp)
