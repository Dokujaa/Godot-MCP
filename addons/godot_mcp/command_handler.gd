# Structure for addons/godot_mcp/command_handler.gd
@tool
extends RefCounted

var editor_plugin: EditorPlugin = null

# Initialize with reference to the editor plugin
func set_editor_plugin(plugin):
	editor_plugin = plugin

# Main command handling function
func handle_command(command_type, params):
	match command_type:
		"GET_SCENE_INFO":
			return handle_get_scene_info()
		"OPEN_SCENE":
			return handle_open_scene(params)
		"SAVE_SCENE":
			return handle_save_scene()
		"CREATE_CHILD_OBJECT":  
			return handle_create_child_object(params)
		"NEW_SCENE":
			return handle_new_scene(params)
		"CREATE_OBJECT":
			return handle_create_object(params)
		"DELETE_OBJECT":
			return handle_delete_object(params)
		"FIND_OBJECTS_BY_NAME":
			return handle_find_objects_by_name(params)
		"GET_OBJECT_PROPERTIES":
			return handle_get_object_properties(params)
		"SET_PROPERTY":
			return handle_set_property(params)
		"SET_COLLISION_SHAPE":
			return handle_set_collision_shape(params)
		"SET_OBJECT_TRANSFORM":
			return handle_set_object_transform(params)
		"CREATE_CHILD_OBJECT":  
			return handle_create_child_object(params)
		"GET_ASSET_LIST":
			return handle_get_asset_list(params)
		"VIEW_SCRIPT":
			return handle_view_script(params)
		"SET_NESTED_PROPERTY":
			return handle_set_nested_property(params)
		"SET_PARENT":
			return handle_set_parent(params)
		"CREATE_SCRIPT":
			return handle_create_script(params)
		"UPDATE_SCRIPT":
			return handle_update_script(params)
		"LIST_SCRIPTS":
			return handle_list_scripts(params)
		"DELETE_SCRIPT":
			return handle_delete_script(params)
		"DELETE_FILE":
			return handle_delete_file(params)
		"EDITOR_CONTROL":
			return handle_editor_control(params)
		"SET_MATERIAL":
			return handle_set_material(params)
		"IMPORT_ASSET":
			return handle_import_asset(params)
		"SET_MESH":
			return handle_set_mesh(params)
		"CREATE_PREFAB":
			return handle_create_packed_scene(params)
		"INSTANTIATE_PREFAB":
			return handle_instantiate_prefab(params)
		"SHOW_MESSAGE":
			return handle_show_message(params)
		"REIMPORT_ASSET":
			return handle_reimport_asset(params)
		"IMPORT_GLB_SCENE":
			return handle_import_glb_scene(params)
		_:
			return {"error": "Unknown command type: " + command_type}

# Scene commands
func handle_get_scene_info():
	var editor_interface = editor_plugin.get_editor_interface()
	var current_scene = editor_interface.get_edited_scene_root()
	
	if current_scene == null:
		return {"error": "No scene is currently open"}
	
	var scene_info = {
		"name": current_scene.name,
		"path": current_scene.scene_file_path,
		"hierarchy": _get_hierarchy_recursive(current_scene),
		"root_objects": []
	}
	
	# Get root-level nodes
	for child in current_scene.get_children():
		scene_info.root_objects.append({
			"name": child.name,
			"type": child.get_class()
		})
	
	return scene_info

# Helper function to recursively build hierarchy
func _get_hierarchy_recursive(node):
	var hierarchy = {
		"name": node.name,
		"type": node.get_class(),
		"children": []
	}
	
	# Add transform info for spatial nodes
	if node is Node3D:
		hierarchy["transform"] = {
			"position": [node.position.x, node.position.y, node.position.z],
			"rotation": [node.rotation_degrees.x, node.rotation_degrees.y, node.rotation_degrees.z],
			"scale": [node.scale.x, node.scale.y, node.scale.z]
		}
	elif node is Node2D:
		hierarchy["transform"] = {
			"position": [node.position.x, node.position.y],
			"rotation": node.rotation_degrees,
			"scale": [node.scale.x, node.scale.y]
		}
	
	# Add script info if available
	if node.get_script():
		hierarchy["script"] = node.get_script().resource_path
	
	# Add all child nodes recursively
	for child in node.get_children():
		hierarchy["children"].append(_get_hierarchy_recursive(child))
	
	return hierarchy

func handle_open_scene(params):
	if not params.has("scene_path"):
		return {"error": "Missing required parameter: scene_path"}
	
	var scene_path = params.scene_path
	var editor_interface = editor_plugin.get_editor_interface()
	
	# Check if file exists
	if not FileAccess.file_exists(scene_path):
		return {"error": "Scene file does not exist: " + scene_path}
	
	# Save current scene if needed
	if params.get("save_current", false):
		editor_interface.save_scene()
	
	# Open the scene
	editor_interface.open_scene_from_path(scene_path)
	return {"message": "Scene opened successfully: " + scene_path}

func handle_save_scene():
	var editor_interface = editor_plugin.get_editor_interface()
	var current_scene = editor_interface.get_edited_scene_root()
	
	if current_scene == null:
		return {"error": "No scene is currently open"}
	
	editor_interface.save_scene()
	return {"message": "Scene saved successfully: " + current_scene.scene_file_path}

func handle_new_scene(params):
	if not params.has("scene_path"):
		return {"error": "Missing required parameter: scene_path"}
	
	var scene_path = params.scene_path
	var editor_interface = editor_plugin.get_editor_interface()
	
	# Check if file exists and handle overwrite
	if FileAccess.file_exists(scene_path) and not params.get("overwrite", false):
		return {"error": "Scene file already exists. Use overwrite=true to replace it."}
	
	# Create directory if needed
	var directory = scene_path.get_base_dir()
	if not DirAccess.dir_exists_absolute(directory):
		var error = DirAccess.make_dir_recursive_absolute(directory)
		if error != OK:
			return {"error": "Failed to create directory: " + directory}
	
	# Create a new scene with a Node as root
	var root_node = Node.new()
	root_node.name = scene_path.get_file().get_basename()
	
	# Create a packed scene and save it
	var packed_scene = PackedScene.new()
	var result = packed_scene.pack(root_node)
	if result != OK:
		return {"error": "Failed to pack scene: " + str(result)}
	
	var error = ResourceSaver.save(packed_scene, scene_path)
	if error != OK:
		return {"error": "Failed to save new scene: " + str(error)}
	
	# Open the newly created scene
	editor_interface.open_scene_from_path(scene_path)
	
	return {"message": "New scene created successfully: " + scene_path}

# Object commands
func handle_create_object(params):
	var type = params.get("type", "EMPTY")
	var name = params.get("name", "")
	var location = params.get("location", [0, 0, 0])
	var rotation = params.get("rotation", [0, 0, 0])
	var scale = params.get("scale", [1, 1, 1])
	var replace_if_exists = params.get("replace_if_exists", false)
	
	var editor_interface = editor_plugin.get_editor_interface()
	var current_scene = editor_interface.get_edited_scene_root()
	
	if current_scene == null:
		return {"error": "No scene is currently open"}
	
	# Check if name already exists and handle replacement
	if name != "":
		var existing_node = current_scene.find_child(name, true, false)
		if existing_node and not replace_if_exists:
			return {"error": "Node with name '" + name + "' already exists. Use replace_if_exists=true to replace it."}
		elif existing_node and replace_if_exists:
			existing_node.queue_free()
	
	# Create the node based on type (case-insensitive)
	var node
	var upper_type = type.to_upper()
	
	# Handle common 3D node types
	match upper_type:
		"NODE", "EMPTY":
			node = Node3D.new()
		"NODE3D":
			node = Node3D.new()
		"SPATIAL": # For compatibility with Godot 3.x terminology
			node = Node3D.new()
		"MESH", "MESHINSTANCE3D":
			node = MeshInstance3D.new()
		"CUBE", "BOX":
			node = MeshInstance3D.new()
			node.mesh = BoxMesh.new()
		"SPHERE":
			node = MeshInstance3D.new()
			node.mesh = SphereMesh.new()
		"CYLINDER":
			node = MeshInstance3D.new()
			node.mesh = CylinderMesh.new()
		"PLANE":
			node = MeshInstance3D.new()
			node.mesh = PlaneMesh.new()
		"CAMERA", "CAMERA3D":
			node = Camera3D.new()
		"LIGHT", "DIRECTIONALLIGHT", "DIRECTIONALLIGHT3D":
			node = DirectionalLight3D.new()
		"SPOTLIGHT", "SPOTLIGHT3D":
			node = SpotLight3D.new()
		"OMNILIGHT", "OMNILIGHT3D":
			node = OmniLight3D.new()
		"RIGIDBODY", "RIGIDBODY3D":
			node = RigidBody3D.new()
		"STATICBODY", "STATICBODY3D":
			node = StaticBody3D.new()
		"CHARACTERBODY", "CHARACTERBODY3D":
			node = CharacterBody3D.new()
		"AREA", "AREA3D":
			node = Area3D.new()
		"COLLISION", "COLLISIONSHAPE3D":
			node = CollisionShape3D.new()
			# Add a default sphere shape
			node.shape = SphereShape3D.new()
		
		# Handle common 2D node types
		"NODE2D":
			node = Node2D.new()
		"SPRITE", "SPRITE2D":
			node = Sprite2D.new()
		"CAMERA2D":
			node = Camera2D.new()
		"AREA2D":
			node = Area2D.new()
		"COLLISION2D", "COLLISIONSHAPE2D":
			node = CollisionShape2D.new()
			# Add a default circle shape
			node.shape = CircleShape2D.new()
		"RIGIDBODY2D":
			node = RigidBody2D.new()
		"STATICBODY2D":
			node = StaticBody2D.new()
		"CHARACTERBODY2D":
			node = CharacterBody2D.new()
		
		# Handle UI node types
		"CONTROL":
			node = Control.new()
		"PANEL":
			node = Panel.new()
		"BUTTON":
			node = Button.new()
		"LABEL":
			node = Label.new()
		"LINEEDIT":
			node = LineEdit.new()
		"TEXTEDIT":
			node = TextEdit.new()
		"CONTAINER":
			node = Container.new()
		"VBOX", "VBOXCONTAINER":
			node = VBoxContainer.new()
		"HBOX", "HBOXCONTAINER":
			node = HBoxContainer.new()
		_:
			# Try to create the node directly by class name using ClassDB
			if ClassDB.class_exists(type) and ClassDB.can_instantiate(type):
				node = ClassDB.instantiate(type)
			else:
				return {"error": "Unsupported object type: " + type}
	
	# Set node name if provided
	if name != "":
		node.name = name
	
	# Add to scene
	current_scene.add_child(node)
	node.owner = current_scene
	
	# Set transform for Node3D or Node2D objects
	if node is Node3D:
		node.position = Vector3(location[0], location[1], location[2])
		node.rotation_degrees = Vector3(rotation[0], rotation[1], rotation[2])
		node.scale = Vector3(scale[0], scale[1], scale[2])
	elif node is Node2D:
		node.position = Vector2(location[0], location[1])
		node.rotation_degrees = rotation[0]
		node.scale = Vector2(scale[0], scale[1])
	
	return {
		"name": node.name,
		"type": node.get_class(),
		"path": current_scene.get_path_to(node)
	}
	
	
