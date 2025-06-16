---
name: Pull Request Template
about: Template for creating pull requests
title: ''
labels: ''
assignees: ''

---

## 📋 Pull Request Description

### 🎯 What does this PR do?
<!-- Briefly describe what changes this PR introduces -->

### 🔗 Related Issues
<!-- Link any related issues using: Fixes #123, Closes #456, Related to #789 -->

### 🚀 Type of Change
<!-- Mark the relevant option with an "x" -->
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Refactoring (no functional changes, no api changes)
- [ ] ⚡ Performance improvement
- [ ] 🧪 Test improvements
- [ ] 🎨 Code style/formatting changes

## 🧪 Testing

### ✅ Test Coverage
<!-- Describe the tests you ran to verify your changes -->
- [ ] Unit tests pass locally
- [ ] Integration tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing completed

### 🔍 Test Instructions
<!-- Provide step-by-step instructions for testing this PR -->
1. 
2. 
3. 

## 📸 Screenshots/Logs
<!-- If applicable, add screenshots or logs to help explain your changes -->

## 🏁 Checklist

### Code Quality
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] My changes generate no new warnings
- [ ] I have added type hints where appropriate

### Testing
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

### Documentation
- [ ] I have made corresponding changes to the documentation
- [ ] I have updated the CHANGELOG.md file (if applicable)
- [ ] I have updated docstrings for any modified functions/classes

### Dependencies
- [ ] I have updated requirements.txt if new dependencies were added
- [ ] I have verified that all dependencies are compatible

## 🤖 Automated Checks Status

The following automated checks will run when this PR is created:

- **🔍 Pylance/Pyright**: Static type checking and code analysis
- **🧪 Unit Tests**: Comprehensive test suite across Python 3.9-3.12
- **🎨 Code Formatting**: Black, isort, and flake8 checks
- **🔒 Security Scan**: Safety and bandit security analysis
- **📦 Build Validation**: Package build and distribution checks

## 📝 Additional Notes
<!-- Add any additional notes, concerns, or considerations here -->

## 🔄 Merge Strategy
<!-- Indicate preferred merge strategy -->
- [ ] Merge commit
- [ ] Squash and merge (recommended for feature PRs)
- [ ] Rebase and merge (recommended for small fixes)

---

**By submitting this pull request, I confirm that:**
- [ ] I have read and followed the project's contributing guidelines
- [ ] My code is properly tested and documented
- [ ] I understand that this code will be reviewed before merging
