"""LLM-powered security analysis and intelligence system."""

import json
import logging
from dataclasses import dataclass
from typing import Any

from src.services.llm.llm_service import get_llm_service

logger = logging.getLogger(__name__)


@dataclass
class SecurityAnalysis:
    """Security analysis result from LLM."""
    
    analysis_type: str
    input_data: dict[str, Any]
    severity_assessment: str
    risk_score: float
    threat_classification: str
    explanation: str
    attack_vectors: list[str]
    exploitation_difficulty: str
    business_impact: str
    recommendations: list[str]
    remediation_steps: list[str]
    cve_references: list[str]
    mitre_attack_tactics: list[str]
    confidence_score: float


class LLMSecurityAnalyzer:
    """LLM-powered security analysis system."""
    
    def __init__(self):
        """Initialize LLM security analyzer."""
        self.llm = get_llm_service()
    
    async def analyze_vulnerability(
        self,
        vulnerability_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> SecurityAnalysis:
        """Analyze vulnerability using LLM.
        
        Args:
            vulnerability_data: Vulnerability information
            context: Additional context (target info, scan results, etc.)
        
        Returns:
            SecurityAnalysis with LLM insights
        """
        context = context or {}
        
        prompt = self._build_vulnerability_prompt(vulnerability_data, context)
        
        response = await self.llm.generate_completion(
            prompt=prompt,
            temperature=0.3,  # Lower temperature for factual analysis
            max_tokens=2000,
        )
        
        return self._parse_security_analysis(
            response,
            "vulnerability_analysis",
            vulnerability_data
        )
    
    async def analyze_scan_results(
        self,
        scan_results: dict[str, Any],
        scan_type: str,
    ) -> SecurityAnalysis:
        """Analyze security scan results.
        
        Args:
            scan_results: Results from security scan
            scan_type: Type of scan (nmap, nikto, sqlmap, etc.)
        
        Returns:
            SecurityAnalysis with comprehensive assessment
        """
        prompt = f"""You are an expert cybersecurity analyst. Analyze the following {scan_type} scan results and provide a comprehensive security assessment.

Scan Results:
```json
{json.dumps(scan_results, indent=2)}
```

Provide analysis in the following format:

1. **Severity Assessment**: Overall severity (CRITICAL/HIGH/MEDIUM/LOW) with justification
2. **Risk Score**: 0-100 risk score
3. **Threat Classification**: Primary threat type
4. **Explanation**: Detailed explanation of findings in plain language
5. **Attack Vectors**: List of potential attack vectors discovered
6. **Exploitation Difficulty**: How difficult to exploit (TRIVIAL/EASY/MODERATE/DIFFICULT/VERY_DIFFICULT)
7. **Business Impact**: Potential impact on business operations
8. **Recommendations**: Prioritized list of recommendations
9. **Remediation Steps**: Specific step-by-step remediation instructions
10. **CVE References**: Any relevant CVE IDs
11. **MITRE ATT&CK Tactics**: Applicable MITRE ATT&CK tactics/techniques
12. **Confidence Score**: Confidence in analysis (0.0-1.0)

Analyze thoroughly and provide actionable intelligence."""

        response = await self.llm.generate_completion(
            prompt=prompt,
            temperature=0.3,
            max_tokens=2500,
        )
        
        return self._parse_security_analysis(
            response,
            f"{scan_type}_analysis",
            scan_results
        )
    
    async def correlate_findings(
        self,
        findings: list[dict[str, Any]],
        target_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Correlate multiple security findings using LLM.
        
        Args:
            findings: List of security findings from various sources
            target_info: Information about the target
        
        Returns:
            Correlation analysis
        """
        target_info = target_info or {}
        
        prompt = f"""You are a cybersecurity threat intelligence analyst. Correlate the following security findings to identify attack patterns, vulnerabilities chains, and comprehensive threat assessment.

Target Information:
```json
{json.dumps(target_info, indent=2)}
```

Security Findings:
```json
{json.dumps(findings, indent=2)}
```

Provide correlation analysis:

1. **Attack Pattern Detection**: Identify any multi-stage attack patterns
2. **Vulnerability Chains**: Vulnerabilities that can be chained together
3. **Priority Vulnerabilities**: Most critical issues requiring immediate attention
4. **Attack Path Analysis**: Likely paths an attacker would take
5. **Defense Gaps**: Identified security control gaps
6. **Comprehensive Risk Assessment**: Overall security posture
7. **Strategic Recommendations**: High-level security improvements
8. **Incident Response Priorities**: If an attack is underway, what to focus on

Be thorough and provide actionable intelligence."""

        response = await self.llm.generate_completion(
            prompt=prompt,
            temperature=0.4,
            max_tokens=3000,
        )
        
        return {
            "correlation_analysis": response,
            "findings_count": len(findings),
            "target": target_info.get("address", "unknown"),
        }
    
    async def generate_exploit_recommendation(
        self,
        vulnerability: dict[str, Any],
        constraints: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate exploit recommendations using LLM.
        
        Args:
            vulnerability: Vulnerability details
            constraints: Exploitation constraints (time, stealth, etc.)
        
        Returns:
            Exploit recommendations
        """
        constraints = constraints or {}
        
        prompt = f"""You are a penetration testing expert. Based on the following vulnerability, provide exploitation recommendations.

Vulnerability:
```json
{json.dumps(vulnerability, indent=2)}
```

Constraints:
```json
{json.dumps(constraints, indent=2)}
```

Provide:

1. **Exploitability Assessment**: How exploitable is this vulnerability?
2. **Required Conditions**: What conditions must be met for exploitation?
3. **Metasploit Modules**: Relevant Metasploit modules if available
4. **Manual Exploitation**: Manual exploitation techniques
5. **Payload Recommendations**: Suitable payloads for different scenarios
6. **Detection Risk**: Likelihood of detection (HIGH/MEDIUM/LOW)
7. **Stealth Techniques**: How to minimize detection
8. **Post-Exploitation**: What to do after successful exploitation
9. **Risks & Warnings**: Potential risks and things that could go wrong

Provide responsible, ethical penetration testing guidance only."""

        response = await self.llm.generate_completion(
            prompt=prompt,
            temperature=0.4,
            max_tokens=2000,
        )
        
        return {
            "vulnerability_id": vulnerability.get("id", "unknown"),
            "exploit_recommendation": response,
            "constraints_applied": constraints,
        }
    
    async def explain_for_executive(
        self,
        technical_findings: dict[str, Any],
    ) -> str:
        """Translate technical findings into executive summary.
        
        Args:
            technical_findings: Technical security findings
        
        Returns:
            Executive-friendly explanation
        """
        prompt = f"""You are translating technical security findings for C-level executives who are not technical. Explain in plain business language focusing on risk, impact, and priorities.

Technical Findings:
```json
{json.dumps(technical_findings, indent=2)}
```

Provide an executive summary that includes:

1. **Bottom Line Up Front**: What's the most important thing to know?
2. **Business Risk**: How does this affect the business?
3. **Potential Consequences**: What could happen if not addressed?
4. **Cost Implications**: Potential financial impact
5. **Priority Actions**: Top 3 things that must be done
6. **Timeline**: Urgency level and recommended timeline
7. **Resource Requirements**: What resources are needed?

Use plain language, avoid jargon, focus on business outcomes."""

        response = await self.llm.generate_completion(
            prompt=prompt,
            temperature=0.5,
            max_tokens=1500,
        )
        
        return response
    
    async def generate_remediation_code(
        self,
        vulnerability: dict[str, Any],
        language: str,
    ) -> str:
        """Generate code patches or fixes for vulnerabilities.
        
        Args:
            vulnerability: Vulnerability details
            language: Programming language
        
        Returns:
            Code fix/patch
        """
        prompt = f"""You are a secure coding expert. Generate a code fix/patch for the following vulnerability in {language}.

Vulnerability:
```json
{json.dumps(vulnerability, indent=2)}
```

Provide:

1. **Vulnerable Code Pattern**: What the vulnerable code likely looks like
2. **Secure Code Fix**: Corrected secure version
3. **Explanation**: Why the fix works
4. **Additional Considerations**: Other security best practices
5. **Testing Recommendations**: How to verify the fix

Generate production-ready, secure code."""

        response = await self.llm.generate_completion(
            prompt=prompt,
            temperature=0.3,
            max_tokens=1500,
        )
        
        return response
    
    def _build_vulnerability_prompt(
        self,
        vuln_data: dict[str, Any],
        context: dict[str, Any],
    ) -> str:
        """Build comprehensive vulnerability analysis prompt."""
        
        prompt = f"""You are an expert cybersecurity vulnerability analyst. Analyze the following vulnerability in detail.

Vulnerability Data:
```json
{json.dumps(vuln_data, indent=2)}
```

Additional Context:
```json
{json.dumps(context, indent=2)}
```

Provide comprehensive analysis including:

1. **Severity Assessment**: CRITICAL/HIGH/MEDIUM/LOW with detailed justification
2. **Risk Score**: Numerical risk score (0-100) considering likelihood and impact
3. **Threat Classification**: Type of vulnerability/threat
4. **Detailed Explanation**: Plain language explanation of the vulnerability
5. **Attack Vectors**: How can this be exploited?
6. **Exploitation Difficulty**: How hard is it to exploit?
7. **Business Impact**: What's the real-world impact?
8. **Immediate Actions**: What should be done right now?
9. **Remediation Steps**: Step-by-step fix instructions
10. **Prevention**: How to prevent this in the future?
11. **Related CVEs**: Any related CVE identifiers
12. **MITRE ATT&CK Mapping**: Map to MITRE ATT&CK framework

Be thorough, accurate, and actionable."""

        return prompt
    
    def _parse_security_analysis(
        self,
        llm_response: str,
        analysis_type: str,
        input_data: dict[str, Any],
    ) -> SecurityAnalysis:
        """Parse LLM response into SecurityAnalysis structure."""
        
        # Extract structured information from LLM response
        # This is a simplified parser - in production, use more robust parsing
        
        lines = llm_response.split("\n")
        
        # Extract key information (simplified)
        severity = "MEDIUM"
        risk_score = 50.0
        threat_class = "unknown"
        explanation = llm_response[:500]
        
        # Try to extract severity
        for line in lines:
            if "severity" in line.lower() and any(s in line.upper() for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]):
                if "CRITICAL" in line.upper():
                    severity = "CRITICAL"
                    risk_score = 90.0
                elif "HIGH" in line.upper():
                    severity = "HIGH"
                    risk_score = 75.0
                elif "LOW" in line.upper():
                    severity = "LOW"
                    risk_score = 25.0
                break
        
        # Extract recommendations and remediation
        recommendations = []
        remediation = []
        cves = []
        mitre_tactics = []
        
        in_recommendations = False
        in_remediation = False
        
        for line in lines:
            if "recommendation" in line.lower():
                in_recommendations = True
                in_remediation = False
                continue
            elif "remediation" in line.lower():
                in_remediation = True
                in_recommendations = False
                continue
            
            if in_recommendations and line.strip().startswith(("-", "*", "•")):
                recommendations.append(line.strip()[1:].strip())
            elif in_remediation and line.strip().startswith(("-", "*", "•")):
                remediation.append(line.strip()[1:].strip())
            
            # Extract CVEs
            if "CVE-" in line:
                import re
                cves.extend(re.findall(r'CVE-\d{4}-\d+', line))
            
            # Extract MITRE tactics
            if "T1" in line and any(tactic in line for tactic in ["TA00", "T1"]):
                import re
                mitre_tactics.extend(re.findall(r'T\d{4}(?:\.\d{3})?', line))
        
        return SecurityAnalysis(
            analysis_type=analysis_type,
            input_data=input_data,
            severity_assessment=severity,
            risk_score=risk_score,
            threat_classification=threat_class,
            explanation=explanation,
            attack_vectors=[],
            exploitation_difficulty="MODERATE",
            business_impact=llm_response,
            recommendations=recommendations[:10],
            remediation_steps=remediation[:10],
            cve_references=list(set(cves)),
            mitre_attack_tactics=list(set(mitre_tactics)),
            confidence_score=0.8,
        )


# Global instance
_llm_security_analyzer: LLMSecurityAnalyzer | None = None


def get_llm_security_analyzer() -> LLMSecurityAnalyzer:
    """Get LLM security analyzer instance."""
    global _llm_security_analyzer
    if _llm_security_analyzer is None:
        _llm_security_analyzer = LLMSecurityAnalyzer()
    return _llm_security_analyzer
