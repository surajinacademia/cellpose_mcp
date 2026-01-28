# Contributing to cellpose-mcp

Thank you for your interest in contributing to cellpose-mcp! This document provides guidelines and information for contributors.

## 🚀 Quick Start for Contributors

### Development Setup

1. **Fork and clone the repository**
 ```bash
 git clone https://github.com/YOUR-USERNAME/cellpose_mcp.git
 cd cellpose_mcp
 ```

2. **Set up development environment**
 ```bash
 # Activate your conda environment
 conda activate image_analysis  # or Cellpose_mcp

 # Install in development mode
 pip install -e ".[test,dev]"
 ```

3. **Install pre-commit hooks**
 ```bash
 pip install pre-commit
 pre-commit install
 ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/cellpose_mcp --cov-report=html

# Run only fast tests
pytest -m "not slow"
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Format code
ruff format src/ tests/

# Lint code
ruff check src/ tests/ --fix

# Type checking
mypy src/cellpose_mcp --ignore-missing-imports

# Security scanning
bandit -r src/
```

## 🎯 How to Contribute

### Types of Contributions

We welcome the following types of contributions:

- **🐛 Bug fixes** - Fix issues in existing functionality
- **✨ New features** - Add new MCP tools or Cellpose integrations
- **📚 Documentation** - Improve README, add examples, API docs
- **🧪 Tests** - Improve test coverage or add new test cases
- **🔒 Security** - Security improvements and vulnerability fixes
- **🏗️ Infrastructure** - CI/CD, build system, tooling improvements

### Before You Start

1. **Check existing issues** - Look for related issues or feature requests
2. **Discuss major changes** - Open an issue to discuss large changes
3. **Follow security guidelines** - Be especially careful with file I/O and model loading

### Development Workflow

1. **Create a feature branch**
 ```bash
 git checkout -b feature/your-feature-name
 # or
 git checkout -b fix/your-bug-fix
 ```

2. **Make your changes**
 - Follow existing code style and patterns
 - Add tests for new functionality
 - Update documentation as needed
 - Consider security implications

3. **Test your changes**
 ```bash
 # Run the full test suite
 pytest

 # Test manually with cellpose-mcp
 python -m cellpose_mcp --help
 ```

4. **Commit your changes**
 ```bash
 git add .
 git commit -m "feat: add new MCP tool for batch processing"
 # Follow conventional commit format
 ```

5. **Push and create PR**
 ```bash
 git push origin feature/your-feature-name
 # Then create a Pull Request on GitHub
 ```

## 📋 Pull Request Guidelines

### PR Checklist

- [ ] **Tests pass** - All existing tests continue to pass
- [ ] **New tests added** - For new features or bug fixes
- [ ] **Documentation updated** - README, docstrings, examples
- [ ] **Security reviewed** - Especially for file I/O and model operations
- [ ] **Type hints added** - For new functions and methods
- [ ] **Conventional commits** - Use conventional commit messages

### PR Template

When creating a PR, please include:

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Security improvement
- [ ] Other (please describe)

## Testing
- [ ] Tests pass locally
- [ ] Added new tests
- [ ] Manually tested with cellpose-mcp

## Security Considerations
(If applicable - especially for file I/O or model loading changes)

## Checklist
- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## 🔍 Code Style Guidelines

### General Principles

- **Readability** - Code should be easy to read and understand
- **Security** - Always consider security implications
- **Async/await** - Use async/await consistently for MCP tools
- **Error handling** - Provide clear error messages and proper exception handling
- **Documentation** - Document all public functions and complex logic

### Specific Guidelines

```python
# ✅ Good: Clear function signature with type hints
async def segment_cells_2d(
    image_path: str,
    model_type: str = "cyto2",
    diameter: float = 0.0
) -> Dict[str, Any]:
    """Segment cells in a 2D image using Cellpose.

    Parameters
    ----------
    image_path : str
        Path to an image file readable by imageio
    model_type : str, optional
        Cellpose model type (default: "cyto2")
    diameter : float, optional
        Cell diameter in pixels (0 for auto-detect)

    Returns
    -------
    Dict[str, Any]
        Dictionary with cells_detected, output_path, diameter, mask_shape
    """

# ❌ Bad: No type hints, unclear parameters
def segment_cells_2d(image_path, model_type=None, diameter=0):
    # Does stuff
    return result
```

### Naming Conventions

- **Functions**: `snake_case` (e.g., `segment_cells_2d`, `train_model`)
- **Variables**: `snake_case` (e.g., `image_path`, `model_type`)
- **Constants**: `UPPER_CASE` (e.g., `DEFAULT_MODEL_TYPE`)
- **Classes**: `PascalCase` (e.g., `CellposeModel`)

## 🧪 Testing Guidelines

### Test Structure

```python
"""
tests/
├── test_tools.py # Main tool functionality tests
├── test_integration.py # Integration tests
└── test_edge_cases.py # Edge cases and error conditions
"""
```

### Writing Tests

```python
import pytest
from cellpose_mcp.tools import segment_cells_2d

@pytest.mark.asyncio
async def test_segment_cells_2d_success():
    """Test successful cell segmentation."""
    # Arrange
    test_image_path = "test_data/sample.png"

    # Act
    result = await segment_cells_2d(test_image_path, model_type="cyto2")

    # Assert
    assert result["cells_detected"] > 0
    assert "output_path" in result
    assert "diameter" in result
```

### Test Markers

- `@pytest.mark.asyncio` - Async tests (most MCP tools)
- `@pytest.mark.slow` - Slow tests that can be skipped for quick runs
- `@pytest.mark.integration` - Integration tests

## 🔒 Security Considerations

### High-Risk Areas

When contributing changes to these areas, extra security review is required:

- File I/O operations
- Model loading and execution
- Any new system access features

### Security Review Process

1. **Self-review** - Consider all security implications
2. **Document risks** - Clearly document any security considerations
3. **Minimal permissions** - Use least privilege principle
4. **Input validation** - Validate all inputs thoroughly
5. **Error handling** - Don't leak sensitive information in errors

## 📞 Getting Help

### Community Support

- **GitHub Issues** - For bug reports and feature requests
- **GitHub Discussions** - For questions and general discussion
- **Security Issues** - Follow SECURITY.md for vulnerability reporting

### Development Questions

If you have questions about:
- **Architecture** - How the MCP server works
- **Testing** - How to write or run tests
- **Cellpose Integration** - How Cellpose APIs work
- **MCP Protocol** - Model Context Protocol details

Feel free to open a GitHub Discussion or comment on existing issues.

## 🎉 Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Special mentions for security improvements

Thank you for helping make cellpose-mcp better and more secure! 🚀