func handle_delete_object(params):
	if not params.has("name"):
		return {"error": "Missing required parameter: name"}
	
	var name_or_path = params.name
	var editor_interface = editor_plugin.get_editor_interface()
	var current_scene = editor_interface.get_edited_scene_root()
	
	if current_scene == null:
		return {"error": "No scene is currently open"}
	
	# Find node by name or path
	var node = null
	
	# Check if it's a path (contains /)
	if "/" in name_or_path:
		# Try direct path lookup first
		node = current_scene.get_node_or_null(name_or_path)
		
		# If that fails, try with leading slash
		if not node and not name_or_path.begins_with("/"):
			node = current_scene.get_node_or_null("/" + name_or_path)
			
		# If still not found, try parsing the path components
		if not node:
			var parts = name_or_path.split("/")
			var current = current_scene
			
			for part in parts:
				if part == "":
					continue
					
				var found = false
				for child in current.get_children():
					if child.name == part:
						current = child
						found = true
						break
						
				if not found:
					# Try searching recursively for this part
					var found_node = current.find_child(part, true, false)
					if found_node:
						current = found_node
					else:
						# Part not found, path is invalid
						return {"error": "Could not find part '" + part + "' in path: " + name_or_path}
			
			node = current
	else:
		# Simple name lookup for non-path names
		node = current_scene.find_child(name_or_path, true, false)
	
	if not node:
		return {"error": "Node not found: " + name_or_path}
	
	# Store the node's path for the response before deleting
	var node_path = current_scene.get_path_to(node)
	var node_type = node.get_class()
	
	# Delete the node
	node.queue_free()
	
	return {
		"message": "Node deleted: " + name_or_path,
		"path": node_path,
		"type": node_type
	}
#func handle_delete_object(params):
	#if not params.has("name"):
		#return {"error": "Missing required parameter: name"}
	#
	#var name = params.name
	#var editor_interface = editor_plugin.get_editor_interface()
	#var current_scene = editor_interface.get_edited_scene_root()
	#
	#if current_scene == null:
		#return {"error": "No scene is currently open"}
	#
	## Find node by name
	#var node = current_scene.find_child(name, true, false)
	#if not node:
		#return {"error": "Node not found: " + name}
	#
	## Delete the node
	#node.queue_free()
	#return {"message": "Node deleted: " + name}

func handle_find_objects_by_name(params):
	if not params.has("name"):
		return {"error": "Missing required parameter: name"}
	
	var search_name = params.name
	var editor_interface = editor_plugin.get_editor_interface()
	var current_scene = editor_interface.get_edited_scene_root()
	
	if current_scene == null:
		return {"error": "No scene is currently open"}
	
	var objects = []
	var nodes = _find_nodes_by_name(current_scene, search_name)
	
	for node in nodes:
		objects.append({
			"name": node.name,
			"path": _get_node_path(node),
			"type": node.get_class()
		})
	
	return {"objects": objects}

# Helper function to find nodes recursively
func _find_nodes_by_name(root, search_name):
	var result = []
	
	if search_name in root.name:
		result.append(root)
	
	for child in root.get_children():
		result.append_array(_find_nodes_by_name(child, search_name))
	
	return result

# Helper function to get a node's path relative to the scene root
func _get_node_path(node):
	var current_scene = editor_plugin.get_editor_interface().get_edited_scene_root()
	if current_scene:
		return current_scene.get_path_to(node)
	return node.get_path()

func handle_get_object_properties(params):
	if not params.has("name"):
		return {"error": "Missing required parameter: name"}
	
	var name_or_path = params.name
	var editor_interface = editor_plugin.get_editor_interface()
	var current_scene = editor_interface.get_edited_scene_root()
	
	if current_scene == null:
		return {"error": "No scene is currently open"}
	
	var node
	
	# Check if we're dealing with a path or just a name
	if "/" in name_or_path:
		# It's a path, try to get the node using get_node
		node = current_scene.get_node_or_null(name_or_path)
		
		# If that fails, try with NodePath
		if not node:
			var node_path = NodePath(name_or_path)
			node = current_scene.get_node_or_null(node_path)
		
		# Try finding from root with a leading slash
		if not node and not name_or_path.begins_with("/"):
			node = current_scene.get_node_or_null("/" + name_or_path)
	else:
		# It's just a name, use find_child (which searches recursively)
		node = current_scene.find_child(name_or_path, true, false)
	
	if not node:
		return {"error": "Node not found: " + name_or_path}
	
	# Get properties
	var properties = {
		"name": node.name,
		"type": node.get_class(),
		"path": current_scene.get_path_to(node),
		"visible": node.visible if "visible" in node else true,
		"components": []
	}
	
	# Handle transform properties for 3D nodes
	if node is Node3D:
		properties["transform"] = {
			"position": [node.position.x, node.position.y, node.position.z],
			"rotation": [node.rotation_degrees.x, node.rotation_degrees.y, node.rotation_degrees.z],
			"scale": [node.scale.x, node.scale.y, node.scale.z]
		}
	elif node is Node2D:
		properties["transform"] = {
			"position": [node.position.x, node.position.y],
			"rotation": node.rotation_degrees,
			"scale": [node.scale.x, node.scale.y]
		}
	
	# Get node properties and components
	if node.get_script():
		properties["components"].append({
			"type": "Script",
			"path": node.get_script().resource_path
		})
	
	# Get children information
	properties["children"] = []
	for child in node.get_children():
		properties["children"].append({
			"name": child.name,
			"type": child.get_class(),
			"path": current_scene.get_path_to(child)
		})
	
	# Get parent information
	var parent = node.get_parent()
	if parent and parent != current_scene:
		properties["parent"] = {
			"name": parent.name,
			"type": parent.get_class(),
			"path": current_scene.get_path_to(parent)
		}
	
	return properties

func handle_set_object_transform(params):
	if not params.has("name"):
		return {"error": "Missing required parameter: name"}
	
	var name = params.name
	var editor_interface = editor_plugin.get_editor_interface()
	var current_scene = editor_interface.get_edited_scene_root()
	
	if current_scene == null:
		return {"error": "No scene is currently open"}
	
	# Find node by name
	var node = current_scene.find_child(name, true, false)
	if not node:
		return {"error": "Node not found: " + name}
	
	# Check if node is 3D
	if not node is Node3D:
		return {"error": "Node is not a 3D node: " + name}
	
	# Set transform properties
	if params.has("location"):
		var loc = params.location
		node.position = Vector3(loc[0], loc[1], loc[2])
	
	if params.has("rotation"):
		var rot = params.rotation
		node.rotation_degrees = Vector3(rot[0], rot[1], rot[2])
	
	if params.has("scale"):
		var scale = params.scale
		node.scale = Vector3(scale[0], scale[1], scale[2])
	
	return {"message": "Transform updated for node: " + name}

# Asset commands
func handle_get_asset_list(params):
	var type = params.get("type", "")
	var search_pattern = params.get("search_pattern", "*")
	var folder = params.get("folder", "res://")
	
	var assets = []
	var dir = DirAccess.open(folder)
	
	if dir == null:
		return {"error": "Unable to access directory: " + folder}
	
	dir.list_dir_begin()
	var file_name = dir.get_next()
	
	while file_name != "":
		var full_path = folder.path_join(file_name)
		
		if dir.current_is_dir():
			# Handle directories if needed
			pass
		else:
			# Check if it matches the search pattern
			if search_pattern == "*" or search_pattern in file_name:
				# Check type if specified
				var add_file = true
				if type != "":
					# Determine file type based on extension
					var extension = file_name.get_extension().to_lower()
					match type.to_lower():
						"scene":
							add_file = extension == "tscn" or extension == "scn"
						"script":
							add_file = extension == "gd" or extension == "cs"
						"texture":
							add_file = extension in ["png", "jpg", "jpeg", "webp"]
						"material":
							add_file = extension == "material" or extension == "tres"
						"prefab", "packedscene":
							add_file = extension == "tscn" or extension == "scn"
				
				if add_file:
					assets.append({
						"name": file_name,
						"path": full_path,
						"type": _get_resource_type(full_path)
					})
		
		file_name = dir.get_next()
	
	dir.list_dir_end()
	return {"assets": assets}

# Helper function to determine resource type
func _get_resource_type(path):
	var extension = path.get_extension().to_lower()
	match extension:
		"tscn", "scn":
			return "PackedScene"
		"gd":
			return "GDScript"
		"cs":
			return "CSharpScript"
		"png", "jpg", "jpeg", "webp":
			return "Texture"
		"material", "tres":
			return "Material"
		"wav", "mp3", "ogg":
			return "AudioStream"
		_:
			return "Resource"

# Script commands
func handle_view_script(params):
	if not params.has("script_path"):
		return {"error": "Missing required parameter: script_path"}
	
	var script_path = params.script_path
	var require_exists = params.get("require_exists", true)
	
	if not FileAccess.file_exists(script_path):
		if require_exists:
			return {"error": "Script file does not exist: " + script_path}
		else:
			return {"exists": false, "message": "Script file does not exist: " + script_path}
	
	var file = FileAccess.open(script_path, FileAccess.READ)
	if file == null:
		return {"error": "Failed to open script file: " + script_path}
	
	var content = file.get_as_text()
	return {"exists": true, "content": content}

