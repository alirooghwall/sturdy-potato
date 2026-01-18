"""Nmap network scanning wrapper with comprehensive scanning capabilities."""

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

from src.services.security_tools.tool_executor import ToolCategory, ToolConfig, ToolExecutor, get_tool_executor


@dataclass
class NmapScanResult:
    """Nmap scan results."""
    
    scan_id: str
    target: str
    scan_type: str
    start_time: str
    end_time: str
    duration: float
    hosts: list[dict[str, Any]] = field(default_factory=list)
    open_ports: list[dict[str, Any]] = field(default_factory=list)
    os_detection: dict[str, Any] = field(default_factory=dict)
    vulnerabilities: list[dict[str, Any]] = field(default_factory=list)
    raw_xml: str = ""
    summary: str = ""


class NmapWrapper:
    """Wrapper for Nmap network scanner."""
    
    def __init__(self):
        """Initialize Nmap wrapper."""
        self.executor = get_tool_executor()
        
        # Nmap tool configuration
        self.config = ToolConfig(
            name="nmap",
            category=ToolCategory.NETWORK_SCANNING,
            command="nmap",
            docker_image="instrumentisto/nmap:latest",
            requires_root=False,
            timeout_seconds=600,
            max_memory_mb=2048,
            network_access=True,
            allowed_args=[
                "sS", "sT", "sU", "sA", "sN", "sF", "sX",  # Scan types
                "p", "F", "r",  # Port specification
                "O", "A", "sV",  # Detection
                "T0", "T1", "T2", "T3", "T4", "T5",  # Timing
                "Pn", "PS", "PA", "PU", "PE",  # Host discovery
                "oX", "oN", "oG",  # Output
                "script", "script-args",  # NSE scripts
                "min-rate", "max-rate",  # Rate limiting
                "v", "vv", "d", "dd",  # Verbosity
            ],
            dangerous_args=["--privileged", "--script=exploit"],
        )
    
    async def quick_scan(self, target: str) -> NmapScanResult:
        """Perform quick port scan (top 100 ports).
        
        Args:
            target: Target IP or domain
        
        Returns:
            NmapScanResult
        """
        args = [
            "-F",  # Fast scan (100 most common ports)
            "-T4",  # Aggressive timing
            "-oX", "/output/scan.xml",
        ]
        
        execution = await self.executor.execute_tool(
            self.config,
            args,
            target,
            {"scan_type": "quick"}
        )
        
        return self._parse_results(execution)
    
    async def full_scan(self, target: str, detect_os: bool = True, detect_services: bool = True) -> NmapScanResult:
        """Perform comprehensive port scan.
        
        Args:
            target: Target IP or domain
            detect_os: Enable OS detection
            detect_services: Enable service version detection
        
        Returns:
            NmapScanResult
        """
        args = [
            "-p-",  # Scan all ports
            "-T4",
            "-oX", "/output/scan.xml",
        ]
        
        if detect_services:
            args.append("-sV")
        
        if detect_os:
            args.append("-O")
        
        execution = await self.executor.execute_tool(
            self.config,
            args,
            target,
            {"scan_type": "full", "os_detection": detect_os, "service_detection": detect_services}
        )
        
        return self._parse_results(execution)
    
    async def stealth_scan(self, target: str, ports: str = "1-1000") -> NmapScanResult:
        """Perform SYN stealth scan.
        
        Args:
            target: Target IP or domain
            ports: Port range to scan
        
        Returns:
            NmapScanResult
        """
        args = [
            "-sS",  # SYN stealth scan
            "-p", ports,
            "-T2",  # Polite timing
            "-oX", "/output/scan.xml",
        ]
        
        execution = await self.executor.execute_tool(
            self.config,
            args,
            target,
            {"scan_type": "stealth", "ports": ports}
        )
        
        return self._parse_results(execution)
    
    async def vulnerability_scan(self, target: str, aggressive: bool = False) -> NmapScanResult:
        """Scan for known vulnerabilities using NSE scripts.
        
        Args:
            target: Target IP or domain
            aggressive: Use aggressive vulnerability scripts
        
        Returns:
            NmapScanResult
        """
        script_category = "vuln" if not aggressive else "vuln,exploit"
        
        args = [
            "-sV",
            "--script", script_category,
            "-oX", "/output/scan.xml",
        ]
        
        execution = await self.executor.execute_tool(
            self.config,
            args,
            target,
            {"scan_type": "vulnerability", "aggressive": aggressive}
        )
        
        return self._parse_results(execution)
    
    async def service_detection_scan(self, target: str, ports: str = "1-65535") -> NmapScanResult:
        """Detailed service and version detection.
        
        Args:
            target: Target IP or domain
            ports: Port range to scan
        
        Returns:
            NmapScanResult
        """
        args = [
            "-sV",
            "-p", ports,
            "--version-intensity", "9",  # Maximum intensity
            "-A",  # Enable OS detection, version detection, script scanning
            "-oX", "/output/scan.xml",
        ]
        
        execution = await self.executor.execute_tool(
            self.config,
            args,
            target,
            {"scan_type": "service_detection", "ports": ports}
        )
        
        return self._parse_results(execution)
    
    async def udp_scan(self, target: str, ports: str = "53,67,68,123,161") -> NmapScanResult:
        """Scan UDP ports (commonly open UDP services).
        
        Args:
            target: Target IP or domain
            ports: UDP ports to scan
        
        Returns:
            NmapScanResult
        """
        args = [
            "-sU",
            "-p", ports,
            "-T4",
            "-oX", "/output/scan.xml",
        ]
        
        execution = await self.executor.execute_tool(
            self.config,
            args,
            target,
            {"scan_type": "udp", "ports": ports}
        )
        
        return self._parse_results(execution)
    
    async def custom_scan(
        self,
        target: str,
        scan_type: str = "sS",
        ports: str = "1-1000",
        timing: str = "T3",
        scripts: list[str] | None = None,
        additional_args: list[str] | None = None,
    ) -> NmapScanResult:
        """Custom Nmap scan with specified parameters.
        
        Args:
            target: Target IP or domain
            scan_type: Scan type (sS, sT, sU, etc.)
            ports: Port specification
            timing: Timing template (T0-T5)
            scripts: NSE scripts to run
            additional_args: Additional Nmap arguments
        
        Returns:
            NmapScanResult
        """
        args = [
            f"-{scan_type}",
            "-p", ports,
            f"-{timing}",
            "-oX", "/output/scan.xml",
        ]
        
        if scripts:
            args.extend(["--script", ",".join(scripts)])
        
        if additional_args:
            args.extend(additional_args)
        
        execution = await self.executor.execute_tool(
            self.config,
            args,
            target,
            {
                "scan_type": "custom",
                "scan_params": {
                    "scan_type": scan_type,
                    "ports": ports,
                    "timing": timing,
                    "scripts": scripts,
                }
            }
        )
        
        return self._parse_results(execution)
    
    def _parse_results(self, execution: Any) -> NmapScanResult:
        """Parse Nmap XML output.
        
        Args:
            execution: Tool execution result
        
        Returns:
            Parsed NmapScanResult
        """
        result = NmapScanResult(
            scan_id=execution.execution_id,
            target=execution.metadata.get("target", "unknown"),
            scan_type=execution.metadata.get("scan_type", "unknown"),
            start_time=execution.started_at.isoformat() if execution.started_at else "",
            end_time=execution.completed_at.isoformat() if execution.completed_at else "",
            duration=0.0,
        )
        
        # Parse XML output if available
        try:
            # Find XML file in output
            xml_content = None
            for output_file in execution.output_files:
                if output_file.endswith(".xml"):
                    # TODO: Read file content
                    pass
            
            if not xml_content and execution.stdout:
                xml_content = execution.stdout
            
            if xml_content:
                result.raw_xml = xml_content
                self._parse_xml(xml_content, result)
        
        except Exception as e:
            result.summary = f"Error parsing results: {str(e)}"
        
        # Generate summary
        result.summary = self._generate_summary(result)
        
        return result
    
    def _parse_xml(self, xml_content: str, result: NmapScanResult) -> None:
        """Parse Nmap XML output.
        
        Args:
            xml_content: XML content
            result: Result object to populate
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Parse hosts
            for host in root.findall('.//host'):
                host_data = self._parse_host(host)
                result.hosts.append(host_data)
                
                # Extract open ports
                for port in host_data.get("ports", []):
                    if port.get("state") == "open":
                        result.open_ports.append({
                            "host": host_data.get("address"),
                            "port": port.get("portid"),
                            "protocol": port.get("protocol"),
                            "service": port.get("service"),
                            "version": port.get("version"),
                        })
            
            # Calculate duration
            if root.get("start") and root.get("end"):
                start = float(root.get("start"))
                end = float(root.get("end"))
                result.duration = end - start
        
        except ET.ParseError as e:
            result.summary += f"\nXML parse error: {str(e)}"
    
    def _parse_host(self, host_elem: ET.Element) -> dict[str, Any]:
        """Parse host element from XML.
        
        Args:
            host_elem: Host XML element
        
        Returns:
            Host data dictionary
        """
        host_data = {
            "status": host_elem.find("status").get("state") if host_elem.find("status") is not None else "unknown",
            "addresses": [],
            "hostnames": [],
            "ports": [],
            "os": [],
        }
        
        # Parse addresses
        for addr in host_elem.findall("address"):
            host_data["addresses"].append({
                "addr": addr.get("addr"),
                "addrtype": addr.get("addrtype"),
            })
            
            # Set primary address
            if addr.get("addrtype") == "ipv4":
                host_data["address"] = addr.get("addr")
        
        # Parse hostnames
        hostnames_elem = host_elem.find("hostnames")
        if hostnames_elem is not None:
            for hostname in hostnames_elem.findall("hostname"):
                host_data["hostnames"].append(hostname.get("name"))
        
        # Parse ports
        ports_elem = host_elem.find("ports")
        if ports_elem is not None:
            for port in ports_elem.findall("port"):
                port_data = {
                    "portid": port.get("portid"),
                    "protocol": port.get("protocol"),
                    "state": port.find("state").get("state") if port.find("state") is not None else "unknown",
                }
                
                # Parse service info
                service = port.find("service")
                if service is not None:
                    port_data["service"] = service.get("name", "unknown")
                    port_data["version"] = service.get("version", "")
                    port_data["product"] = service.get("product", "")
                
                # Parse scripts (vulnerabilities)
                for script in port.findall("script"):
                    if "vuln" in script.get("id", ""):
                        port_data.setdefault("vulnerabilities", []).append({
                            "id": script.get("id"),
                            "output": script.get("output", ""),
                        })
                
                host_data["ports"].append(port_data)
        
        # Parse OS detection
        os_elem = host_elem.find("os")
        if os_elem is not None:
            for osmatch in os_elem.findall("osmatch"):
                host_data["os"].append({
                    "name": osmatch.get("name"),
                    "accuracy": osmatch.get("accuracy"),
                })
        
        return host_data
    
    def _generate_summary(self, result: NmapScanResult) -> str:
        """Generate human-readable summary.
        
        Args:
            result: Scan result
        
        Returns:
            Summary string
        """
        summary_parts = [
            f"Nmap Scan Results for {result.target}",
            f"Scan Type: {result.scan_type}",
            f"Duration: {result.duration:.2f}s",
            f"Hosts Found: {len(result.hosts)}",
            f"Open Ports: {len(result.open_ports)}",
        ]
        
        if result.open_ports:
            summary_parts.append("\nOpen Ports:")
            for port in result.open_ports[:10]:  # Show first 10
                summary_parts.append(
                    f"  {port['host']}:{port['port']}/{port['protocol']} - {port.get('service', 'unknown')}"
                )
        
        if result.vulnerabilities:
            summary_parts.append(f"\nVulnerabilities Found: {len(result.vulnerabilities)}")
        
        return "\n".join(summary_parts)


# Global instance
_nmap_wrapper: NmapWrapper | None = None


def get_nmap_wrapper() -> NmapWrapper:
    """Get Nmap wrapper instance."""
    global _nmap_wrapper
    if _nmap_wrapper is None:
        _nmap_wrapper = NmapWrapper()
    return _nmap_wrapper
