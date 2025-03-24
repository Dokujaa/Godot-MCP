# addons/godot_mcp/ui/mcp_panel.gd
@tool
extends Control

var status_label: Label
var port_field: SpinBox
var start_button: Button
var stop_button: Button
var log_display: TextEdit

func _ready():
	# Set up references to UI elements
	status_label = $VBoxContainer/StatusPanel/StatusLabel
	port_field = $VBoxContainer/ConfigPanel/PortField
	start_button = $VBoxContainer/ButtonPanel/StartButton
	stop_button = $VBoxContainer/ButtonPanel/StopButton
	log_display = $VBoxContainer/LogPanel/LogDisplay
	
	# Initialize UI
	port_field.value = 6400  # Default port
	start_button.disabled = false
	stop_button.disabled = true
	
	# Connect signals
	start_button.pressed.connect(_on_start_button_pressed)
	stop_button.pressed.connect(_on_stop_button_pressed)
	
	# Set initial status
	update_status("Not running")
	add_log_message("Godot MCP Plugin initialized")

func update_status(status_text: String, is_error: bool = false):
	status_label.text = "Status: " + status_text
	if is_error:
		status_label.add_theme_color_override("font_color", Color(1, 0.3, 0.3))
	else:
		status_label.remove_theme_color_override("font_color")

func add_log_message(message: String):
	var timestamp = Time.get_datetime_string_from_system()
	log_display.text += "[" + timestamp + "] " + message + "\n"
	log_display.scroll_vertical = log_display.get_line_count()

func _on_start_button_pressed():
	# This function will be called from the plugin.gd script
	# when the server is actually started
	update_status("Running on port " + str(port_field.value))
	start_button.disabled = true
	stop_button.disabled = false
	add_log_message("MCP Server started on port " + str(port_field.value))

func _on_stop_button_pressed():
	# This function will be called from the plugin.gd script
	# when the server is actually stopped
	update_status("Stopped")
	start_button.disabled = false
	stop_button.disabled = true
	add_log_message("MCP Server stopped")

# Function to be called from plugin.gd when a client connects
func on_client_connected():
	add_log_message("Client connected")
	update_status("Client connected")

# Function to be called from plugin.gd when a client disconnects
func on_client_disconnected():
	add_log_message("Client disconnected")
	update_status("Running (no clients)")

# Function to be called from plugin.gd when a command is received
func on_command_received(command_type, params):
	add_log_message("Command received: " + command_type)

# Function to be called from plugin.gd when a response is sent
func on_response_sent(command_type, success):
	var status = "Success" if success else "Failed"
	add_log_message("Response sent for " + command_type + ": " + status)