func handle_create_script(params):
	if not params.has("script_name"):
		return {"error": "Missing required parameter: script_name"}
	
	var script_name = params.script_name
	var script_type = params.get("script_type", "Node")
	var nam = params.get("namespace", "")
	var script_folder = params.get("script_folder", "res://scripts")
	var overwrite = params.get("overwrite", false)
	var content = params.get("content", "")
	
	# Ensure script has .gd extension
	if not script_name.ends_with(".gd"):
		script_name += ".gd"
	
	# Create full script path
	var script_path = script_folder.path_join(script_name)
	
	# Check if directory exists, create if needed
	if not DirAccess.dir_exists_absolute(script_folder):
		var error = DirAccess.make_dir_recursive_absolute(script_folder)
		if error != OK:
			return {"error": "Failed to create script directory: " + script_folder}
	
	# Check if script already exists
	if FileAccess.file_exists(script_path) and not overwrite:
		return {"error": "Script already exists. Use overwrite=true to replace it."}
	
	# Create script content if not provided
	if content == "":
		content = _generate_script_template(script_type, nam)
	
	# Write script file
	var file = FileAccess.open(script_path, FileAccess.WRITE)
	if file == null:
		return {"error": "Failed to create script file: " + script_path}
	
	file.store_string(content)
	
	return {"message": "Script created successfully: " + script_path}

# Helper function to generate script template
func _generate_script_template(node_type, nam):
	var template = ""
	
	# Add class_name if namespace is provided
	if nam != "":
		template += "class_name " + nam + "\n\n"
	
	# Add extends
	template += "extends " + node_type + "\n\n"
	
	# Add basic structure
	template += "# Properties\n\n"
	template += "# Called when the node enters the scene tree\n"
	template += "func _ready():\n"
	template += "\tpass\n\n"
	template += "# Called every frame\n"
	template += "func _process(delta):\n"
	template += "\tpass\n"
	
	return template

func handle_update_script(params):
	if not params.has("script_path") or not params.has("content"):
		return {"error": "Missing required parameters: script_path and content"}
	
	var script_path = params.script_path
	var content = params.content
	var create_if_missing = params.get("create_if_missing", false)
	var create_folder_if_missing = params.get("create_folder_if_missing", false)
	
	# Check if script exists
	if not FileAccess.file_exists(script_path):
		if not create_if_missing:
			return {"error": "Script file does not exist: " + script_path}
		
		# Create directory if needed
		var directory = script_path.get_base_dir()
		if create_folder_if_missing and not DirAccess.dir_exists_absolute(directory):
			var dir_error = DirAccess.make_dir_recursive_absolute(directory)
			if dir_error != OK:
				return {"error": "Failed to create directory: " + directory}
	
	# Write script content
	var file = FileAccess.open(script_path, FileAccess.WRITE)
	if file == null:
		return {"error": "Failed to open script file for writing: " + script_path}
	
	file.store_string(content)
	
	return {"message": "Script updated successfully: " + script_path}

func handle_list_scripts(params):
	var folder_path = params.get("folder_path", "res://")
	
	var scripts = []
	var dir = DirAccess.open(folder_path)
	
	if dir == null:
		return {"error": "Unable to access directory: " + folder_path}
	
	dir.list_dir_begin()
	var file_name = dir.get_next()
	
	while file_name != "":
		if not dir.current_is_dir():
			var extension = file_name.get_extension().to_lower()
			if extension == "gd" or extension == "cs":
				scripts.append(folder_path.path_join(file_name))
		
		file_name = dir.get_next()
	
	dir.list_dir_end()
	return {"scripts": scripts}

# Editor control commands
func handle_editor_control(params):
	if not params.has("command"):
		return {"error": "Missing required parameter: command"}
	
	var command = params.command
	var editor_interface = editor_plugin.get_editor_interface()
	
	match command:
		"PLAY":
			editor_interface.play_main_scene()
			return {"message": "Started playing the main scene"}
		"STOP":
			editor_interface.stop_playing_scene()
			return {"message": "Stopped playing the scene"}
		"SAVE":
			editor_interface.save_scene()
			return {"message": "Scene saved"}
		"READ_CONSOLE":
			# Godot doesn't have a direct API for reading console output
			return {"message": "Console reading not implemented in Godot"}
		_:
			return {"error": "Unknown editor command: " + command}

# Material commands
func handle_set_material(params):
	if not params.has("object_name"):
		return {"error": "Missing required parameter: object_name"}
	
	var object_name = params.object_name
	var material_name = params.get("material_name", "")
	var color = params.get("color", [1.0, 1.0, 1.0, 1.0])
	var create_if_missing = params.get("create_if_missing", true)
	
	print("handle_set_material called for node: ", object_name, " color: ", color)
	
	var editor_interface = editor_plugin.get_editor_interface()
	var current_scene = editor_interface.get_edited_scene_root()
	
	if current_scene == null:
		return {"error": "No scene is currently open"}
	
	# Find node using the improved node lookup
	var node = _find_node(current_scene, object_name)
	if not node:
		return {"error": "Node not found: " + object_name}
	
	print("Node found: ", node.name, " type: ", node.get_class())
	
	# Check if node can have materials
	if not (node is MeshInstance3D or node is CSGShape3D):
		return {"error": "Node does not support materials: " + object_name}
	
	var material
	
	# Create or load material
	if material_name != "":
		var material_path = "res://materials/" + material_name + ".material"
		
		if FileAccess.file_exists(material_path):
			# Load existing material
			material = load(material_path)
		elif create_if_missing:
			# Create directory if needed
			if not DirAccess.dir_exists_absolute("res://materials"):
				DirAccess.make_dir_recursive_absolute("res://materials")
			
			# Create new material
			material = StandardMaterial3D.new()
			
			# Set color
			if color.size() >= 3:
				var albedo_color = Color(color[0], color[1], color[2])
				if color.size() >= 4:
					albedo_color.a = color[3]
				material.albedo_color = albedo_color
			
			# Save material
			var error = ResourceSaver.save(material, material_path)
			if error != OK:
				return {"error": "Failed to save material: " + str(error)}
		else:
			return {"error": "Material not found and create_if_missing is false"}
	else:
		# Create instance material
		material = StandardMaterial3D.new()
		
		# Set color
		if color.size() >= 3:
			var albedo_color = Color(color[0], color[1], color[2])
			if color.size() >= 4:
				albedo_color.a = color[3]
			material.albedo_color = albedo_color
	
	# Apply material
	if node is MeshInstance3D:
		node.material_override = material
	elif node is CSGShape3D:
		node.material = material
	
	if material_name != "":
		return {
			"material_name": material_name,
			"path": "res://materials/" + material_name + ".material",
			"message": "Applied shared material to " + object_name
		}
	else:
		return {
			"material_name": "instance_material",
			"message": "Applied instance material to " + object_name
		}

# Asset import
func handle_import_asset(params):
	if not params.has("source_path") or not params.has("target_path"):
		return {"error": "Missing required parameters: source_path and target_path"}
	
	var source_path = params.source_path
	var target_path = params.target_path
	var overwrite = params.get("overwrite", false)
	
	# Ensure target_path starts with res://
	if not target_path.begins_with("res://"):
		target_path = "res://" + target_path
	
	# Check if source file exists
	if not FileAccess.file_exists(source_path):
		return {"error": "Source file does not exist: " + source_path}
	
	# Check if target file exists
	if FileAccess.file_exists(target_path) and not overwrite:
		return {"error": "Target file already exists. Use overwrite=true to replace it."}
	
	# Create target directory if needed
	var target_dir = target_path.get_base_dir()
	if not DirAccess.dir_exists_absolute(target_dir):
		var dir_error = DirAccess.make_dir_recursive_absolute(target_dir)
		if dir_error != OK:
			return {"error": "Failed to create target directory: " + target_dir}
	
	# Copy the file
	var source_file = FileAccess.open(source_path, FileAccess.READ)
	if source_file == null:
		return {"error": "Failed to open source file: " + source_path}
	
	var target_file = FileAccess.open(target_path, FileAccess.WRITE)
	if target_file == null:
		return {"error": "Failed to create target file: " + target_path}
	
	target_file.store_buffer(source_file.get_buffer(source_file.get_length()))
	
	return {
		"success": true,
		"message": "Asset imported successfully: " + target_path
	}

func handle_create_packed_scene(params):
	"""Create a packed scene (prefab) from an existing node."""
	if not params.has("object_name") or not params.has("prefab_path"):
		return {"error": "Missing required parameters: object_name and prefab_path"}
	
	var object_name = params.object_name
	var prefab_path = params.prefab_path
	var overwrite = params.get("overwrite", false)
	
	# Ensure prefab_path starts with res://
	if not prefab_path.begins_with("res://"):
		prefab_path = "res://" + prefab_path
	
	# Ensure it has .tscn extension
	if not prefab_path.ends_with(".tscn"):
		prefab_path += ".tscn"
	
	# Check if file exists and handle overwrite
	if FileAccess.file_exists(prefab_path) and not overwrite:
		return {"error": "Packed scene file already exists. Use overwrite=true to replace it."}
	
	var editor_interface = editor_plugin.get_editor_interface()
	var current_scene = editor_interface.get_edited_scene_root()
	
	if current_scene == null:
		return {"error": "No scene is currently open"}
	
	# Find node by name
	var node = current_scene.find_child(object_name, true, false)
	if not node:
		return {"error": "Node not found: " + object_name}
	
	# Create directory if needed
	var directory = prefab_path.get_base_dir()
	if not DirAccess.dir_exists_absolute(directory):
		var dir_error = DirAccess.make_dir_recursive_absolute(directory)
		if dir_error != OK:
			return {"error": "Failed to create directory: " + directory}
	
	# Create packed scene
	var packed_scene = PackedScene.new()
	var result = packed_scene.pack(node)
	if result != OK:
		return {"error": "Failed to pack scene: " + str(result)}
	
	# Save packed scene
	result = ResourceSaver.save(packed_scene, prefab_path)
	if result != OK:
		return {"error": "Failed to save packed scene: " + str(result)}
	
	return {
		"success": true,
		"path": prefab_path,
		"message": "Packed scene created successfully from " + object_name
	}

