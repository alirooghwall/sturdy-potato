# Security Tools Integration - Complete Implementation Guide

## 🎯 System Overview

The ISR Platform now includes **comprehensive Kali Linux security tools integration** with LLM-powered analysis and custom ML models.

### What's Implemented

✅ **Core Infrastructure**
- Tool execution engine with Docker isolation
- Input validation and sanitization
- Resource management and rate limiting
- Async execution with timeout controls

✅ **Security Tools Integrated**
1. **Nmap** - Network scanning (7 scan types)
2. **SQLmap** - SQL injection detection
3. **Nikto** - Web server vulnerability scanner
4. **Metasploit** - Exploitation framework

✅ **AI/ML Components**
- **LLM Security Analyzer** - GPT-4/Claude for intelligent analysis
- **CyberBERT** - Custom transformer for threat classification
- Full security analysis pipeline

✅ **API Endpoints**
- `/api/v1/security/nmap/scan` - Network scanning
- `/api/v1/security/sqlmap/scan` - SQL injection testing
- `/api/v1/security/nikto/scan` - Web vulnerability scanning
- `/api/v1/security/metasploit/execute` - Exploitation operations
- `/api/v1/security/analyze/llm` - LLM security analysis
- `/api/v1/security/classify/threat` - CyberBERT threat classification

✅ **Deployment**
- Docker Compose configuration
- Kubernetes manifests
- Horizontal pod autoscaling
- Production-ready setup

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended for Development)

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env and add:
# - SECRET_KEY
# - OPENAI_API_KEY (for LLM features)

# 2. Start all services
docker-compose -f docker-compose.security.yml up -d

# 3. Wait for services to be ready
docker-compose -f docker-compose.security.yml ps

# 4. Run migrations
docker-compose -f docker-compose.security.yml exec isr-api \
  python -m alembic upgrade head

# 5. Access API
open http://localhost:8000/docs
```

### Option 2: Kubernetes (Production)

```bash
# 1. Create namespace and secrets
kubectl apply -f kubernetes/security-deployment.yaml

# 2. Update secrets
kubectl edit secret isr-secrets -n isr-platform

# 3. Deploy application
kubectl apply -f kubernetes/security-deployment.yaml

# 4. Check status
kubectl get pods -n isr-platform

# 5. Access via LoadBalancer
kubectl get svc isr-api -n isr-platform
```

---

## 📊 Using Security Tools

### 1. Network Scanning with Nmap

```bash
# Quick scan (top 100 ports)
curl -X POST http://localhost:8000/api/v1/security/nmap/scan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "target": "192.168.1.1",
    "scan_type": "quick"
  }'

# Full scan with OS/service detection
curl -X POST http://localhost:8000/api/v1/security/nmap/scan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "target": "scanme.nmap.org",
    "scan_type": "full",
    "detect_os": true,
    "detect_services": true
  }'

# Vulnerability scan
curl -X POST http://localhost:8000/api/v1/security/nmap/scan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "target": "example.com",
    "scan_type": "vuln"
  }'
```

**Response:**
```json
{
  "scan_id": "uuid",
  "target": "192.168.1.1",
  "scan_type": "quick",
  "hosts": [...],
  "open_ports": [
    {
      "host": "192.168.1.1",
      "port": "80",
      "protocol": "tcp",
      "service": "http",
      "version": "Apache 2.4.41"
    }
  ],
  "summary": "Nmap Scan Results..."
}
```

### 2. SQL Injection Testing with SQLmap

```bash
# Detect SQL injection
curl -X POST http://localhost:8000/api/v1/security/sqlmap/scan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "url": "http://target.com/page.php?id=1",
    "scan_type": "detect",
    "level": 3,
    "risk": 2
  }'

# Full injection test with cookies
curl -X POST http://localhost:8000/api/v1/security/sqlmap/scan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "url": "http://target.com/login",
    "scan_type": "full",
    "data": "username=test&password=test",
    "cookie": "session=abc123",
    "level": 5,
    "risk": 3
  }'

# Enumerate databases
curl -X POST http://localhost:8000/api/v1/security/sqlmap/scan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "url": "http://target.com/page.php?id=1",
    "scan_type": "enum_dbs"
  }'
```

### 3. Web Vulnerability Scanning with Nikto

```bash
# Quick scan
curl -X POST http://localhost:8000/api/v1/security/nikto/scan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "host": "example.com",
    "port": 80,
    "ssl": false,
    "scan_type": "quick"
  }'

# Comprehensive HTTPS scan
curl -X POST http://localhost:8000/api/v1/security/nikto/scan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "host": "example.com",
    "port": 443,
    "ssl": true,
    "scan_type": "comprehensive"
  }'
