"""Security tools API endpoints."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.services.security_tools.wrappers.network_scanning.nmap_wrapper import (
    get_nmap_wrapper,
)
from src.services.security_tools.wrappers.vulnerability_scanning.nikto_wrapper import (
    get_nikto_wrapper,
)
from src.services.security_tools.wrappers.vulnerability_scanning.sqlmap_wrapper import (
    get_sqlmap_wrapper,
)
from src.services.security_tools.wrappers.exploitation.metasploit_wrapper import (
    get_metasploit_wrapper,
)
from src.services.cyber_intelligence.llm_security_analyzer import (
    get_llm_security_analyzer,
)
from src.services.cyber_ml.custom_transformers.cyber_bert import get_cyber_bert


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


router = APIRouter()


# Request/Response Models

class NmapScanRequest(BaseModel):
    """Nmap scan request."""
    target: str = Field(..., description="Target IP or domain")
    scan_type: str = Field("quick", description="quick, full, stealth, vuln, service, udp, custom")
    ports: str | None = Field(None, description="Port range (e.g., 1-1000)")
    detect_os: bool = Field(False, description="Enable OS detection")
    detect_services: bool = Field(True, description="Enable service detection")


class SQLMapScanRequest(BaseModel):
    """SQLMap scan request."""
    url: str = Field(..., description="Target URL")
    data: str | None = Field(None, description="POST data")
    cookie: str | None = Field(None, description="Cookie string")
    level: int = Field(1, ge=1, le=5, description="Test level")
    risk: int = Field(1, ge=1, le=3, description="Risk level")
    scan_type: str = Field("detect", description="detect, full, enum_dbs, enum_tables, dump")


class NiktoScanRequest(BaseModel):
    """Nikto scan request."""
    host: str = Field(..., description="Target host")
    port: int = Field(80, ge=1, le=65535, description="Port number")
    ssl: bool = Field(False, description="Use SSL/TLS")
    scan_type: str = Field("quick", description="quick, comprehensive, custom")


class MetasploitRequest(BaseModel):
    """Metasploit operation request."""
    operation: str = Field(..., description="search, check, auxiliary")
    target: str | None = Field(None, description="Target IP")
    module: str | None = Field(None, description="Module path")
    query: str | None = Field(None, description="Search query")
    options: dict[str, Any] = Field(default_factory=dict, description="Module options")


class SecurityAnalysisRequest(BaseModel):
    """Security analysis request."""
    analysis_type: str = Field(..., description="vulnerability, scan_results, correlation")
    data: dict[str, Any] = Field(..., description="Data to analyze")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ThreatClassificationRequest(BaseModel):
    """Threat classification request."""
    text: str = Field(..., description="Security text to classify")
    include_probabilities: bool = Field(False, description="Include probability distribution")


# Endpoints

@router.post("/nmap/scan")
async def nmap_scan(request: NmapScanRequest) -> dict[str, Any]:
    """Execute Nmap scan.
    
    Scans target using Nmap with specified configuration.
    """
    nmap = get_nmap_wrapper()
    
    try:
        if request.scan_type == "quick":
            result = await nmap.quick_scan(request.target)
        elif request.scan_type == "full":
            result = await nmap.full_scan(
                request.target,
                detect_os=request.detect_os,
                detect_services=request.detect_services,
            )
        elif request.scan_type == "stealth":
            result = await nmap.stealth_scan(request.target, ports=request.ports or "1-1000")
        elif request.scan_type == "vuln":
            result = await nmap.vulnerability_scan(request.target)
        elif request.scan_type == "service":
            result = await nmap.service_detection_scan(request.target, ports=request.ports or "1-1000")
        elif request.scan_type == "udp":
            result = await nmap.udp_scan(request.target)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown scan type: {request.scan_type}",
            )
        
        return {
            "scan_id": result.scan_id,
            "target": result.target,
            "scan_type": result.scan_type,
            "hosts": result.hosts,
            "open_ports": result.open_ports,
            "summary": result.summary,
            "timestamp": utcnow().isoformat(),
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}",
        )


@router.post("/sqlmap/scan")
async def sqlmap_scan(request: SQLMapScanRequest) -> dict[str, Any]:
    """Execute SQLMap SQL injection scan.
    
    Tests target URL for SQL injection vulnerabilities.
    """
    sqlmap = get_sqlmap_wrapper()
    
    try:
        if request.scan_type == "detect":
            result = await sqlmap.detect_injection(
                request.url,
                level=request.level,
                risk=request.risk,
            )
        elif request.scan_type == "full":
            result = await sqlmap.full_injection_test(
                request.url,
                data=request.data,
                cookie=request.cookie,
                level=request.level,
                risk=request.risk,
            )
        elif request.scan_type == "enum_dbs":
            result = await sqlmap.enumerate_databases(request.url)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown scan type: {request.scan_type}",
            )
        
        return {
            "scan_id": result.scan_id,
            "target_url": result.target_url,
            "injectable": result.injectable,
            "injection_points": result.injection_points,
            "dbms": result.dbms,
            "databases": result.databases,
            "summary": result.summary,
            "timestamp": utcnow().isoformat(),
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}",
        )


@router.post("/nikto/scan")
async def nikto_scan(request: NiktoScanRequest) -> dict[str, Any]:
    """Execute Nikto web server scan.
    
    Scans web server for known vulnerabilities and misconfigurations.
    """
    nikto = get_nikto_wrapper()
    
    try:
        if request.scan_type == "quick":
            result = await nikto.quick_scan(request.host, request.port, request.ssl)
        elif request.scan_type == "comprehensive":
            result = await nikto.comprehensive_scan(request.host, request.port, request.ssl)
        else:
            result = await nikto.scan_host(request.host, request.port, request.ssl)
        
        return {
            "scan_id": result.scan_id,
            "target": result.target,
            "port": result.port,
            "ssl": result.ssl,
            "findings": result.findings,
            "vulnerabilities": result.vulnerabilities,
            "server_info": result.server_info,
            "summary": result.summary,
            "timestamp": utcnow().isoformat(),
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}",
        )


@router.post("/metasploit/execute")
async def metasploit_execute(request: MetasploitRequest) -> dict[str, Any]:
    """Execute Metasploit operation.
    
    Search exploits, check vulnerabilities, or run auxiliary modules.
    """
    msf = get_metasploit_wrapper()
    
    try:
        if request.operation == "search":
            if not request.query:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Query required for search operation",
                )
            result = await msf.search_exploits(request.query)
        
        elif request.operation == "check":
            if not request.target or not request.module:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Target and module required for check operation",
                )
            result = await msf.check_vulnerability(
                request.target,
                request.options.get("port", 80),
                request.module,
            )
        
        elif request.operation == "auxiliary":
            if not request.target or not request.module:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Target and module required for auxiliary operation",
                )
            result = await msf.run_auxiliary(
                request.module,
                request.target,
                request.options,
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown operation: {request.operation}",
            )
        
        return {
            "operation_id": result.operation_id,
            "operation_type": result.operation_type,
            "target": result.target,
            "module": result.module_used,
            "success": result.success,
            "exploited": result.exploited,
            "summary": result.summary,
            "sessions": result.sessions,
            "timestamp": utcnow().isoformat(),
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Operation failed: {str(e)}",
        )


@router.post("/analyze/llm")
async def analyze_with_llm(request: SecurityAnalysisRequest) -> dict[str, Any]:
    """Analyze security data using LLM.
    
    Uses GPT-4/Claude for intelligent security analysis.
    """
    analyzer = get_llm_security_analyzer()
    
    try:
        if request.analysis_type == "vulnerability":
            result = await analyzer.analyze_vulnerability(
                request.data,
                request.context,
            )
            
            return {
                "analysis_type": result.analysis_type,
                "severity": result.severity_assessment,
                "risk_score": result.risk_score,
                "threat_classification": result.threat_classification,
                "explanation": result.explanation,
                "attack_vectors": result.attack_vectors,
                "exploitation_difficulty": result.exploitation_difficulty,
                "recommendations": result.recommendations,
                "remediation_steps": result.remediation_steps,
                "cve_references": result.cve_references,
                "mitre_tactics": result.mitre_attack_tactics,
                "confidence": result.confidence_score,
            }
        
        elif request.analysis_type == "scan_results":
            result = await analyzer.analyze_scan_results(
                request.data,
                request.context.get("scan_type", "unknown"),
            )
            
            return {
                "analysis_type": result.analysis_type,
                "severity": result.severity_assessment,
                "risk_score": result.risk_score,
                "explanation": result.explanation,
                "recommendations": result.recommendations,
            }
        
        elif request.analysis_type == "correlation":
            result = await analyzer.correlate_findings(
                request.data.get("findings", []),
                request.context,
            )
            
            return result
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown analysis type: {request.analysis_type}",
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@router.post("/classify/threat")
async def classify_threat(request: ThreatClassificationRequest) -> dict[str, Any]:
    """Classify threat level using CyberBERT transformer.
    
    Uses custom-trained BERT model for cybersecurity text classification.
    """
    cyberbert = get_cyber_bert()
    
    try:
        result = cyberbert.classify_threat_level(
            request.text,
            return_probabilities=request.include_probabilities,
        )
        
        return {
            "label": result["label"],
            "confidence": result["confidence"],
            "probabilities": result.get("probabilities"),
            "timestamp": utcnow().isoformat(),
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}",
        )


@router.get("/tools/available")
async def list_available_tools() -> dict[str, Any]:
    """List all available security tools."""
    return {
        "tools": [
            {
                "name": "nmap",
                "category": "network_scanning",
                "description": "Network scanning and host discovery",
                "scan_types": ["quick", "full", "stealth", "vuln", "service", "udp"],
            },
            {
                "name": "sqlmap",
                "category": "vulnerability_scanning",
                "description": "SQL injection detection and exploitation",
                "scan_types": ["detect", "full", "enum_dbs", "enum_tables", "dump"],
            },
            {
                "name": "nikto",
                "category": "vulnerability_scanning",
                "description": "Web server scanner",
                "scan_types": ["quick", "comprehensive"],
            },
            {
                "name": "metasploit",
                "category": "exploitation",
                "description": "Exploitation framework",
                "operations": ["search", "check", "auxiliary"],
            },
        ],
        "ai_features": [
            {
                "name": "llm_analyzer",
                "description": "LLM-powered security analysis",
                "capabilities": ["vulnerability", "scan_results", "correlation"],
            },
            {
                "name": "cyberbert",
                "description": "Custom transformer for threat classification",
                "capabilities": ["threat_classification", "severity_prediction"],
            },
        ],
    }