func handle_instantiate_prefab(params):
	"""Instantiate a packed scene (prefab) into the current scene."""
	if not params.has("prefab_path"):
		return {"error": "Missing required parameter: prefab_path"}
	
	var prefab_path = params.prefab_path
	var position_x = params.get("position_x", 0.0)
	var position_y = params.get("position_y", 0.0)
	var position_z = params.get("position_z", 0.0)
	var rotation_x = params.get("rotation_x", 0.0)
	var rotation_y = params.get("rotation_y", 0.0)
	var rotation_z = params.get("rotation_z", 0.0)
	
	# Ensure prefab_path starts with res://
	if not prefab_path.begins_with("res://"):
		prefab_path = "res://" + prefab_path
	
	# Check if file exists
	if not FileAccess.file_exists(prefab_path):
		return {"error": "Packed scene file does not exist: " + prefab_path}
	
	var editor_interface = editor_plugin.get_editor_interface()
	var current_scene = editor_interface.get_edited_scene_root()
	
	if current_scene == null:
		return {"error": "No scene is currently open"}
	
	# Load the packed scene
	var scene_resource = load(prefab_path)
	if not scene_resource is PackedScene:
		return {"error": "Failed to load packed scene: " + prefab_path}
	
	# Instantiate the scene
	var instance = scene_resource.instantiate()
	if not instance:
		return {"error": "Failed to instantiate packed scene"}
	
	# Add to the current scene
	current_scene.add_child(instance)
	instance.owner = current_scene
	
	# Set transform if it's a spatial node
	if instance is Node3D:
		instance.position = Vector3(position_x, position_y, position_z)
		instance.rotation_degrees = Vector3(rotation_x, rotation_y, rotation_z)
	
	return {
		"success": true,
		"instance_name": instance.name,
		"message": "Packed scene instantiated successfully"
	}
func handle_set_property(params):
	if not params.has("node_name") or not params.has("property_name") or not params.has("value"):
		return {"error": "Missing required parameters: node_name, property_name, and value"}
	
	var node_name = params.node_name
	var property_name = params.property_name
	var value = params.value
	var force_type = params.get("force_type", "")
	
	print("handle_set_property called with node_name: ", node_name, " property_name: ", property_name, " value: ", value)
	
	var editor_interface = editor_plugin.get_editor_interface()
	var current_scene = editor_interface.get_edited_scene_root()
	
	if current_scene == null:
		return {"error": "No scene is currently open"}
	
	# Find node by name or path
	var node = null
	
	# Check if it's a path (contains /)
	if "/" in node_name:
		# Try direct path lookup first
		node = current_scene.get_node_or_null(node_name)
		if not node:
			# Try as relative path
			if not node_name.begins_with("/"):
				node = current_scene.get_node_or_null("/" + node_name)
	else:
		# Simple name lookup
		node = current_scene.find_child(node_name, true, false)
	
	if node:
		print("Node found: ", node.name, " of type: ", node.get_class())
	else:
		print("Node not found: ", node_name)
		return {"error": "Node not found: " + node_name}
	
	# Handle special properties
	if property_name == "script":
		# Check if script file exists
		if not FileAccess.file_exists(value):
			return {"error": "Script file not found: " + value}
		
		# Try to load the script
		var script_resource = load(value)
		if not script_resource:
			return {"error": "Failed to load script: " + value}
		
		if not script_resource is GDScript:
			return {"error": "Resource is not a GDScript: " + value}
		
		# Set the script
		node.set_script(script_resource)
		return {"message": "Script set on node '" + node_name + "': " + value}
	
	# Handle other special properties
	if property_name == "visible":
		node.visible = bool(value)
		return {"message": "Property set: visible = " + str(bool(value))}
	
	if property_name == "name":
		# Check if name is already taken
		var existing = current_scene.find_child(str(value), true, false)
		if existing != null and existing != node:
			return {"error": "Name already in use by another node"}
		node.name = str(value)
		return {"message": "Node renamed to: " + str(value)}
	
	# Handle property paths (e.g., "position:x")
	var parts = property_name.split(":")
	if parts.size() == 2:
		var base_property = parts[0]
		var sub_property = parts[1]
		
		if base_property in node:
			var base_value = node.get(base_property)
			
			# Handle different vector types
			if base_value is Vector2 or base_value is Vector3 or base_value is Color:
				if sub_property in ["x", "y", "z", "r", "g", "b", "a"]:
					# Safety check for Vector2 which doesn't have z
					if base_value is Vector2 and sub_property == "z":
						return {"error": "Vector2 doesn't have a z component"}
					
					# Safety check for components that don't exist
					if sub_property == "z" and not (base_value is Vector3):
						return {"error": "Property doesn't have a z component"}
					
					if sub_property in ["r", "g", "b", "a"] and not (base_value is Color):
						return {"error": "Only Color has r, g, b, a components"}
					
					# Convert value to float for vector components
					var float_value
					if typeof(value) == TYPE_STRING:
						float_value = float(value)
					else:
						float_value = float(value)
					
					# Set the appropriate component
					match sub_property:
						"x":
							base_value.x = float_value
						"y":
							base_value.y = float_value
						"z":
							base_value.z = float_value
						"r":
							base_value.r = float_value
						"g":
							base_value.g = float_value
						"b":
							base_value.b = float_value
						"a":
							base_value.a = float_value
					
					# Set the modified vector back to the node
					node.set(base_property, base_value)
					return {"message": "Property set: " + property_name + " = " + str(float_value)}
			
			return {"error": "Unable to set sub-property: " + property_name}
	
	# Handle regular properties
	if not property_name in node:
		return {"error": "Property not found on node: " + property_name}
	
	# Get the current property value to determine its type
	var current_value = node.get(property_name)
	print("Current value type: ", typeof(current_value))
	
	var converted_value = value
	
	# If force_type is specified, use that for conversion
	if force_type != "":
		match force_type:
			"bool":
				if typeof(value) == TYPE_STRING:
					converted_value = (value.to_lower() == "true")
				else:
					converted_value = bool(value)
			"int":
				converted_value = int(value)
			"float":
				converted_value = float(value)
			"string":
				converted_value = str(value)
			"Vector2":
				if typeof(value) == TYPE_ARRAY and value.size() >= 2:
					converted_value = Vector2(float(value[0]), float(value[1]))
			"Vector3":
				if typeof(value) == TYPE_ARRAY and value.size() >= 3:
					converted_value = Vector3(float(value[0]), float(value[1]), float(value[2]))
			"Color":
				if typeof(value) == TYPE_ARRAY:
					if value.size() >= 4:
						converted_value = Color(float(value[0]), float(value[1]), float(value[2]), float(value[3]))
					elif value.size() >= 3:
						converted_value = Color(float(value[0]), float(value[1]), float(value[2]))
	else:
		# Try to convert the value to match the current property type
		match typeof(current_value):
			TYPE_BOOL:
				if typeof(value) == TYPE_STRING:
					converted_value = (value.to_lower() == "true")
				else:
					converted_value = bool(value)
			TYPE_INT:
				converted_value = int(value)
			TYPE_FLOAT:
				converted_value = float(value)
			TYPE_STRING:
				converted_value = str(value)
			TYPE_VECTOR2:
				if typeof(value) == TYPE_ARRAY and value.size() >= 2:
					converted_value = Vector2(float(value[0]), float(value[1]))
			TYPE_VECTOR3:
				if typeof(value) == TYPE_ARRAY and value.size() >= 3:
					converted_value = Vector3(float(value[0]), float(value[1]), float(value[2]))
			TYPE_COLOR:
				if typeof(value) == TYPE_ARRAY:
					if value.size() >= 4:
						converted_value = Color(float(value[0]), float(value[1]), float(value[2]), float(value[3]))
					elif value.size() >= 3:
						converted_value = Color(float(value[0]), float(value[1]), float(value[2]))
	
	print("Converted value: ", converted_value, " of type: ", typeof(converted_value))
	
	# Try to set the property
	var previous_value = node.get(property_name)
	
	# Use set to safely call the setter
	var error = null
	node.set(property_name, converted_value)
	
	# Check if the property actually changed
	var new_value = node.get(property_name)
	# Handle type-safe comparison - don't compare different types directly
	var values_different = false
	if typeof(new_value) == typeof(converted_value):
		values_different = (new_value != converted_value)
	else:
		# Different types means they're different values
		values_different = true
	
	if new_value == previous_value and values_different:
		return {"warning": "Property might be read-only or conversion failed: " + property_name, "previous_value": previous_value, "attempted_value": converted_value}
	
	return {"message": "Property set: " + property_name + " = " + str(converted_value)}


