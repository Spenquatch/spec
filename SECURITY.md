# Security Policy

## Supported Versions

We actively maintain security updates for the following versions:

| Version | Supported          | Notes                    |
| ------- | ------------------ | ------------------------ |
| 0.1.x   | :white_check_mark: | Current stable release   |
| main    | :white_check_mark: | Development branch       |
| < 0.1.0 | :x:                | Pre-release versions     |

**Security Update Policy:**
- **Critical vulnerabilities**: Patched within 24-48 hours
- **High severity**: Patched within 1 week
- **Medium/Low severity**: Included in next regular release

## Reporting a Vulnerability

We take security vulnerabilities seriously. Please use GitHub's private security advisory feature to report vulnerabilities rather than public GitHub issues.

### How to Report

**GitHub Private Security Advisory:** [Report a security vulnerability](https://github.com/Spenquatch/spec/security/advisories/new)

**Alternative Methods:**
- **GitHub Direct Message**: Contact @Spenquatch directly for sensitive issues
- **GitHub Issue** (for non-sensitive security improvements): Use the security label

**Please Include:**
- **Description**: Clear description of the vulnerability
- **Reproduction Steps**: Detailed steps to reproduce the issue
- **Impact Assessment**: Potential security impact and affected components
- **Environment**: OS, Python version, spec-cli version
- **Proof of Concept**: Code or commands demonstrating the issue (if safe to share)
- **Suggested Fix**: Any ideas for fixing the issue (optional)
- **CVE Details**: If you've already requested a CVE ID

**Please Do NOT Include:**
- Actual exploitation against production systems
- Any data that could harm users or systems
- Public disclosure before we've had a chance to respond

### Response Timeline

- **Initial Response:** Within 24 hours via GitHub notification (acknowledgment and triage)
- **Status Update:** Within 72 hours via GitHub security advisory (investigation results)
- **Resolution:** Varies by severity (see below)

**Resolution Timeframes:**
- **Critical**: 24-48 hours
- **High**: 1 week
- **Medium**: 2-4 weeks
- **Low**: Next regular release

### What to Expect

1. **Acknowledgment** of your report via GitHub security advisory
2. **Triage** and severity assessment using GitHub's CVSS scoring
3. **Investigation** and vulnerability validation with updates in the advisory
4. **Fix Development** (if confirmed vulnerable) with progress tracking
5. **Testing** and quality assurance
6. **Coordinated Disclosure** through GitHub security advisory publication
7. **Public Advisory** using GitHub's security advisory system
8. **Recognition** in GitHub security advisory and project contributors (if desired)

## Security Features

### Local-First Architecture
- **No External Dependencies**: Core functionality works entirely offline
- **Local AI Processing**: Documentation generation uses local models only
- **No Data Transmission**: Your code never leaves your machine
- **Optional Cloud Features**: Any cloud features are explicitly opt-in and clearly marked

### Data Protection & Privacy
- **No Sensitive Data Logging**: Prevents accidental exposure of secrets, API keys, or credentials
- **Secure File Path Handling**: Prevents directory traversal and validates all file operations
- **Input Validation**: Comprehensive sanitization of all user input and file paths
- **Memory Security**: Secure handling of in-memory data with proper cleanup
- **Temporary File Security**: Secure creation and cleanup of temporary files

### Code Security
- **Type Safety**: MyPy strict mode with 100% type coverage prevents many security issues
- **Input Sanitization**: All user inputs validated and sanitized before processing
- **Path Validation**: Prevents directory traversal and ensures operations stay within project bounds
- **Dependency Security**: Regular automated scanning for vulnerable dependencies
- **Static Analysis**: Comprehensive static analysis with security-focused linters

### Development Security
- **Secure Development**: Security-conscious development practices and code review
- **Automated Security Scanning**: Pre-commit hooks and CI/CD security checks
- **Dependency Management**: Pinned dependencies with regular security updates
- **Secret Prevention**: Pre-commit hooks prevent accidental commit of secrets
- **Security Testing**: Security-focused test cases and vulnerability testing

## Responsible Disclosure

We deeply appreciate security researchers who help improve spec-cli's security. We are committed to working with the security community through responsible disclosure.

### Recognition
- **GitHub Security Advisory**: Credit in GitHub's public security advisories (with your permission)
- **Contributor Recognition**: Listed in GitHub project contributors and CHANGELOG
- **GitHub Profile**: Security contributions visible on your GitHub contribution graph
- **Hall of Fame**: Special recognition in project README for security contributors (planned)

### Coordination Guidelines
- **Please allow reasonable time** for us to investigate and fix issues before public disclosure
- **We will keep you informed** of our progress through GitHub security advisory updates
- **We will coordinate timing** of public disclosure through GitHub's coordinated disclosure process
- **We will provide credit** as desired in GitHub security advisories and public communications

### Bug Bounty Program
While we don't currently have a formal bug bounty program, we are considering implementing one as the project grows. Security researchers who report valid vulnerabilities will be the first to know when this becomes available.

### Contact for Questions
If you have questions about our security policy or need clarification on the disclosure process, please:

- **GitHub Discussions**: [Ask security-related questions](https://github.com/Spenquatch/spec/discussions) using the "Security" category
- **Direct Message**: Contact @Spenquatch directly on GitHub for private inquiries

---

**Thank you for helping keep spec-cli and its users secure!**

We are committed to transparency, security, and working collaboratively with the security community to build a safer tool for everyone.
