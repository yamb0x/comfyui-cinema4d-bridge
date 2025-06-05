"""
Cinema4D Plugin for MCP Server Communication
This script should be loaded in Cinema4D Script Manager to establish socket connection
"""

import c4d
import socket
import json
import threading
import time
from c4d import gui

# Global variables
g_socket = None
g_connected = False
g_server_thread = None

def execute_script(script_code):
    """Execute Python script and return result"""
    try:
        # Create a local namespace for script execution
        local_namespace = {
            'c4d': c4d,
            'documents': c4d.documents,
            'gui': c4d.gui
        }
        
        # Capture print output
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        # Execute the script
        exec(script_code, local_namespace)
        
        # Get the output
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        return {"success": True, "output": output}
        
    except Exception as e:
        import sys
        sys.stdout = old_stdout
        return {"success": False, "error": str(e)}

def handle_client(client_socket):
    """Handle client connection and commands"""
    global g_connected
    
    try:
        while g_connected:
            # Receive data
            data = client_socket.recv(4096)
            if not data:
                break
                
            try:
                # Parse JSON command
                command = json.loads(data.decode('utf-8'))
                script = command.get('script', '')
                
                if script:
                    # Execute script in main thread context
                    result = execute_script(script)
                    response = json.dumps(result)
                else:
                    response = json.dumps({"success": False, "error": "No script provided"})
                
                # Send response
                client_socket.send(response.encode('utf-8'))
                
            except json.JSONDecodeError:
                error_response = json.dumps({"success": False, "error": "Invalid JSON"})
                client_socket.send(error_response.encode('utf-8'))
                
    except Exception as e:
        print(f"Client handler error: {e}")
    finally:
        client_socket.close()

def socket_server_thread():
    """Socket server thread function"""
    global g_socket, g_connected
    
    try:
        # Create socket
        g_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        g_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        g_socket.bind(('localhost', 54321))
        g_socket.listen(1)
        
        print("Cinema4D MCP Server listening on port 54321")
        gui.MessageDialog("Cinema4D MCP Server listening on port 54321")
        
        while g_connected:
            try:
                # Accept connections
                client_socket, addr = g_socket.accept()
                print(f"MCP Client connected from {addr}")
                
                # Handle client in the same thread (Cinema4D requirement)
                handle_client(client_socket)
                
            except socket.error as e:
                if g_connected:
                    print(f"Socket accept error: {e}")
                break
                
    except Exception as e:
        print(f"Socket server error: {e}")
        gui.MessageDialog(f"Socket server error: {e}")
    finally:
        if g_socket:
            g_socket.close()
            g_socket = None

def start_server():
    """Start the MCP server"""
    global g_connected, g_server_thread
    
    if g_connected:
        gui.MessageDialog("Server is already running!")
        return
    
    g_connected = True
    g_server_thread = threading.Thread(target=socket_server_thread, daemon=True)
    g_server_thread.start()

def stop_server():
    """Stop the MCP server"""
    global g_connected, g_socket, g_server_thread
    
    g_connected = False
    
    if g_socket:
        g_socket.close()
        g_socket = None
    
    if g_server_thread:
        g_server_thread.join(timeout=1)
        g_server_thread = None
    
    gui.MessageDialog("Cinema4D MCP Server stopped")

def main():
    """Main function - automatically start server when script loads"""
    start_server()

if __name__ == '__main__':
    main()