from app import app, db
from flask_migrate import Migrate

migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        if db.engine.url.drivername == 'sqlite':
            migrate.init_app(app, db, render_as_batch=True)
        else:
            migrate.init_app(app, db)