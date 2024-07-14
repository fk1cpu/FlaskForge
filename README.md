# FlaskForge

FlaskForge is a command-line tool to generate a skeleton for a Flask web application. It sets up the directory structure, creates virtual environments, installs dependencies, generates boilerplate code, and configures CI/CD pipelines.

## Features

- Creates Flask project structure with templates and static directories.
- Sets up virtual environments.
- Installs specified dependencies.
- Generates boilerplate code for blueprints, routes, forms, and models.
- Configures Docker with `Dockerfile` and `docker-compose.yml`.
- Sets up CI/CD pipelines with GitHub Actions.
- Initializes the database with Flask-Migrate.
- Supports post-generation hooks.

## Requirements

- Python 3.6 or higher
- Git

## Installation

Clone the repository:

```bash
git clone https://github.com/fk1cpu/FlaskForge.git
cd FlaskForge
```
Install the necessary dependencies:

```bash
pip install -r requirements.txt
```
## Usage

To generate a new Flask project, run:

```bash
python flaskforge.py <project_name> [options]
```

## Options

* `project_name`: The name of the project.
* `-bp, --blueprints`: Comma-separated list of blueprints (default: `''`).
* `-D, --dependencies`: Comma-separated list of dependencies (default: `Flask,Flask-CKEditor,Flask-Mail,Flask-Login,Flask-Migrate,Flask-SQLAlchemy,Flask-WTF,email_validator,python-dotenv`).
* `-v, --verbosity`: Logging verbosity level (default: `0`).
    * `0`: CRITICAL
    * `1`: ERROR
    * `2`: WARNING
    * `3`: INFO
    * `4`: DEBUG
* `-tl, --template`: Project template (`rest_api`, `full_stack`, default: `rest_api`).
* `-c, --config`: Path to custom configuration file (default: `''`).
* `-hks, --post_gen_hooks`: Comma-separated list of post-generation hooks (default: `''`).
* `-env, --venv-dir`: Directory for the virtual environment.

## Example

Generate a new project named `my_awesome_flask_app` with blueprints `auth` and `blog`:

```bash
python flaskforge.py my_awesome_flask_app -bp auth,blog -v 3
```
## Project Structure

The generated project will have the following structure:

```bash
my_awesome_flask_app/
│
├── .fforge/                  # Virtual environment directory
├── .github/
│   └── workflows/
│       └── python-app.yml    # GitHub Actions CI/CD pipeline
├── my_awesome_flask_app/
│   ├── __init__.py           # Flask app factory
│   ├── models.py             # Database models
│   ├── templates/            # Jinja2 templates
│   ├── static/               # Static files (CSS, JavaScript, images)
│   ├── auth/                 # Blueprint for authentication
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── forms.py
│   │   └── templates/
│   │       └── auth_home.html
│   └── blog/                 # Blueprint for blog
│       ├── __init__.py
│       ├── routes.py
│       ├── forms.py
│       └── templates/
│           └── blog_home.html
├── Dockerfile                # Docker configuration
├── docker-compose.yml        # Docker Compose configuration
└── requirements.txt          # Project dependencies
```

## Customization

### Templates

You can customize the project templates by modifying the files in the `templates/` directory. The default templates include:

- `rest_api`: Basic REST API setup
- `full_stack`: Full-stack web application setup

## Post-Generation Hooks

You can specify post-generation hooks to run custom scripts after the project is generated. Provide a comma-separated list of commands using the `-hks` option. These commands will be executed in the context of the created project's virtual environment.

#### Example Post-Generation Hooks
1. Run a script to set up environment variables:
    * Create a script `setup_env.sh` in the root of your project:

    ```bash
    #!/bin/bash
    echo "Setting up environment variables..."
    export FLASK_APP=run.py
    export FLASK_ENV=development
    echo "All Done! :)"
    ```
    * Make the script executable:

    ```bash
    chmod +x setup_env.sh
    ```
    * Use the script as a post-generation hook:

    ```bash
    python flaskforge.py my_awesome_flask_app -bp auth,blog -hks "./setup_env.sh" -v 3
    ```
2. Run database migrations automatically:
    * Use Flask-Migrate commands as hooks:

    ```bash
    python flaskforge.py my_awesome_flask_app -bp auth,blog -hks "flask db init,flask db migrate,flask db upgrade" -v 3
    ```
## Configuration File
You can specify a custom configuration file with the `-c` option. The configuration file should be a JSON file with the following structure:

```json
{
  "project_name": "my_awesome_flask_app",
  "blueprints": ["auth", "blog"],
  "dependencies": ["Flask", "Flask-SQLAlchemy"],
  "verbosity": 3,
  "template": "full_stack",
  "config_path": "",
  "post_gen_hooks": ["echo 'Post-gen hook 1'", "echo 'Post-gen hook 2'"],
  "venv_dir": ".fforge"
}
```
## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE.md) file for details.

## Acknowledgements
- [Flask]()
- [Jinja2]()
- [Flask-SQLAlchemy]()
- [Flask-Migrate]()
