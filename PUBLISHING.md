# Publishing to PyPI

This package uses GitHub Actions with Trusted Publisher for secure, automated publishing to PyPI.

## Initial Setup (One-time)

### 1. Configure Trusted Publisher on PyPI

1. Go to https://pypi.org/manage/account/publishing/
2. Click "Add a new pending publisher"
3. Fill in the form:
   - **PyPI Project Name**: `mawo-core`
   - **Owner**: `mawo-ru`
   - **Repository name**: `mawo-core`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
4. Click "Add"

### 2. Configure Trusted Publisher on TestPyPI (Optional, for testing)

1. Go to https://test.pypi.org/manage/account/publishing/
2. Click "Add a new pending publisher"
3. Fill in the form:
   - **PyPI Project Name**: `mawo-core`
   - **Owner**: `mawo-ru`
   - **Repository name**: `mawo-core`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `testpypi`
4. Click "Add"

### 3. Create GitHub Environments

1. Go to https://github.com/mawo-ru/mawo-core/settings/environments
2. Create two environments:
   - **pypi** (for production releases)
   - **testpypi** (for testing)
3. (Optional) Add protection rules:
   - Required reviewers
   - Wait timer
   - Deployment branches (only from `main`)

## Publishing a New Version

### Method 1: Create a GitHub Release (Recommended)

1. Update version in `pyproject.toml`
2. Commit and push changes
3. Create a new release on GitHub:
   - Go to https://github.com/mawo-ru/mawo-core/releases/new
   - Create a new tag (e.g., `v0.1.0`)
   - Fill in release title and description
   - Click "Publish release"
4. GitHub Actions will automatically:
   - Build the package
   - Publish to TestPyPI
   - Publish to PyPI

### Method 2: Manual Trigger

1. Go to https://github.com/mawo-ru/mawo-core/actions/workflows/publish.yml
2. Click "Run workflow"
3. Select branch and click "Run workflow"

## Verification

After publishing, verify the package:

### On PyPI
```bash
pip install mawo-core
python -c "from mawo import Russian; print(Russian())"
```

### On TestPyPI
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mawo-core
python -c "from mawo import Russian; print(Russian())"
```

## Local Testing

Test the build process locally before pushing:

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build the package
python -m build

# Check the package
twine check dist/*

# (Optional) Upload to TestPyPI manually
twine upload --repository testpypi dist/*
```

## Security Benefits of Trusted Publisher

✅ **No API tokens needed** - Uses OIDC for authentication  
✅ **Automatic credential rotation** - Temporary credentials per publish  
✅ **Audit trail** - Clear connection between GitHub releases and PyPI uploads  
✅ **Reduced attack surface** - No long-lived secrets in GitHub  

## Troubleshooting

### "Trusted publisher configuration does not match"
- Verify the repository owner, name, workflow, and environment match exactly
- Check that the workflow is running from the correct branch

### "Environment protection rules not met"
- Check environment protection settings in GitHub
- Ensure required reviewers have approved the deployment

### "Permission denied"
- Verify `id-token: write` permission is set in the workflow
- Check that the environment is correctly configured

## Links

- PyPI Project: https://pypi.org/project/mawo-core/
- TestPyPI Project: https://test.pypi.org/project/mawo-core/
- GitHub Actions: https://github.com/mawo-ru/mawo-core/actions
- PyPI Trusted Publishers: https://docs.pypi.org/trusted-publishers/