```

### 4. Metasploit Operations

```bash
# Search for exploits
curl -X POST http://localhost:8000/api/v1/security/metasploit/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "operation": "search",
    "query": "apache struts"
  }'

# Check if target is vulnerable
curl -X POST http://localhost:8000/api/v1/security/metasploit/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "operation": "check",
    "target": "192.168.1.100",
    "module": "exploit/multi/http/struts2_content_type_ognl",
    "options": {
      "port": 8080
    }
  }'

# Run auxiliary scanner
curl -X POST http://localhost:8000/api/v1/security/metasploit/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "operation": "auxiliary",
    "target": "192.168.1.0/24",
    "module": "auxiliary/scanner/http/http_version",
    "options": {
      "THREADS": 10
    }
  }'
```

### 5. LLM Security Analysis

```bash
# Analyze vulnerability
curl -X POST http://localhost:8000/api/v1/security/analyze/llm \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "analysis_type": "vulnerability",
    "data": {
      "cve_id": "CVE-2024-1234",
      "description": "SQL injection vulnerability in login form",
      "cvss_score": 9.8
    },
    "context": {
      "target": "production web application",
      "exposure": "public internet"
    }
  }'

# Analyze scan results
curl -X POST http://localhost:8000/api/v1/security/analyze/llm \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "analysis_type": "scan_results",
    "data": {
      "scan_type": "nmap",
      "findings": {
        "open_ports": [80, 443, 22, 3306],
        "services": ["http", "https", "ssh", "mysql"]
      }
    },
    "context": {
      "scan_type": "nmap"
    }
  }'

# Correlate multiple findings
curl -X POST http://localhost:8000/api/v1/security/analyze/llm \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "analysis_type": "correlation",
    "data": {
      "findings": [
        {"tool": "nmap", "finding": "MySQL port 3306 open"},
        {"tool": "nikto", "finding": "Default MySQL credentials"},
        {"tool": "sqlmap", "finding": "SQL injection in login"}
      ]
    },
    "context": {
      "target": "192.168.1.100"
    }
  }'
```

**LLM Response Example:**
```json
{
  "analysis_type": "vulnerability_analysis",
  "severity": "CRITICAL",
  "risk_score": 95.0,
  "threat_classification": "Remote Code Execution",
  "explanation": "The SQL injection vulnerability allows...",
  "attack_vectors": [
    "Direct SQL injection via login form",
    "Bypass authentication",
    "Extract sensitive data"
  ],
  "exploitation_difficulty": "EASY",
  "business_impact": "Complete compromise of database...",
  "recommendations": [
    "Immediately patch SQL injection vulnerability",
    "Implement parameterized queries",
    "Add WAF protection"
  ],
  "remediation_steps": [
    "Step 1: Take application offline or restrict access",
    "Step 2: Apply latest security patches",
    "Step 3: Review all database queries..."
  ],
  "cve_references": ["CVE-2024-1234"],
  "mitre_tactics": ["T1190", "T1078"],
  "confidence": 0.95
}
```

### 6. CyberBERT Threat Classification

```bash
# Classify threat level
curl -X POST http://localhost:8000/api/v1/security/classify/threat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "text": "Remote code execution vulnerability in Apache Struts allows unauthenticated attacker to execute arbitrary commands",
    "include_probabilities": true
  }'
```

**Response:**
```json
{
  "label": "CRITICAL",
  "confidence": 0.96,
  "probabilities": {
    "SAFE": 0.01,
    "INFO": 0.01,
    "LOW": 0.01,
    "MEDIUM": 0.01,
    "HIGH": 0.00,
    "CRITICAL": 0.96
  },
  "timestamp": "2024-01-18T..."
}
```

---

## 🔧 Adding New Security Tools

The framework makes adding new tools straightforward. Here's the pattern:

### 1. Create Tool Wrapper

```python
# src/services/security_tools/wrappers/category/tool_wrapper.py

from ..tool_executor import ToolCategory, ToolConfig, ToolExecutor, get_tool_executor

class YourToolWrapper:
    def __init__(self):
        self.executor = get_tool_executor()
        
        self.config = ToolConfig(
            name="yourtool",
            category=ToolCategory.YOUR_CATEGORY,
            command="yourtool",
            docker_image="yourtool:latest",
            requires_root=False,
            timeout_seconds=600,
            max_memory_mb=2048,
            network_access=True,
            allowed_args=["arg1", "arg2"],
            dangerous_args=["--dangerous"],
        )
    
    async def scan(self, target: str) -> YourResult:
        args = ["-scan", target]
        
        execution = await self.executor.execute_tool(
            self.config,
            args,
            target,
            {"scan_type": "standard"}
        )
        
        return self._parse_results(execution)
    
    def _parse_results(self, execution):
        # Parse tool output
        pass
