# Contributing to AdminHunter

Thank you for considering contributing! This project thrives on community involvement.

## How to Contribute

1. **Fork** the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes following the existing code style
4. Add or update tests in the `tests/` directory
5. Run the test suite locally before committing:
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   pytest -q
   ```
6. Push and open a Pull Request

## Guidelines

- **Keep it focused**: one PR = one logical change
- **Security first**: never commit real credentials or target URLs
- **Documentation**: update `README.md` when changing CLI options or behavior
- **Tests**: new detection patterns must include unit tests

## Development Setup

- Python 3.11+ required
- The test suite uses `pytest` with an in-process test server (no network needed)

## Reporting Issues

Use the issue tracker for bugs and feature requests. For security vulnerabilities, follow the process in [SECURITY.md](SECURITY.md).