#func handle_set_property(params):
	#if not params.has("node_name") or not params.has("property_name") or not params.has("value"):
		#return {"error": "Missing required parameters: node_name, property_name, and value"}
	#
	#var node_name = params.node_name
	#var property_name = params.property_name
	#var value = params.value
	#var force_type = params.get("force_type", "")
	#
	#var editor_interface = editor_plugin.get_editor_interface()
	#var current_scene = editor_interface.get_edited_scene_root()
	#
	#if current_scene == null:
		#return {"error": "No scene is currently open"}
	#
	## Find node by name
	#var node = current_scene.find_child(node_name, true, false)
	#if not node:
		#return {"error": "Node not found: " + node_name}
	#
	## Handle special properties
	#if property_name == "script":
		## Check if script file exists
		#if not FileAccess.file_exists(value):
			#return {"error": "Script file not found: " + value}
		#
		## Try to load the script
		#var script_resource = load(value)
		#if not script_resource:
			#return {"error": "Failed to load script: " + value}
		#
		#if not script_resource is GDScript:
			#return {"error": "Resource is not a GDScript: " + value}
		#
		## Set the script
		#node.set_script(script_resource)
		#return {"message": "Script set on node '" + node_name + "': " + value}
	#
	## Handle other special properties
	#if property_name == "visible":
		#node.visible = bool(value)
		#return {"message": "Property set: visible = " + str(bool(value))}
	#
	#if property_name == "name":
		## Check if name is already taken
		#var existing = current_scene.find_child(str(value), true, false)
		#if existing != null and existing != node:
			#return {"error": "Name already in use by another node"}
		#node.name = str(value)
		#return {"message": "Node renamed to: " + str(value)}
	#
	## Handle property paths (e.g., "position:x")
	#var parts = property_name.split(":")
	#if parts.size() == 2:
		#var base_property = parts[0]
		#var sub_property = parts[1]
		#
		#if base_property in node:
			#var base_value = node.get(base_property)
			#
			## Handle different vector types
			#if base_value is Vector2 or base_value is Vector3 or base_value is Color:
				#if sub_property in ["x", "y", "z", "r", "g", "b", "a"]:
					## Safety check for Vector2 which doesn't have z
					#if base_value is Vector2 and sub_property == "z":
						#return {"error": "Vector2 doesn't have a z component"}
					#
					## Safety check for components that don't exist
					#if sub_property == "z" and not (base_value is Vector3):
						#return {"error": "Property doesn't have a z component"}
					#
					#if sub_property in ["r", "g", "b", "a"] and not (base_value is Color):
						#return {"error": "Only Color has r, g, b, a components"}
					#
					## Convert value to float for vector components
					#var float_value
					#if typeof(value) == TYPE_STRING:
						#float_value = float(value)
					#else:
						#float_value = float(value)
					#
					## Set the appropriate component
					#match sub_property:
						#"x": base_value.x = float_value
						#"y": base_value.y = float_value
						#"z": base_value.z = float_value
						#"r": base_value.r = float_value
						#"g": base_value.g = float_value
						#"b": base_value.b = float_value
						#"a": base_value.a = float_value
					#
					## Set the modified vector back to the node
					#node.set(base_property, base_value)
					#return {"message": "Property set: " + property_name + " = " + str(float_value)}
			#
			#return {"error": "Unable to set sub-property: " + property_name}
	#
	## Handle regular properties
	#if not property_name in node:
		#return {"error": "Property not found on node: " + property_name}
	#
	## Get the current property value to determine its type
	#var current_value = node.get(property_name)
	#var converted_value = value
	#
	## If force_type is specified, use that for conversion
	#if force_type != "":
		#match force_type:
			#"bool":
				#if typeof(value) == TYPE_STRING:
					#converted_value = (value.to_lower() == "true")
				#else:
					#converted_value = bool(value)
			#"int":
				#converted_value = int(value)
			#"float":
				#converted_value = float(value)
			#"string":
				#converted_value = str(value)
			#"Vector2":
				#if typeof(value) == TYPE_ARRAY and value.size() >= 2:
					#converted_value = Vector2(float(value[0]), float(value[1]))
			#"Vector3":
				#if typeof(value) == TYPE_ARRAY and value.size() >= 3:
					#converted_value = Vector3(float(value[0]), float(value[1]), float(value[2]))
			#"Color":
				#if typeof(value) == TYPE_ARRAY:
					#if value.size() >= 4:
						#converted_value = Color(float(value[0]), float(value[1]), float(value[2]), float(value[3]))
					#elif value.size() >= 3:
						#converted_value = Color(float(value[0]), float(value[1]), float(value[2]))
	#else:
		## Try to convert the value to match the current property type
		#match typeof(current_value):
			#TYPE_BOOL:
				#if typeof(value) == TYPE_STRING:
					#converted_value = (value.to_lower() == "true")
				#else:
					#converted_value = bool(value)
			#TYPE_INT:
				#converted_value = int(value)
			#TYPE_FLOAT:
				#converted_value = float(value)
			#TYPE_STRING:
				#converted_value = str(value)
			#TYPE_VECTOR2:
				#if typeof(value) == TYPE_ARRAY and value.size() >= 2:
					#converted_value = Vector2(float(value[0]), float(value[1]))
			#TYPE_VECTOR3:
				#if typeof(value) == TYPE_ARRAY and value.size() >= 3:
					#converted_value = Vector3(float(value[0]), float(value[1]), float(value[2]))
			#TYPE_COLOR:
				#if typeof(value) == TYPE_ARRAY:
					#if value.size() >= 4:
						#converted_value = Color(float(value[0]), float(value[1]), float(value[2]), float(value[3]))
					#elif value.size() >= 3:
						#converted_value = Color(float(value[0]), float(value[1]), float(value[2]))
	#
	## Try to set the property
	#var previous_value = node.get(property_name)
	#
	## Use callv to safely call the setter
	#node.set(property_name, converted_value)
	#
	## Check if the property actually changed
	#var new_value = node.get(property_name)
	#if new_value == previous_value and new_value != converted_value:
		#return {"warning": "Property might be read-only or conversion failed: " + property_name, "previous_value": previous_value, "attempted_value": converted_value}
	#
	#return {"message": "Property set: " + property_name + " = " + str(converted_value)}

func handle_set_parent(params):
	if not params.has("child_name") or not params.has("parent_name"):
		return {"error": "Missing required parameters: child_name and parent_name"}
	
	var child_name = params.child_name
	var parent_name = params.parent_name
	var keep_global_transform = params.get("keep_global_transform", true)
	
	var editor_interface = editor_plugin.get_editor_interface()
	var current_scene = editor_interface.get_edited_scene_root()
	
	if current_scene == null:
		return {"error": "No scene is currently open"}
	
	# Find child node (search the entire scene)
	var child_node = current_scene.find_child(child_name, true, false)
	if not child_node:
		return {"error": "Child node not found: " + child_name}
	
	# Find parent node (search the entire scene)
	var parent_node
	if parent_name == "root":
		parent_node = current_scene
	else:
		parent_node = current_scene.find_child(parent_name, true, false)
	
	if not parent_node:
		return {"error": "Parent node not found: " + parent_name}
	
	# Store the global transform if needed
	var global_transform = null
	if child_node is Node3D and keep_global_transform:
		global_transform = child_node.global_transform
	elif child_node is Node2D and keep_global_transform:
		global_transform = child_node.global_transform
	
	# Get the original parent
	var original_parent = child_node.get_parent()
	if original_parent:
		# Remove from original parent
		original_parent.remove_child(child_node)
	
	# Add to new parent
	parent_node.add_child(child_node)
	
	# Ensure ownership is set correctly
	child_node.owner = current_scene
	
	# Set all children's owner recursively
	_set_owner_recursive(child_node, current_scene)
	
	# Restore global transform if needed
	if child_node is Node3D and global_transform and keep_global_transform:
		child_node.global_transform = global_transform
	elif child_node is Node2D and global_transform and keep_global_transform:
		child_node.global_transform = global_transform
	
	return {"message": "Set parent of '" + child_name + "' to '" + parent_name + "'"}

# Helper function to set owner recursively
func _set_owner_recursive(node, owner):
	for child in node.get_children():
		child.owner = owner
		_set_owner_recursive(child, owner)
		
		
		
		
func handle_create_child_object(params):
	"""Create a new object as a child of an existing node."""
	if not params.has("parent_name"):
		return {"error": "Missing required parameter: parent_name"}
	
	var parent_name = params.parent_name
	var type = params.get("type", "EMPTY")
	var name = params.get("name", "")
	var location = params.get("location", [0, 0, 0])
	var rotation = params.get("rotation", [0, 0, 0])
	var scale = params.get("scale", [1, 1, 1])
	var replace_if_exists = params.get("replace_if_exists", false)
	
	var editor_interface = editor_plugin.get_editor_interface()
	var current_scene = editor_interface.get_edited_scene_root()
	
	if current_scene == null:
		return {"error": "No scene is currently open"}
	
	# Find parent node with proper path handling
	var parent_node = null
	
	if parent_name == "root":
		parent_node = current_scene
	else:
		# Check if it's a path (contains /)
		if "/" in parent_name:
			# Try direct path lookup first
			parent_node = current_scene.get_node_or_null(parent_name)
			
			# If that fails, try with leading slash
			if not parent_node and not parent_name.begins_with("/"):
				parent_node = current_scene.get_node_or_null("/" + parent_name)
				
			# If still not found, try parsing the path components
			if not parent_node:
				var parts = parent_name.split("/")
				var current = current_scene
				
				for part in parts:
					if part == "":
						continue
						
					var found = false
					for child in current.get_children():
						if child.name == part:
							current = child
							found = true
							break
							
					if not found:
						# Try searching recursively for this part
						var found_node = current.find_child(part, true, false)
						if found_node:
							current = found_node
						else:
							# Part not found, path is invalid
							return {"error": "Could not find part '" + part + "' in path: " + parent_name}
				
				parent_node = current
		else:
			# Simple name lookup for non-path names
			parent_node = current_scene.find_child(parent_name, true, false)
	
	if not parent_node:
		return {"error": "Parent node not found: " + parent_name}
	
	# Check if name already exists and handle replacement
	if name != "":
		var existing_node = current_scene.find_child(name, true, false)
		if existing_node and not replace_if_exists:
			return {"error": "Node with name '" + name + "' already exists. Use replace_if_exists=true to replace it."}
		elif existing_node and replace_if_exists:
			existing_node.queue_free()
	
	# Create the node based on type
	var node
	var upper_type = type.to_upper()
	
	# Handle common 3D node types
	match upper_type:
		"NODE", "EMPTY":
			node = Node3D.new()
		"NODE3D":
			node = Node3D.new()
		"SPATIAL": # For compatibility with Godot 3.x terminology
			node = Node3D.new()
		"MESH", "MESHINSTANCE3D":
			node = MeshInstance3D.new()
		"CUBE", "BOX":
			node = MeshInstance3D.new()
			node.mesh = BoxMesh.new()
		"SPHERE":
			node = MeshInstance3D.new()
			node.mesh = SphereMesh.new()
		"CYLINDER":
			node = MeshInstance3D.new()
			node.mesh = CylinderMesh.new()
		"PLANE":
			node = MeshInstance3D.new()
			node.mesh = PlaneMesh.new()
		"CAMERA", "CAMERA3D":
			node = Camera3D.new()
		"LIGHT", "DIRECTIONALLIGHT", "DIRECTIONALLIGHT3D":
			node = DirectionalLight3D.new()
		"SPOTLIGHT", "SPOTLIGHT3D":
			node = SpotLight3D.new()
		"OMNILIGHT", "OMNILIGHT3D":
			node = OmniLight3D.new()
		"RIGIDBODY", "RIGIDBODY3D":
			node = RigidBody3D.new()
		"STATICBODY", "STATICBODY3D":
			node = StaticBody3D.new()
		"CHARACTERBODY", "CHARACTERBODY3D":
			node = CharacterBody3D.new()
		"AREA", "AREA3D":
			node = Area3D.new()
		"COLLISION", "COLLISIONSHAPE3D":
			node = CollisionShape3D.new()
			# Add a default sphere shape
			node.shape = SphereShape3D.new()
		
		# Handle common 2D node types
		"NODE2D":
			node = Node2D.new()
		"SPRITE", "SPRITE2D":
			node = Sprite2D.new()
		"CAMERA2D":
			node = Camera2D.new()
		"AREA2D":
			node = Area2D.new()
		"COLLISION2D", "COLLISIONSHAPE2D":
			node = CollisionShape2D.new()
			# Add a default circle shape
			node.shape = CircleShape2D.new()
		"RIGIDBODY2D":
			node = RigidBody2D.new()
		"STATICBODY2D":
			node = StaticBody2D.new()
		"CHARACTERBODY2D":
			node = CharacterBody2D.new()
		
		# Handle UI node types
		"CONTROL":
			node = Control.new()
		"PANEL":
			node = Panel.new()
		"BUTTON":
			node = Button.new()
		"LABEL":
			node = Label.new()
		"LINEEDIT":
			node = LineEdit.new()
		"TEXTEDIT":
			node = TextEdit.new()
		"CONTAINER":
			node = Container.new()
		"VBOX", "VBOXCONTAINER":
			node = VBoxContainer.new()
		"HBOX", "HBOXCONTAINER":
			node = HBoxContainer.new()
		_:
			# Try to create the node directly by class name using ClassDB
			if ClassDB.class_exists(type) and ClassDB.can_instantiate(type):
				node = ClassDB.instantiate(type)
			else:
				return {"error": "Unsupported object type: " + type}
	
	# Set node name if provided
	if name != "":
		node.name = name
	
	# Add to parent node directly
	parent_node.add_child(node)
	node.owner = current_scene
	
	# Recursively set ownership for all children
	_set_owner_recursive(node, current_scene)
	
	# Set transform for Node3D or Node2D objects
	if node is Node3D:
		node.position = Vector3(location[0], location[1], location[2])
		node.rotation_degrees = Vector3(rotation[0], rotation[1], rotation[2])
		node.scale = Vector3(scale[0], scale[1], scale[2])
	elif node is Node2D:
		node.position = Vector2(location[0], location[1])
		node.rotation_degrees = rotation[0]
		node.scale = Vector2(scale[0], scale[1])
	
	# In the JSON output, include the full path to the parent to help with debugging
	var parent_path = current_scene.get_path_to(parent_node)
	
	return {
		"name": node.name,
		"type": node.get_class(),
		"path": current_scene.get_path_to(node),
		"parent": parent_node.name,
		"parent_path": parent_path
	}










