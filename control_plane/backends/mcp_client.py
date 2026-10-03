"""
Real MCP Client for TradingView MCP Server
==========================================
Genuine JSON-RPC 2.0 communication with the MCP server via stdio transport.
No mocks, no placeholders - actual tool invocation and evidence capture.
"""

import json
import sys
import subprocess
import time
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import threading
import queue


@dataclass
class MCPToolResult:
    """Result of an actual MCP tool call."""
    tool: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0
    timestamp: str = ""
    request_id: str = ""
    raw_response: str = ""


@dataclass
class MCPToolInfo:
    """Discovered tool information."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    category: str = ""


class MCPClient:
    """
    Real MCP client using JSON-RPC 2.0 over stdio transport.
    
    Communicates with the actual MCP server process via stdin/stdout.
    No mocks, no placeholders - genuine tool invocation.
    """
    
    def __init__(self, server_dir: str = r"C:\Users\wigmore\trading_stack\tradingview-mcp-jackson",
                 server_script: str = "src/server.js"):
        self.server_dir = server_dir
        self.server_script = server_script
        self._process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._lock = threading.Lock()
        self._tools_cache: Optional[List[MCPToolInfo]] = None
        self._server_info: Optional[Dict[str, Any]] = None
    
    def _next_id(self) -> int:
        with self._lock:
            self._request_id += 1
            return self._request_id
    
    def start(self) -> bool:
        """Start the MCP server process."""
        try:
            launch_options = {}
            if sys.platform == 'win32':
                startup = subprocess.STARTUPINFO()
                startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startup.wShowWindow = subprocess.SW_HIDE
                launch_options = {
                    'creationflags': subprocess.CREATE_NO_WINDOW,
                    'startupinfo': startup,
                }
            self._process = subprocess.Popen(
                ["node", self.server_script],
                cwd=self.server_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                **launch_options,
            )
            # Wait for server to initialize
            time.sleep(2)
            return self._process.poll() is None
        except Exception as e:
            print(f"Failed to start MCP server: {e}")
            return False
    
    def stop(self):
        """Stop the MCP server process."""
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
    
    def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request and return the response."""
        if not self._process or self._process.poll() is not None:
            raise RuntimeError("MCP server not running")
        
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
        }
        if params:
            request["params"] = params
        
        request_json = json.dumps(request) + "\n"
        
        # Send request
        self._process.stdin.write(request_json)
        self._process.stdin.flush()
        
        # Read response (may take time for tool execution)
        response_line = self._process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from MCP server")
        
        response = json.loads(response_line)
        
        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")
        
        return response.get("result", {})
    
    def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP connection."""
        result = self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "trading-research-control-plane",
                "version": "0.2.0"
            }
        })
        self._server_info = result
        # Send initialized notification
        self._send_notification("notifications/initialized", {})
        return result
    
    def _send_notification(self, method: str, params: Dict[str, Any] = None):
        """Send a JSON-RPC notification (no response expected)."""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params:
            notification["params"] = params
        
        notification_json = json.dumps(notification) + "\n"
        self._process.stdin.write(notification_json)
        self._process.stdin.flush()
    
    def list_tools(self) -> List[MCPToolInfo]:
        """Discover all available tools from the MCP server."""
        if self._tools_cache is not None:
            return self._tools_cache
        
        result = self._send_request("tools/list", {})
        tools = []
        
        for tool_data in result.get("tools", []):
            # Categorize tool based on name prefix
            name = tool_data.get("name", "")
            category = self._categorize_tool(name)
            
            tool_info = MCPToolInfo(
                name=name,
                description=tool_data.get("description", ""),
                input_schema=tool_data.get("inputSchema", {}),
                category=category,
            )
            tools.append(tool_info)
        
        self._tools_cache = tools
        return tools
    
    def _categorize_tool(self, name: str) -> str:
        """Categorize a tool based on its name."""
        if name.startswith("tv_"):
            return "health"
        elif name.startswith("chart_") or name.startswith("symbol_"):
            return "chart"
        elif name.startswith("pine_") or name.startswith("strategy_tester_"):
            return "pine"
        elif name.startswith("data_"):
            return "data"
        elif name.startswith("draw_"):
            return "drawing"
        elif name.startswith("alert_"):
            return "alerts"
        elif name.startswith("batch_"):
            return "batch"
        elif name.startswith("replay_"):
            return "replay"
        elif name.startswith("indicator_") or name.startswith("watchlist_"):
            return "indicator"
        elif name.startswith("ui_") or name.startswith("layout_") or name.startswith("pane_") or name.startswith("tab_"):
            return "ui"
        elif name.startswith("morning_") or name.startswith("session_"):
            return "morning"
        elif name.startswith("live_") or name.startswith("webhook_"):
            return "live_trading"
        elif name.startswith("capture_"):
            return "capture"
        else:
            return "other"
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> MCPToolResult:
        """Call an MCP tool and return the actual result."""
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        request_id = str(self._next_id())
        
        try:
            result = self._send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments or {}
            })
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Parse the result content
            content = result.get("content", [])
            text_content = ""
            for item in content:
                if item.get("type") == "text":
                    text_content = item.get("text", "")
                    break
            
            # Try to parse JSON from text content
            try:
                parsed_result = json.loads(text_content)
            except (json.JSONDecodeError, TypeError):
                parsed_result = text_content
            
            is_error = result.get("isError", False)
            
            return MCPToolResult(
                tool=tool_name,
                success=not is_error,
                result=parsed_result,
                error=None if not is_error else str(parsed_result),
                execution_time_ms=execution_time_ms,
                timestamp=timestamp,
                request_id=request_id,
                raw_response=text_content,
            )
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return MCPToolResult(
                tool=tool_name,
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms,
                timestamp=timestamp,
                request_id=request_id,
            )
    
    def get_server_info(self) -> Optional[Dict[str, Any]]:
        """Get server information from initialization."""
        return self._server_info


def create_mcp_client(**kwargs) -> MCPClient:
    """Factory function to create MCP client."""
    return MCPClient(**kwargs)