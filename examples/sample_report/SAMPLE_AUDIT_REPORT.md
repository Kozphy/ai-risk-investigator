# Sample Audit Report — AI Risk Investigator

**Document:** sample_vendor_contract.txt  
**Frameworks:** SOX, ISO 27001, COSO, GDPR, AI Act  
**Mode:** Mock LLM (deterministic demo findings)

## Executive Summary

### Top Risks
- Indemnity and liability caps may be commercially unbalanced
- Data processing clause lacks explicit retention limits
- Vendor access controls are vaguely defined

### Key Observations
- Document contains standard commercial terms with several ambiguous risk transfer clauses
- Privacy and AI-related obligations are incomplete relative to GDPR / AI Act expectations

### Recommended Actions
- Negotiate liability cap symmetry and carve-outs for willful misconduct
- Add data retention, subprocessors, and breach notification SLAs
- Require SOC 2 / ISO 27001 evidence for vendor access

### Heatmap Summary
Elevated legal and data privacy risk; medium operational and vendor risk.

## Findings

| Severity | Category | Finding | Confidence |
|----------|----------|---------|------------|
| High | Legal | Asymmetric indemnity and unlimited liability exposure | 0.86 |
| High | Data Privacy | Insufficient personal data retention controls | 0.81 |
| Medium | AI Governance | AI system usage lacks governance commitments | 0.74 |
| Medium | Vendor | Vendor remote access not constrained | 0.79 |

## Appendix
Supporting text excerpts are drawn from the uploaded document and must be reviewer-validated before management reporting.
