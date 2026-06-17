# CHANGELOG

<!--next-version-placeholder-->

## v0.2.3 (2026-06-10)

### Bug Fixes
* **antspynet:** recover corrupt brain extraction weights

### Build
* **deps:** bump actions/setup-python from 5 to 6
* **deps:** bump actions/checkout from 4 to 5
* **deps:** bump astral-sh/setup-uv from 5 to 6

## v0.2.2 (2025-02-15)

### Features
* **pre-commit:** bump ruff to v0.9.6
* **env:** add sample .env file
* **docker:** add template to the production image

### Bug Fixes
* **tests:** use explicit variable to skip tests
* **docker:** add missing network

### CI/CD
* **docker:** prefix image version

### Build
* **tests:** disable tests for CI - arm64 exceeds 6 hour job execution limit on GHA

### Refactoring
* **docker:** generalize service name - remove deprecated version attribute

### Style
* **pre-commit:** consistent annotations

## v0.2.1 (2024-12-29)

### Bug Fixes
* **ci:** correct ordering of tag extraction job
* **ci:** replace deprecated image tag

### Build
* **ci:** truncate commit tag
* **ci:** update released to published for docker image publishing
* **ci:** test docker builds for amd64 for push events
* **ci:** update push trigger to tagged versions
* **ci:** add manual and release triggers for docker images
* **deps:** bump astral-sh/setup-uv from 4 to 5

### Style
* **ci:** rename workflow files to be consistent

## v0.2.0 (2024-12-28)

### Features
* **dash:** add locally hosted assets for font-awesome
* **make:** update helper tasks
* **gha:** add code quality
* **docker:** add Dockerfiles for upstream images (antspyx, antspynet)
* **pyproject:** better versioning
* **version:** add dynamic version tag to webapp
* **python:** create an installable pip package
* **debug:** add debug server function
* **build:** bump antspy to v0.5.4, antspynet to 58b19c9

### Bug Fixes
* **Dockefile:** remove redundant COPY
* **typing:** assert not None
* **typing:** resolve colliding functions
* **pyupgrade:** use f-strings
* **typing:** ignore import issues
* **pre-commit:** pyupgrade
* **pyproject:** add complete list of dependencies
* **ci:** remove duplicate meta identifier
* **coverage:** add missing tox.ini
* **gha:** remove dependencies on base-image

### CI/CD
* **docker:** test amd64 only for docker builds (arm64 exceeds 6hr limit)
* **pre-commit:** add config

### Build
* deprecate requirements.txt
* **micromamba:** add unpinned, pinned and conda-lock envs
* **pixi:** add pixi build config + lock + envrc

### Refactoring
* **docker:** update gha ci/cd - deprecate base image
* **docker:** deprecate base image - rebase on micromamba from conda
* **web:** migrate config for demo to web/
* **utils:** linting, split and organize imports
* **ruff:** linting, formatting, organize imports for processing script
* **ruff:** linting, formatting, organize imports - modularize logging
* **layout:** migrate layout to a module

### Style
* **docker:** consistent formatting and resolve FromAsCasing warning
* **tox/lint:** remove assignment to unused variable
* **ruff:** formatting
* **logging:** consistent usage of lowercase
* **ruff:** organize imports

### Tests
* **data:** add test inputs and their provenance
* **data:** add ground-truth data
* **textures:** add units for tests for all image processing modules

### Chores
* cleanup deprecated files
* **gha:** bump build-push-action to v6

## v0.1.0 (2023-08-18)

### Features
* Initial Dash web application for MRI texture map generation
* T1 and T2/FLAIR input support with automatic file detection
* Brain extraction and tissue segmentation pipeline
* Bias correction and registration workflows
* QC report generation with PDF output
* Multi-arch Docker builds (amd64, arm64)
* CI/CD with GitHub Actions for Docker image publishing
* MkDocs documentation site deployment
* Dependabot configuration for GHA version updates

### Bug Fixes
* Correct bug that could induce a bad GM or WM intensity pick estimation
* Bias correction: adjust intensity truncation for t1-weighted images
* Fix registration parameter to use Global Correlation for T1-weighted images
* Fix keras import issues with frozen antspynet version
* Fix docker CI/CD tag handling

### Build
* Heroku deployment support (Procfile, runtime.txt)
* Docker Compose configuration for local development
* Makefile for build automation
* Requirements.txt for dependency management

### Documentation
* README with usage instructions and demo links
* Example images and documentation assets
* Issue templates for bug reports
