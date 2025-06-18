# Security Considerations

## Dependency Vulnerabilities

### PyTorch GHSA-887c-mr87-cxwp (CVE-2025-3730)

**Status**: False Positive (Resolved)
**Date Assessed**: 2025-06-18

#### Details
- **Vulnerability**: Local denial of service in `torch.nn.functional.ctc_loss`
- **Affected Versions**: PyTorch 2.6.0
- **Current Version**: torch 2.7.1
- **Patch Commit**: 46fc5d8e360127361211cb237d5f9eef0223e567

#### Risk Assessment
- **CVSS Score**: 4.8 (Medium)
- **Attack Vector**: Local only
- **Impact**: Denial of Service
- **Function**: CTC (Connectionist Temporal Classification) loss

#### Decision
We are accepting this reported vulnerability as a false positive because:

1. **Version Status**: We use torch 2.7.1, which includes the security patch (vulnerability was in 2.6.0)
2. **Limited Impact**: Local DoS only, not remote code execution
3. **Function Usage**: spec-cli does not use CTC loss functionality
4. **Database Lag**: pip-audit database has not been updated to reflect the fix in 2.7.1

#### Configuration
This vulnerability is ignored in our pip-audit configuration:
```bash
pip-audit --ignore-vuln GHSA-887c-mr87-cxwp
```

See `scripts/dev_runners.py` audit function for implementation.

#### Monitoring
- Continue to monitor PyTorch security advisories
- Update to newer versions when available
- Re-evaluate if spec-cli adds CTC loss functionality
- Remove ignore flag when pip-audit database is updated

## Reporting Security Issues

If you discover a security vulnerability in spec-cli, please report it privately to the maintainers.
