# Contributing Guide

> [!IMPORTANT]
> **EXPERIMENTAL PROJECT** - Focus on fixing broken features, not adding new ones. Use Claude Code to help navigate the codebase.

Guidelines for contributing to the comfy2c4d project.

## Development Setup

1. Fork and clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
3. Install development dependencies:
   ```bash
   pip install pytest black flake8 mypy
   ```

## Code Standards

### Style Guide
- Python 3.10+ features allowed
- Follow PEP 8 with 100 char line limit
- Use type hints for function signatures
- Format with `black`

### Import Convention
```python
# Always use src prefix
from src.core.workflow_manager import WorkflowManager
from src.ui.widgets import DynamicNodeWidget

# Not this
from core.workflow_manager import WorkflowManager
```

### Naming Conventions
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

## Architecture Principles

### 1. Dynamic Over Static
- Avoid hardcoding UI elements
- Let workflows drive the interface
- Support any ComfyUI node automatically

### 2. Async First
- Use `async/await` for I/O operations
- Don't block the UI thread
- Leverage `qasync` for Qt integration

### 3. State Management
- Single source of truth in config files
- Cross-tab persistence via unified state
- Explicit save/load operations

## Making Changes

### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Development Workflow
- Write code following standards
- Add/update documentation
- Test thoroughly
- Update CLAUDE.md if adding patterns

### 3. Testing
```python
# Run tests
pytest tests/

# Check code style
black --check src/
flake8 src/

# Type checking
mypy src/
```

### 4. Commit Messages
```
feat: Add new feature
fix: Fix specific issue
docs: Update documentation
refactor: Restructure code
test: Add tests
style: Format code
```

## Common Tasks

### Adding New Node Support
1. No code needed! Dynamic UI handles it
2. Test with workflow containing the node
3. Add to documentation if special handling

### Improving Performance
1. Profile first: `python -m cProfile main.py`
2. Focus on UI responsiveness
3. Use caching and lazy loading
4. Document optimizations

### Fixing Bugs
1. Check issues tracker
2. Reproduce consistently
3. Add test case
4. Fix with minimal changes
5. Update relevant docs

## Documentation

### When to Update Docs
- New features or patterns
- Breaking changes
- Complex bug fixes
- Performance improvements

### Documentation Files
- `CLAUDE.md`: AI development patterns
- `ARCHITECTURE.md`: System design changes
- `CONFIG.md`: New configuration options
- `PARAMETERS.md`: UI generation rules

## Debugging Tips

### Enable Debug Logging
```bash
export COMFY_C4D_DEBUG=1
python main.py
```

### Common Issues
- **Import errors**: Check virtual environment
- **Event loop errors**: Don't mix asyncio.run()
- **UI not updating**: Use QTimer.singleShot()
- **Memory leaks**: Clear caches on tab switch

## Pull Request Process

1. **Before Submitting**
   - Code follows standards
   - Tests pass
   - Documentation updated
   - No hardcoded values

2. **PR Description**
   - Describe changes clearly
   - Link related issues
   - Include screenshots for UI changes
   - List testing performed

3. **Review Process**
   - Address feedback promptly
   - Keep changes focused
   - Update branch with main

## Security

- Never commit credentials
- Sanitize file paths
- Validate user input
- No external network calls without user consent

## Questions?

- Check existing issues first
- Ask in discussions
- Review ARCHITECTURE.md
- Study similar code patterns

Remember: The goal is maintainable, extensible code that works with any ComfyUI workflow!