#func handle_create_child_object(params):
	#"""Create a new object as a child of an existing node."""
	#if not params.has("parent_name"):
		#return {"error": "Missing required parameter: parent_name"}
	#
	#var parent_name = params.parent_name
	#var type = params.get("type", "EMPTY")
	#var name = params.get("name", "")
	#var location = params.get("location", [0, 0, 0])
	#var rotation = params.get("rotation", [0, 0, 0])
	#var scale = params.get("scale", [1, 1, 1])
	#var replace_if_exists = params.get("replace_if_exists", false)
	#
	#var editor_interface = editor_plugin.get_editor_interface()
	#var current_scene = editor_interface.get_edited_scene_root()
	#
	#if current_scene == null:
		#return {"error": "No scene is currently open"}
	#
	## Find parent node
	#var parent_node
	#if parent_name == "root":
		#parent_node = current_scene
	#else:
		#parent_node = current_scene.find_child(parent_name, true, false)
	#
	#if not parent_node:
		#return {"error": "Parent node not found: " + parent_name}
	#
	## Check if name already exists and handle replacement
	#if name != "":
		#var existing_node = current_scene.find_child(name, true, false)
		#if existing_node and not replace_if_exists:
			#return {"error": "Node with name '" + name + "' already exists. Use replace_if_exists=true to replace it."}
		#elif existing_node and replace_if_exists:
			#existing_node.queue_free()
	#
	## Create the node based on type (same logic as handle_create_object)
	#var node
	#var upper_type = type.to_upper()
	#
	## Handle common 3D node types
	#match upper_type:
		#"NODE", "EMPTY":
			#node = Node3D.new()
		## (rest of the type matching code from handle_create_object)
		## ...
		#_:
			## Try to create the node directly by class name using ClassDB
			#if ClassDB.class_exists(type) and ClassDB.can_instantiate(type):
				#node = ClassDB.instantiate(type)
			#else:
				#return {"error": "Unsupported object type: " + type}
	#
	## Set node name if provided
	#if name != "":
		#node.name = name
	#
	## Add to parent node directly
	#parent_node.add_child(node)
	#node.owner = current_scene
	#
	## Set transform for Node3D or Node2D objects
	#if node is Node3D:
		#node.position = Vector3(location[0], location[1], location[2])
		#node.rotation_degrees = Vector3(rotation[0], rotation[1], rotation[2])
		#node.scale = Vector3(scale[0], scale[1], scale[2])
	#elif node is Node2D:
		#node.position = Vector2(location[0], location[1])
		#node.rotation_degrees = rotation[0]
		#node.scale = Vector2(scale[0], scale[1])
	#
	#return {
		#"name": node.name,
		#"type": node.get_class(),
		#"path": current_scene.get_path_to(node),
		#"parent": parent_name
	#}
	
func handle_set_mesh(params):
	"""Create and set a mesh on a MeshInstance3D node."""
	if not params.has("node_name") or not params.has("mesh_type"):
		return {"error": "Missing required parameters: node_name and mesh_type"}
	
	var node_name = params.node_name
	var mesh_type = params.mesh_type
	
	print("handle_set_mesh called for node: ", node_name, " mesh_type: ", mesh_type)
	
	var editor_interface = editor_plugin.get_editor_interface()
	var current_scene = editor_interface.get_edited_scene_root()
	
	if current_scene == null:
		return {"error": "No scene is currently open"}
	
	# Find node using the improved node lookup
	var node = _find_node(current_scene, node_name)
	if not node:
		return {"error": "Node not found: " + node_name}
	
	print("Node found: ", node.name, " type: ", node.get_class())
	
	# Check if the node can have a mesh property
	if not node is MeshInstance3D:
		return {"error": "Node is not a MeshInstance3D: " + node_name}
	
	# Create mesh based on type
	var mesh
	match mesh_type.to_upper():
		"CAPSULEMESH":
			mesh = CapsuleMesh.new()
			if params.has("radius"):
				mesh.radius = float(params.radius)
			if params.has("height"):
				mesh.height = float(params.height)
		"BOXMESH":
			mesh = BoxMesh.new()
			if params.has("size"):
				var size = params.size
				mesh.size = Vector3(float(size[0]), float(size[1]), float(size[2]))
		"SPHEREMESH":
			mesh = SphereMesh.new()
			if params.has("radius"):
				mesh.radius = float(params.radius)
		"CYLINDERMESH":
			mesh = CylinderMesh.new()
			if params.has("radius"):
				mesh.radius = float(params.radius)
			if params.has("height"):
				mesh.height = float(params.height)
		"PLANEMESH":
			mesh = PlaneMesh.new()
			if params.has("size"):
				var size = params.size
				mesh.size = Vector2(float(size[0]), float(size[1]))
		_:
			return {"error": "Unsupported mesh type: " + mesh_type}
	
	# Set the mesh
	node.mesh = mesh
	
	return {"message": "Set " + mesh_type + " on " + node_name}
	
	
func _find_node(root, name_or_path):
	# Check if it's a path (contains /)
	if "/" in name_or_path:
		# Try direct path lookup first
		var node = root.get_node_or_null(name_or_path)
		if node:
			return node
			
		# Try as relative path
		if not name_or_path.begins_with("/"):
			node = root.get_node_or_null("/" + name_or_path)
			if node:
				return node
				
		# Try all combinations of path separators
		var parts = name_or_path.split("/")
		var current = root
		
		for part in parts:
	   # Look for the next part in current node's children
			var found = false
			for child in current.get_children():
				if child.name == part:
					current = child
					found = true
					break
					
			if not found:
				# Try searching recursively
				var found_node = current.find_child(part, true, false)
				if found_node:
					current = found_node
				else:
					return null
				
		return current
	else:
		# Simple name lookup
		return root.find_child(name_or_path, true, false)
		
		
func handle_set_collision_shape(params):
	"""Create and set a collision shape on a CollisionShape3D or CollisionShape2D node."""
	if not params.has("node_name") or not params.has("shape_type"):
		return {"error": "Missing required parameters: node_name and shape_type"}
	
	var node_name = params.node_name
	var shape_type = params.shape_type
	var shape_params = params.get("shape_params", {})
	
	var editor_interface = editor_plugin.get_editor_interface()
	var current_scene = editor_interface.get_edited_scene_root()
	
	if current_scene == null:
		return {"error": "No scene is currently open"}
	
	# Find node by name or path
	var node = _find_node(current_scene, node_name)
	if not node:
		return {"error": "Node not found: " + node_name}

	# Check if the node can have a shape property
	if not (node is CollisionShape3D or node is CollisionShape2D):
		return {"error": "Node is not a CollisionShape: " + node_name}
	
	# Create shape based on type
	var shape
	match shape_type.to_upper():
		"CAPSULESHAPE3D":
			shape = CapsuleShape3D.new()
			if shape_params.has("radius"):
				shape.radius = float(shape_params.radius)
			if shape_params.has("height"):
				shape.height = float(shape_params.height)
		"BOXSHAPE3D":
			shape = BoxShape3D.new()
			if shape_params.has("size"):
				var size = shape_params.size
				shape.size = Vector3(float(size[0]), float(size[1]), float(size[2]))
		"SPHERESHAPE3D":
			shape = SphereShape3D.new()
			if shape_params.has("radius"):
				shape.radius = float(shape_params.radius)
		"CYLINDERSHAPE3D":
			shape = CylinderShape3D.new()
			if shape_params.has("radius"):
				shape.radius = float(shape_params.radius)
			if shape_params.has("height"):
				shape.height = float(shape_params.height)
		"WORLDBOUNDARYSHAPE3D":
			shape = WorldBoundaryShape3D.new()
		# 2D Shapes
		"CIRCLESHAPE2D":
			shape = CircleShape2D.new()
			if shape_params.has("radius"):
				shape.radius = float(shape_params.radius)
		"RECTANGLESHAPE2D":
			shape = RectangleShape2D.new()
			if shape_params.has("size"):
				var size = shape_params.size
				shape.size = Vector2(float(size[0]), float(size[1]))
		"CAPSULESHAPE2D":
			shape = CapsuleShape2D.new()
			if shape_params.has("radius"):
				shape.radius = float(shape_params.radius)
			if shape_params.has("height"):
				shape.height = float(shape_params.height)
		_:
			return {"error": "Unsupported shape type: " + shape_type}
	
	# Set the shape
	node.shape = shape
	
	return {"message": "Set " + shape_type + " on " + node_name}
	
	
