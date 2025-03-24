# Structure for addons/godot_mcp/plugin.gd
@tool
extends EditorPlugin

const SERVER_PORT = 6400
var server: TCPServer = null
var active_connections = []
var command_handler

func _enter_tree():
	# Initialize the plugin
	print("Godot MCP Plugin activated")
	
	# Create command handler
	command_handler = preload("res://addons/godot_mcp/command_handler.gd").new()
	command_handler.set_editor_plugin(self)
	
	# Start the TCP server
	server = TCPServer.new()
	var error = server.listen(SERVER_PORT)
	if error != OK:
		push_error("Failed to start Godot MCP Server on port %d: %s" % [SERVER_PORT, error])
		return
	
	print("Godot MCP Server listening on port %d" % SERVER_PORT)
	
	# Add UI
	add_control_to_bottom_panel(
		preload("res://addons/godot_mcp/ui/mcp_panel.tscn").instantiate(),
		"MCP"
	)

func _exit_tree():
	# Clean up the plugin when disabled
	if server:
		server.stop()
		server = null
	
	for connection in active_connections:
		if connection.get_status() == StreamPeerTCP.STATUS_CONNECTED:
			connection.disconnect_from_host()
	
	active_connections.clear()
	
	# Remove UI
	remove_control_from_bottom_panel(get_editor_interface().get_base_control().get_node("MCPPanel"))
	print("Godot MCP Plugin deactivated")

func _process(delta):
	# Check for new connections
	if server and server.is_connection_available():
		var connection = server.take_connection()
		if connection:
			active_connections.append(connection)
			print("New MCP connection established")
	
	# Process existing connections
	var i = 0
	while i < active_connections.size():
		var connection = active_connections[i]
		
		# Check connection status
		if connection.get_status() != StreamPeerTCP.STATUS_CONNECTED:
			active_connections.remove_at(i)
			print("MCP connection closed")
			continue
		
		# Check for incoming messages
		if connection.get_available_bytes() > 0:
			var data = _read_message(connection)
			if data.size() > 0:
				# Process the command
				var response = _process_command(data)
				
				# Send the response
				_send_message(connection, response)
		
		i += 1

func _read_message(connection):
	# Read data from the connection
	var data = PackedByteArray()
	var bytes_available = connection.get_available_bytes()
	
	if bytes_available > 0:
		data = connection.get_data(bytes_available)[1]
		
		# Attempt to parse as JSON
		var json_string = data.get_string_from_utf8()
		var json = JSON.new()
		var error = json.parse(json_string)
		
		if error == OK:
			return json.get_data()
		else:
			print("Failed to parse JSON: ", json.get_error_message())
			
	return {}

func _send_message(connection, data):
	# Convert to JSON and send
	var json_string = JSON.stringify(data)
	connection.put_data(json_string.to_utf8_buffer())



func _process_command(data):
	# Process the command and return a response
	if data == null or typeof(data) != TYPE_DICTIONARY:
		return {
			"status": "error",
			"error": "Invalid command format. Expected a dictionary."
		}
	
	if not data.has("type") or not data.has("params"):
		return {
			"status": "error",
			"error": "Invalid command format. Expected 'type' and 'params' fields."
		}
	
	var command_type = data["type"]
	var params = data["params"]
	
	if command_type == "ping":
		return {"status": "success", "result": {"message": "pong"}}
	
	# Forward to command handler
	var result = command_handler.handle_command(command_type, params)
	
	# Check if result is valid
	if result == null:
		return {
			"status": "error",
			"error": "Command handler returned null result"
		}
	
	if result.has("error"):
		return {"status": "error", "error": result.error}
	else:
		return {"status": "success", "result": result}
