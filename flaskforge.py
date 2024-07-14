import os
import platform
import subprocess
import argparse
import logging
from jinja2 import Template

class FlaskForge:
    def __init__(self, config):
        self.project_name = config.get('project_name')
        self.blueprints = config.get('blueprints', [])
        self.dependencies = config.get('dependencies', [])
        self.verbosity = config.get('verbosity', 0)
        self.template = config.get('template', 'rest_api')
        self.config_path = config.get('config_path', '')
        self.post_gen_hooks = config.get('post_gen_hooks', '')
        self.project_path = os.path.join(os.getcwd(), self.project_name)
        self.venv_dir = os.path.join(self.project_path, '.fforge') or os.path.join(self.project_path, config.get('venv_dir'))
        self.setup_logging()

    def setup_logging(self):
        """Sets up the logging configuration based on verbosity."""
        log_levels = {
            0: logging.CRITICAL,
            1: logging.ERROR,
            2: logging.WARNING,
            3: logging.INFO,
            4: logging.DEBUG
        }
        logging.basicConfig(level=log_levels.get(self.verbosity, logging.INFO))
        self.logger = logging.getLogger('FlaskForge')

    def create_directories(self):
        """Creates the necessary directories for the project."""
        try:
            os.makedirs(self.project_path, exist_ok=True)
            os.makedirs(os.path.join(self.project_path, self.project_name), exist_ok=True)
            os.makedirs(os.path.join(self.project_path, self.project_name, 'templates'), exist_ok=True)
            os.makedirs(os.path.join(self.project_path, self.project_name, 'static'), exist_ok=True)
            self.logger.info(f"Directories created for project {self.project_name}")
        except OSError as e:
            self.logger.error(f"Error creating directories: {e}")
    
    def create_virtualenv(self):
        """Creates a virtual environment for the project."""
        try:
            subprocess.run(['python', '-m', 'venv', self.venv_dir], check=True)
            self.logger.info("Virtual environment created")
            self.activate_command = os.path.join(self.venv_dir, 'Scripts', 'activate') if platform.system() == 'Windows' else f'source {os.path.join(self.venv_dir, "bin", "activate")}'
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error creating virtual environment: {e}")

    def install_dependencies(self):
        """Installs the project dependencies in the virtual environment."""
        if self.dependencies:
            try:
                subprocess.run([self.activate_command + ' && pip install ' + ' '.join(self.dependencies)], shell=True, check=True)
                self.logger.info("Dependencies installed")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Error installing dependencies: {e}")

    def create_base_files(self):
        """Creates the base files for the project from templates."""
        template_path = os.path.join(os.path.dirname(__file__), 'templates', self.template)
        for root, _, files in os.walk(template_path):
            for file in files:
                relative_path = os.path.relpath(os.path.join(root, file), template_path)
                dest_path = os.path.join(self.project_path, relative_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(os.path.join(root, file), 'r') as f_src, open(dest_path, 'w') as f_dest:
                    template_content = Template(f_src.read())
                    f_dest.write(template_content.render(project_name=self.project_name))
        self.logger.info("Base files created from template")

    def create_blueprints(self):
        """Creates blueprint directories and files."""
        for bp in self.blueprints:
            bp = bp.strip()
            if bp:
                bp_dir = os.path.join(self.project_path, self.project_name, bp)
                os.makedirs(bp_dir, exist_ok=True)
                os.makedirs(os.path.join(bp_dir, 'templates'), exist_ok=True)
                os.makedirs(os.path.join(bp_dir, 'static'), exist_ok=True)
                self.create_blueprint_files(bp, bp_dir)
        self.logger.info("Blueprints created")

    def create_blueprint_files(self, bp, bp_dir):
        """Creates files for a blueprint."""
        with open(os.path.join(bp_dir, 'routes.py'), 'w') as f:
            f.write(f"""from flask import Blueprint, render_template
{bp} = Blueprint('{bp}', __name__, template_folder='templates', static_folder='static')

@{bp}.route('/{bp}_home')
def {bp}_home():
    return render_template('{bp}/{bp}_home.html')
""")
        with open(os.path.join(bp_dir, '__init__.py'), 'w') as f:
            f.write(f"from .routes import {bp}")
        with open(os.path.join(bp_dir, 'forms.py'), 'w') as f:
            f.write("""from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
""")
        with open(os.path.join(bp_dir, 'templates', f'{bp}_home.html'), 'w') as f:
            f.write(f"""{{% extends "base.html" %}}
{{% block content %}}
<h1>Welcome to the {bp.capitalize()} Home Page</h1>
{{% endblock %}}
""")

    def create_init_py(self):
        """Creates the __init__.py file for the Flask app."""
        with open(os.path.join(self.project_path, self.project_name, '__init__.py'), 'w') as f:
            f.write(f"""from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')

    db.init_app(app)
    migrate.init_app(app, db)

    from . import routes
    app.register_blueprint(routes.main_bp)

    return app
""")
        self.logger.info("Created __init__.py for Flask app")

    def create_models_py(self):
        """Creates the models.py file for the Flask app."""
        with open(os.path.join(self.project_path, self.project_name, 'models.py'), 'w') as f:
            f.write("""from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return f'<User {self.username}>'
""")
        self.logger.info("Created models.py")

    def create_docker_files(self):
        """Creates Dockerfile and docker-compose.yml for the project."""
        with open(os.path.join(self.project_path, 'Dockerfile'), 'w') as f:
            f.write("""FROM python:3.8-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["flask", "run", "--host=0.0.0.0"]
""")
        with open(os.path.join(self.project_path, 'docker-compose.yml'), 'w') as f:
            f.write("""version: '3'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - .:/app
    environment:
      FLASK_ENV: development
      FLASK_APP: main.py
""")
        self.logger.info("Created Docker files")

    def create_ci_cd_files(self):
        """Creates CI/CD configuration files for GitHub Actions."""
        github_dir = os.path.join(self.project_path, '.github', 'workflows')
        os.makedirs(github_dir, exist_ok=True)
        with open(os.path.join(github_dir, 'python-app.yml'), 'w') as f:
            f.write("""name: Python application

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.6, 3.7, 3.8, 3.9]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Test with pytest
      run: |
        pytest
""")
        self.logger.info("Created CI/CD files")

    def initialize_database(self):
        """Initializes the database using Flask-Migrate."""
        try:
            subprocess.run([self.activate_command + ' && flask db init'], shell=True, check=True, cwd=self.project_path)
            subprocess.run([self.activate_command + ' && flask db migrate'], shell=True, check=True, cwd=self.project_path)
            subprocess.run([self.activate_command + ' && flask db upgrade'], shell=True, check=True, cwd=self.project_path)
            self.logger.info("Initialized database")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error initializing database: {e}")

    def run_post_gen_hooks(self):
        """Runs post-generation hooks if any are specified."""
        if self.post_gen_hooks:
            hooks = self.post_gen_hooks.split(',')
            for hook in hooks:
                try:
                    subprocess.run(self.activate_command + ' && ' + hook.strip(), shell=True, check=True, cwd=self.project_path)
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Error running post-generation hook '{hook}': {e}")
            self.logger.info("Post-generation hooks executed")

    def run(self):
        """Runs the entire project generation process."""
        self.create_directories()
        self.create_virtualenv()
        self.install_dependencies()
        self.create_base_files()
        self.create_blueprints()
        self.create_init_py()
        self.create_models_py()
        self.create_docker_files()
        self.create_ci_cd_files()
        self.initialize_database()
        self.run_post_gen_hooks()
        self.logger.info(f"Flask project {self.project_name} created successfully")

def main():
    parser = argparse.ArgumentParser(description='Generate a Flask project skeleton.')
    parser.add_argument('project_name', type=str, help='The name of the project.')
    parser.add_argument('-bp', '--blueprints', type=str, help='Comma-separated list of blueprints.', default='')
    parser.add_argument('-D', '--dependencies', type=str, help='Comma-separated list of dependencies.', default='Flask,Flask-CKEditor,Flask-Mail,Flask-Login,Flask-Migrate,Flask-SQLAlchemy,Flask-WTF,email_validator,python-dotenv')
    parser.add_argument('-v', '--verbosity', type=int, default=0, help='Logging verbosity level: 0 (CRITICAL), 1 (ERROR), 2 (WARNING), 3 (INFO), 4 (DEBUG)')
    parser.add_argument('-tl', '--template', type=str, help='Project template (rest_api, full_stack).', default='rest_api')
    parser.add_argument('-c', '--config', type=str, help='Path to custom configuration file.', default='')
    parser.add_argument('-hks', '--post_gen_hooks', type=str, help='Comma-separated list of post-generation hooks.', default='')
    parser.add_argument('-env', '--venv-dir', help='Directory for the virtual environment')
    
    args = parser.parse_args()
    config = {
        'project_name': args.project_name,
        'blueprints': args.blueprints.split(',') if args.blueprints else [],
        'dependencies': args.dependencies.split(',') if args.dependencies else [],
        'verbosity': args.verbosity,
        'template': args.template,
        'config_path': args.config,
        'post_gen_hooks': args.post_gen_hooks,
        'venv_dir': args.venv_dir
    }

    forge = FlaskForge(config)
    forge.run()

if __name__ == '__main__':
    main()