#func handle_set_nested_property(params):
	#"""Set a nested property like environment/sky/sky_material on a node."""
	#if not params.has("node_name") or not params.has("property_name") or not params.has("value"):
		#return {"error": "Missing required parameters: node_name, property_name, and value"}
	#
	#var node_name = params.node_name
	#var property_path = params.property_name
	#var value = params.value
	#var value_type = params.get("value_type", "")
	#
	#var editor_interface = editor_plugin.get_editor_interface()
	#var current_scene = editor_interface.get_edited_scene_root()
	#
	#if current_scene == null:
		#return {"error": "No scene is currently open"}
	#
	## Find node by name or path
	#var node = null
	#
	## Check if it's a path (contains /)
	#if "/" in node_name:
		## Try direct path lookup first
		#node = current_scene.get_node_or_null(node_name)
		#
		## If that fails, try with leading slash
		#if not node and not node_name.begins_with("/"):
			#node = current_scene.get_node_or_null("/" + node_name)
			#
		## Try other lookup methods if needed...
	#else:
		## Simple name lookup for non-path names
		#node = current_scene.find_child(node_name, true, false)
	#
	#if not node:
		#return {"error": "Node not found: " + node_name}
	#
	## Split the property path
	#var property_parts = property_path.split("/")
	#
	## Handle special cases for common node types
	#if node is WorldEnvironment:
		## Make sure the environment exists
		#if not node.environment:
			#node.environment = Environment.new()
		#
		## Handle environment properties
		#if property_parts.size() >= 1 and property_parts[0] == "environment":
			#var env = node.environment
			#
			## Handle special case for sky material
			#if property_parts.size() >= 3 and property_parts[1] == "sky" and property_parts[2] == "sky_material":
				## Make sure sky exists
				#if not env.sky:
					#env.sky = Sky.new()
				#
				#if property_parts.size() == 3:
					## Create the material based on type
					#var material = null
					#if value == "ProceduralSkyMaterial":
						#material = ProceduralSkyMaterial.new()
					#elif value == "PanoramaSkyMaterial":
						#material = PanoramaSkyMaterial.new()
					#elif value == "PhysicalSkyMaterial":
						#material = PhysicalSkyMaterial.new()
					#else:
						#return {"error": "Unknown sky material type: " + str(value)}
					#
					## Set the sky material
					#env.sky.sky_material = material
					#return {"message": "Set sky material to " + str(value)}
				#
				## Handle sky material properties (e.g., environment/sky/sky_material/sky_top_color)
				#elif property_parts.size() >= 4 and env.sky.sky_material:
					#var material = env.sky.sky_material
					#var mat_prop = property_parts[3]
					#
					## Verify property exists on the material
					#if not mat_prop in material:
						#return {"error": "Property not found on sky material: " + mat_prop}
					#
					## Handle color properties
					#if typeof(material.get(mat_prop)) == TYPE_COLOR:
						#if typeof(value) == TYPE_ARRAY and value.size() >= 3:
							#if value.size() >= 4:
								#material.set(mat_prop, Color(value[0], value[1], value[2], value[3]))
							#else:
								#material.set(mat_prop, Color(value[0], value[1], value[2]))
							#return {"message": "Set sky material property " + mat_prop + " to " + str(value)}
					#else:
						## Set other property types
						#material.set(mat_prop, value)
						#return {"message": "Set sky material property " + mat_prop + " to " + str(value)}
			#
			## Handle direct environment properties
			#elif property_parts.size() == 2:
				#var prop = property_parts[1]
				#
				## Map common property names to actual Godot property names
				#match prop:
					#"background_color":
						#prop = "background_color"
					#"ambient_light_color":
						#prop = "ambient_light_color"
					#"fog_color":
						#prop = "fog_color"
					#"background_mode":
						#prop = "background_mode"
					## Add more mappings as needed
				#
				## Verify property exists
				#if not prop in env:
					#var available_props = []
					#for p in ["background_color", "ambient_light_color", "fog_color", "background_mode", 
							  #"fog_enabled", "fog_density", "glow_enabled", "glow_intensity", 
							  #"adjustment_enabled", "tonemap_mode"]:
						#if p in env:
							#available_props.append(p)
					#return {"error": "Property not found on environment: " + prop + 
							#". Available properties include: " + str(available_props)}
				#
				## Convert value based on property type
				#var converted_value = value
				#var current_value = env.get(prop)
				#
				## Handle different types
				#if typeof(current_value) == TYPE_COLOR:
					#if typeof(value) == TYPE_ARRAY and value.size() >= 3:
						#if value.size() >= 4:
							#converted_value = Color(value[0], value[1], value[2], value[3])
						#else:
							#converted_value = Color(value[0], value[1], value[2])
				#elif typeof(current_value) == TYPE_BOOL:
					#if typeof(value) == TYPE_STRING:
						#converted_value = (value.to_lower() == "true")
					#else:
						#converted_value = bool(value)
				#elif typeof(current_value) == TYPE_INT:
					#converted_value = int(value)
				#elif typeof(current_value) == TYPE_FLOAT:
					#converted_value = float(value)
				#
				## Set the property
				#env.set(prop, converted_value)
				#return {"message": "Set environment property " + prop + " to " + str(converted_value)}
			#
			## Handle environment sub-objects (e.g., environment/fog/enabled)
			#elif property_parts.size() == 3:
				#var sub_obj = property_parts[1]
				#var sub_prop = property_parts[2]
				#
				## Map common property paths
				#if sub_obj == "fog" and sub_prop == "enabled":
					#env.fog_enabled = bool(value)
					#return {"message": "Set fog_enabled to " + str(bool(value))}
				#elif sub_obj == "glow" and sub_prop == "enabled":
					#env.glow_enabled = bool(value)
					#return {"message": "Set glow_enabled to " + str(bool(value))}
				#elif sub_obj == "ambient_light" and sub_prop == "color":
					#if typeof(value) == TYPE_ARRAY and value.size() >= 3:
						#env.ambient_light_color = Color(value[0], value[1], value[2])
						#return {"message": "Set ambient_light_color to " + str(value)}
				#
				## Generic property mapping attempt
				#var full_prop = sub_obj + "_" + sub_prop
				#if full_prop in env:
					#env.set(full_prop, value)
					#return {"message": "Set " + full_prop + " to " + str(value)}
				#
				#return {"error": "Unsupported environment property path: " + property_path}
	#
	## Handle other node types here
	## ...
	#
	#return {"error": "Unsupported nested property path: " + property_path}


func handle_set_nested_property(params):
	"""Set a nested property like environment/sky/sky_material on a node."""
	if not params.has("node_name") or not params.has("property_name") or not params.has("value"):
		return {"error": "Missing required parameters: node_name, property_name, and value"}
	
	var node_name = params.node_name
	var property_path = params.property_name
	var value = params.value
	var value_type = params.get("value_type", "")
	
	print("Setting nested property: ", property_path, " to ", value, " on ", node_name)
	
	var editor_interface = editor_plugin.get_editor_interface()
	var current_scene = editor_interface.get_edited_scene_root()
	
	if current_scene == null:
		return {"error": "No scene is currently open"}
	
	# Find node by name or path
	var node = null
	
	# Check if it's a path (contains /)
	if "/" in node_name:
		# Try direct path lookup first
		node = current_scene.get_node_or_null(node_name)
		
		# If that fails, try with leading slash
		if not node and not node_name.begins_with("/"):
			node = current_scene.get_node_or_null("/" + node_name)
			
		# Try parsing the path manually if needed
		if not node:
			# Try other path resolution methods...
			pass
	else:
		# Simple name lookup for non-path names
		node = current_scene.find_child(node_name, true, false)
	
	if not node:
		return {"error": "Node not found: " + node_name}
	
	# Split the property path
	var property_parts = property_path.split("/")
	
	# Handle WorldEnvironment properties
	if node is WorldEnvironment:
		return _handle_worldenvironment_properties(node, property_parts, value)
	
	# Add other node type handlers here
	
	# Default case for simple properties
	return {"error": "Unsupported node type for nested properties: " + node.get_class()}