```

### 2. Add API Endpoint

```python
# Add to src/api/routers/security_tools.py

@router.post("/yourtool/scan")
async def yourtool_scan(request: YourToolRequest):
    wrapper = get_yourtool_wrapper()
    result = await wrapper.scan(request.target)
    return result
```

### 3. Add Docker Service

```yaml
# Add to docker-compose.security.yml

  yourtool:
    image: yourtool:latest
    volumes:
      - security_tools_workspace:/output
    command: tail -f /dev/null
```

That's it! The tool is now integrated.

---

## 🤖 ML Model Training

### Training CyberBERT on Custom Data

```python
from src.services.cyber_ml.custom_transformers.cyber_bert import get_cyber_bert

cyberbert = get_cyber_bert()

# Prepare training data
train_texts = [
    "SQL injection vulnerability...",
    "XSS in user input field...",
    # ... more examples
]

train_labels = [
    "HIGH",
    "MEDIUM",
    # ... corresponding labels
]

# Fine-tune model
results = cyberbert.fine_tune(
    train_texts=train_texts,
    train_labels=train_labels,
    epochs=5,
    batch_size=32,
    learning_rate=2e-5,
    output_dir="./cyberbert-custom",
)
```

---

## 🔒 Security Best Practices

### 1. Input Validation
- All inputs validated before tool execution
- Command injection prevention
- Target validation (IP/domain/URL format)

### 2. Isolation
- Tools run in Docker containers
- Network namespace isolation
- Resource limits enforced

### 3. Access Control
- JWT authentication required
- Role-based access control
- Audit logging of all operations

### 4. Rate Limiting
- Per-user limits
- Per-tool limits
- Global system limits

### 5. Legal Compliance
```python
# Before scanning, verify authorization
if not user_has_authorization(target):
    raise HTTPException(403, "Unauthorized target")
```

---

## 📊 Monitoring & Metrics

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Dependency health
curl http://localhost:8000/ready

# Tool execution status
curl http://localhost:8000/api/v1/security/tools/available
```

### Logs

```bash
# Docker Compose
docker-compose -f docker-compose.security.yml logs -f isr-api

# Kubernetes
kubectl logs -f -n isr-platform deployment/isr-api
```

---

## 🚨 Troubleshooting

### Tool Execution Timeout

```python
# Increase timeout in wrapper
self.config = ToolConfig(
    ...
    timeout_seconds=1800,  # 30 minutes
)
```

### Docker Container Issues

```bash
# Check container logs
docker-compose -f docker-compose.security.yml logs nmap-scanner

# Restart containers
docker-compose -f docker-compose.security.yml restart
```

### ML Model Loading Errors

```bash
# Download models manually
python -c "from transformers import AutoModel; AutoModel.from_pretrained('bert-base-uncased')"
```

---

## 📚 Additional Tools to Implement

Following the pattern above, you can add:

**Web Security:**
- Burp Suite API integration
- OWASP ZAP integration
- Wfuzz
- Commix

**Password Attacks:**
- Hashcat
- John the Ripper
- Hydra
- Medusa

**Wireless:**
- Aircrack-ng
- Kismet
- Reaver

**Forensics:**
- Volatility
- Autopsy
- Foremost

**And 40+ more tools...**

Each follows the same wrapper pattern, making implementation consistent and maintainable.

---

## ✅ Testing

```bash
# Run security tools tests
pytest tests/test_security_tools.py -v

# Test specific tool
pytest tests/test_security_tools.py::test_nmap_scan -v

# Integration tests
pytest tests/test_security_integration.py -v
```

---

## 🎯 What's Production Ready

✅ **Core Framework** - Fully implemented and tested
✅ **4 Major Tools** - Nmap, SQLmap, Nikto, Metasploit
✅ **LLM Analysis** - Complete with GPT-4/Claude
✅ **Custom ML** - CyberBERT transformer ready
✅ **API** - RESTful endpoints documented
✅ **Deployment** - Docker Compose + Kubernetes
✅ **Documentation** - Comprehensive guides

## 🎯 What Needs Extension

📋 **40+ Additional Tools** - Follow wrapper pattern
📋 **Advanced ML Models** - Train on custom datasets
📋 **Orchestration** - Multi-tool workflow automation
📋 **Reporting** - Enhanced report generation
📋 **UI Dashboard** - Web interface for operations

---

**The foundation is complete and production-ready. You can now:**
1. Deploy to Kubernetes
2. Start scanning targets
3. Use LLM for analysis
4. Add new tools as needed
5. Train custom ML models

**This is a professional, scalable, military-grade security operations platform.**
