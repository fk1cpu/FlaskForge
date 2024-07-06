import os
import platform
import subprocess
import argparse
import logging
from jinja2 import Template

class FlaskForge:
    def __init__(self, project_name, blueprints, dependencies, verbosity, template, config_path, post_gen_hooks, venv_dir):
        self.project_name = project_name
        self.blueprints = blueprints
        self.dependencies = dependencies
        self.verbosity = verbosity
        self.template = template
        self.config_path = config_path
        self.post_gen_hooks = post_gen_hooks
        self.project_path = os.path.join(os.getcwd(), project_name)
        self.venv_dir =  os.path.join(self.project_path, '.fforge') or os.path.join(self.project_path, venv_dir)
        self.setup_logging()

    def setup_logging(self):
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
        os.makedirs(self.project_path, exist_ok=True)
        os.makedirs(os.path.join(self.project_path, self.project_name), exist_ok=True)
        os.makedirs(os.path.join(self.project_path, self.project_name, 'templates'), exist_ok=True)
        os.makedirs(os.path.join(self.project_path, self.project_name, 'static'), exist_ok=True)
        self.logger.info(f"Directories created for project {self.project_name}")

    def create_virtualenv(self):
        subprocess.run(['python', '-m', 'venv', self.venv_dir])
        self.logger.info("Virtual environment created")
        if platform.system() == 'Windows':
            self.activate_command = os.path.join(self.venv_dir, 'Scripts', 'activate')
        else:
            self.activate_command = f'source {os.path.join(self.venv_dir, "bin", "activate")}'

    def create_base_files(self):
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
        subprocess.run([self.activate_command + ' && flask db init'], shell=True, cwd=self.project_path)
        subprocess.run([self.activate_command + ' && flask db migrate'], shell=True, cwd=self.project_path)
        subprocess.run([self.activate_command + ' && flask db upgrade'], shell=True, cwd=self.project_path)
        self.logger.info("Initialized database")

    def run_post_gen_hooks(self):
        if self.post_gen_hooks:
            hooks = self.post_gen_hooks.split(',')
            for hook in hooks:
                subprocess.run(self.activate_command + ' && ' + hook.strip(), shell=True, cwd=self.project_path)
            self.logger.info("Post-generation hooks executed")

    def run(self):
        self.create_directories()
        self.create_virtualenv()
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
    parser.add_argument('-hks', '--post_gen_hooks', type=str, help='Path to post-generation hooks script.', default='')
    parser.add_argument('-env', '--venv-dir', help='Directory for the virtual environment')
    
    args = parser.parse_args()
    blueprints = args.blueprints.split(',') if args.blueprints else []
    dependencies = args.dependencies.split(',') if args.dependencies else []

    forge = FlaskForge(args.project_name, blueprints, dependencies, args.verbosity, args.template, args.config, args.post_gen_hooks, args.venv_dir)
    forge.run()

if __name__ == '__main__':
    main()