func _handle_worldenvironment_properties(node, property_parts, value):
	"""Handle nested properties for WorldEnvironment nodes."""
	# Make sure the environment exists
	if not node.environment:
		node.environment = Environment.new()
	
	# Get environment resource for easier access
	var env = node.environment
	
	# First level should be "environment"
	if property_parts.size() < 1 or property_parts[0] != "environment":
		return {"error": "WorldEnvironment properties must start with 'environment/'"}
	
	# Handle sky material properties (4-part paths)
	if property_parts.size() == 4 and property_parts[1] == "sky" and property_parts[2] == "sky_material":
		# Make sure sky exists
		if not env.sky:
			env.sky = Sky.new()
			
		# Make sure sky material exists
		if not env.sky.sky_material:
			env.sky.sky_material = ProceduralSkyMaterial.new()
		
		var material = env.sky.sky_material
		var property_name = property_parts[3]
		
		# Debug info
		print("Trying to set sky material property: ", property_name)
		print("Material class: ", material.get_class())
		
		# Direct property handling for cloud properties
		if property_name == "use_clouds" or property_name == "clouds_enabled":
			# Enable/disable clouds directly
			material.use_clouds = bool(value)
			return {"message": "Set use_clouds to " + str(bool(value))}
			
		elif property_name == "cloud_color":
			# Set cloud color directly
			if typeof(value) == TYPE_ARRAY and value.size() >= 3:
				material.cloud_color = Color(float(value[0]), float(value[1]), float(value[2]))
				return {"message": "Set cloud_color to " + str(material.cloud_color)}
			
		elif property_name == "cloud_coverage":
			# Set cloud coverage directly
			material.cloud_coverage = float(value)
			return {"message": "Set cloud_coverage to " + str(float(value))}
			
		elif property_name == "cloud_size":
			# Set cloud size directly
			material.cloud_size = float(value)
			return {"message": "Set cloud_size to " + str(float(value))}
			
		# Handle other properties with the property map
		var property_map = {
			# Sky colors
			"sky_top_color": "sky_top_color",
			"sky_horizon_color": "sky_horizon_color",
			"sky_curve": "sky_curve",
			"ground_horizon_color": "ground_horizon_color",
			"ground_bottom_color": "ground_bottom_color",
			"ground_curve": "ground_curve",
			
			# Sun properties
			"sun_angle_max": "sun_angle_max",
			"sun_curve": "sun_curve"
		}
		
		# Check if property name needs to be mapped
		if property_name in property_map:
			property_name = property_map[property_name]
			
			# Try to set the property with property-specific type conversion
			var current_value = material.get(property_name)
			var converted_value = value
			
			# Handle different property types
			match typeof(current_value):
				TYPE_BOOL:
					converted_value = bool(value)
				TYPE_INT:
					converted_value = int(value)
				TYPE_FLOAT:
					converted_value = float(value)
				TYPE_COLOR:
					if typeof(value) == TYPE_ARRAY and value.size() >= 3:
						if value.size() >= 4:
							converted_value = Color(float(value[0]), float(value[1]), float(value[2]), float(value[3]))
						else:
							converted_value = Color(float(value[0]), float(value[1]), float(value[2]))
			
			# Set the property
			material.set(property_name, converted_value)
			return {"message": "Set sky material property " + property_name + " to " + str(converted_value)}
		
		return {"error": "Unknown sky material property: " + property_name + ". Available cloud properties: use_clouds, cloud_color, cloud_coverage, cloud_size"}
	
	# Handle sky material type (3-part paths)
	elif property_parts.size() == 3 and property_parts[1] == "sky" and property_parts[2] == "sky_material":
		# Make sure sky exists
		if not env.sky:
			env.sky = Sky.new()
		
		# Create the material based on type
		var material = null
		
		if value == "ProceduralSkyMaterial":
			material = ProceduralSkyMaterial.new()
		elif value == "PanoramaSkyMaterial":
			material = PanoramaSkyMaterial.new()
		elif value == "PhysicalSkyMaterial":
			material = PhysicalSkyMaterial.new()
		else:
			return {"error": "Unknown sky material type: " + str(value)}
		
		# Set the sky material
		env.sky.sky_material = material
		return {"message": "Set sky material to " + str(value)}
	
	# Handle direct environment properties (2-part paths)
	elif property_parts.size() == 2:
		var property_name = property_parts[1]
		
		# Map common property name variations to actual property names
		var property_map = {
			"background": "background_mode",
			"ambient_light_color": "ambient_light_color",
			"background_color": "background_color",
			"fog_enabled": "fog_enabled",
			"glow_enabled": "glow_enabled",
			"glow_intensity": "glow_intensity",
			"fog_density": "fog_density",
			"fog_color": "fog_color",
			"volumetric_fog_enabled": "volumetric_fog_enabled",
			"volumetric_fog_density": "volumetric_fog_density",
			"volumetric_fog_albedo": "volumetric_fog_albedo"
		}
		
		# Check if we need to map the property name
		if property_name in property_map:
			property_name = property_map[property_name]
		
		# Verify property exists
		if not property_name in env:
			return {"error": "Property not found on environment: " + property_name}
		
		# Convert value based on property type
		var converted_value = value
		var current_value = env.get(property_name)
		
		# Handle different property types
		match typeof(current_value):
			TYPE_BOOL:
				converted_value = bool(value)
			TYPE_INT:
				converted_value = int(value)
			TYPE_FLOAT:
				converted_value = float(value)
			TYPE_COLOR:
				if typeof(value) == TYPE_ARRAY and value.size() >= 3:
					if value.size() >= 4:
						converted_value = Color(float(value[0]), float(value[1]), float(value[2]), float(value[3]))
					else:
						converted_value = Color(float(value[0]), float(value[1]), float(value[2]))
		
		# Set the property
		env.set(property_name, converted_value)
		return {"message": "Set environment property " + property_name + " to " + str(converted_value)}
	
	# Handle fog properties (3-part paths)
	elif property_parts.size() == 3 and property_parts[1] == "fog":
		var prop = property_parts[2]
		
		if prop == "enabled":
			env.fog_enabled = bool(value)
			return {"message": "Set fog_enabled to " + str(bool(value))}
		elif prop == "density":
			env.fog_density = float(value)
			return {"message": "Set fog_density to " + str(float(value))}
		elif prop == "color":
			if typeof(value) == TYPE_ARRAY and value.size() >= 3:
				env.fog_color = Color(float(value[0]), float(value[1]), float(value[2]))
				return {"message": "Set fog_color to " + str(env.fog_color)}
		else:
			# Try a direct combined property name
			var combined_prop = "fog_" + prop
			if combined_prop in env:
				env.set(combined_prop, value)
				return {"message": "Set " + combined_prop + " to " + str(value)}
			return {"error": "Unknown fog property: " + prop}
	
	# Handle volumetric fog properties (3-part paths)  
	elif property_parts.size() == 3 and property_parts[1] == "volumetric_fog":
		var prop = property_parts[2]
		
		if prop == "enabled":
			env.volumetric_fog_enabled = bool(value)
			return {"message": "Set volumetric_fog_enabled to " + str(bool(value))}
		elif prop == "density":
			env.volumetric_fog_density = float(value)
			return {"message": "Set volumetric_fog_density to " + str(float(value))}
		elif prop == "albedo":
			if typeof(value) == TYPE_ARRAY and value.size() >= 3:
				env.volumetric_fog_albedo = Color(float(value[0]), float(value[1]), float(value[2]))
				return {"message": "Set volumetric_fog_albedo to " + str(env.volumetric_fog_albedo)}
		else:
			# Try a direct combined property name
			var combined_prop = "volumetric_fog_" + prop
			if combined_prop in env:
				env.set(combined_prop, value)
				return {"message": "Set " + combined_prop + " to " + str(value)}
			return {"error": "Unknown volumetric fog property: " + prop}
			
	# Other environment properties can be added here
	
	return {"error": "Unsupported property path: " + property_parts.join("/")}

# Add the following function:
func handle_delete_script(params):
	if not params.has("script_path"):
		return {"error": "Missing required parameter: script_path"}
	
	var script_path = params.script_path
	
	# Check if file exists
	if not FileAccess.file_exists(script_path):
		return {"error": "Script file does not exist: " + script_path}
	
	# Delete the file
	var error = DirAccess.remove_absolute(script_path)
	if error != OK:
		return {"error": "Failed to delete script file: " + script_path + " (Error code: " + str(error) + ")"}
	
	return {
		"message": "Script deleted successfully: " + script_path
	}

# Add the following function near the handle_delete_script function:
func handle_delete_file(params):
	if not params.has("file_path"):
		return {"error": "Missing required parameter: file_path"}
	
	var file_path = params.file_path
	
	# Check if file exists
	if not FileAccess.file_exists(file_path):
		return {"error": "File does not exist: " + file_path}
	
	# Delete the file
	var error = DirAccess.remove_absolute(file_path)
	if error != OK:
		return {"error": "Failed to delete file: " + file_path + " (Error code: " + str(error) + ")"}
	
	return {
		"message": "File deleted successfully: " + file_path
	}

func handle_show_message(params):
	if not params.has("message"):
		return {"error": "Missing required parameter: message"}
	
	var message = params.message
	
	# Show a message dialog
	editor_plugin.get_editor_interface().show_message_notification(message)
	
	return {"message": "Message shown successfully"}

func handle_reimport_asset(params):
	if not params.has("asset_path"):
		return {"error": "Missing required parameter: asset_path"}
	
	var asset_path = params.asset_path
	
	# Force a filesystem scan to detect the new file
	var editor_filesystem = editor_plugin.get_editor_interface().get_resource_filesystem()
	if editor_filesystem:
		editor_filesystem.scan()
		# Also scan the specific directory
		var dir_path = asset_path.get_base_dir()
		editor_filesystem.scan_sources()
		
		return {
			"message": "Triggered filesystem scan for: " + asset_path
		}
	else:
		return {"error": "Could not access editor filesystem"}

func handle_import_glb_scene(params):
	if not params.has("glb_path"):
		return {"error": "Missing required parameter: glb_path"}
	
	var glb_path = params.glb_path
	var name = params.get("name", "")
	var position = params.get("position", [0, 0, 0])
	var rotation = params.get("rotation", [0, 0, 0])
	var scale = params.get("scale", [1, 1, 1])
	
	var editor_interface = editor_plugin.get_editor_interface()
	var current_scene = editor_interface.get_edited_scene_root()
	
	if current_scene == null:
		return {"error": "No scene is currently open"}
	
	# Check if the GLB file exists
	if not FileAccess.file_exists(glb_path):
		return {"error": "GLB file not found: " + glb_path}
	
	# Try to load the GLB as a PackedScene
	var glb_scene = load(glb_path)
	if not glb_scene:
		return {"error": "Failed to load GLB file: " + glb_path}
	
	# Check if it's a PackedScene
	if glb_scene is PackedScene:
		# Instantiate the packed scene
		var instance = glb_scene.instantiate()
		if not instance:
			return {"error": "Failed to instantiate GLB scene"}
		
		# Set the name
		if name != "":
			instance.name = name
		else:
			# Use filename without extension
			var filename = glb_path.get_file().get_basename()
			instance.name = filename
		
		# Add to current scene
		current_scene.add_child(instance)
		instance.owner = current_scene
		
		# Set ownership recursively for all children
		_set_owner_recursive(instance, current_scene)
		
		# Set transform if it's a 3D node
		if instance is Node3D:
			instance.position = Vector3(position[0], position[1], position[2])
			instance.rotation_degrees = Vector3(rotation[0], rotation[1], rotation[2])
			instance.scale = Vector3(scale[0], scale[1], scale[2])
		
		return {
			"success": true,
			"instance_name": instance.name,
			"message": "GLB scene imported successfully as: " + instance.name
		}
	else:
		# If it's not a PackedScene, try to create a MeshInstance3D
		var node_name = name if name != "" else glb_path.get_file().get_basename()
		
		# Create a MeshInstance3D
		var mesh_instance = MeshInstance3D.new()
		mesh_instance.name = node_name
		
		# Try to set the mesh
		if glb_scene is Mesh:
			mesh_instance.mesh = glb_scene
		else:
			# Try loading it differently
			return {"error": "GLB file is not a PackedScene or Mesh resource"}
		
		# Add to scene
		current_scene.add_child(mesh_instance)
		mesh_instance.owner = current_scene
		
		# Set transform
		mesh_instance.position = Vector3(position[0], position[1], position[2])
		mesh_instance.rotation_degrees = Vector3(rotation[0], rotation[1], rotation[2])
		mesh_instance.scale = Vector3(scale[0], scale[1], scale[2])
		
		return {
			"success": true,
			"instance_name": mesh_instance.name,
			"message": "GLB imported as MeshInstance3D: " + mesh_instance.name
		}
