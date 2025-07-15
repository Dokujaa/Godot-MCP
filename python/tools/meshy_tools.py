# tools/meshy_tools.py
from mcp.server.fastmcp import FastMCP, Context
from typing import Optional, Dict, Any
import requests
import json
import time
import os
import urllib.request
import logging
from config import config
from godot_connection import get_godot_connection

logger = logging.getLogger("GodotMCP")

def register_meshy_tools(mcp: FastMCP):
    """Register Meshy API tools with the MCP server."""
    
    @mcp.tool()
    def generate_mesh_from_text(
        ctx: Context,
        prompt: str,
        name: str = None,
        art_style: str = "realistic",
        negative_prompt: str = "",
        should_remesh: bool = True,
        import_to_godot: bool = True,
        position: list = None
    ) -> str:
        """Generate a 3D mesh from text description using Meshy API and optionally import it into Godot.
        
        ⚠️ IMPORTANT: This generates PREVIEW quality meshes (lower quality, faster, often free).
        ⚠️ DO NOT automatically refine unless explicitly requested by the user!
        ⚠️ Refinement costs real API credits and should only be used when the user is satisfied with the preview.
        
        Uses the official Meshy API v2 text-to-3d endpoint to generate 3D models.
        This creates a preview mesh first, which can later be refined for higher quality using refine_generated_mesh().
        
        For testing without consuming credits, you can set MESHY_API_KEY to: msy_dummy_api_key_for_test_mode_12345678
        
        Args:
            ctx: The MCP context
            prompt: Text description of the 3D model to generate (e.g., "a medieval sword with ornate handle")
            name: Optional name for the generated mesh object in Godot
            art_style: Art style for generation ("realistic", "cartoon", "low-poly", "sculpture")
            negative_prompt: What to avoid in the generation (e.g., "low quality, low resolution, low poly, ugly")
            should_remesh: Whether to apply remeshing for better topology (recommended: True)
            import_to_godot: Whether to automatically import the mesh into Godot scene
            position: Optional [x, y, z] position to place the object
            
        Returns:
            str: Success message with details or error information
        """
        try:
            if not config.meshy_api_key:
                return "Error: MESHY_API_KEY environment variable not set. Please set your Meshy API key or use the test key: msy_dummy_api_key_for_test_mode_12345678"
            
            # Step 1: Create text-to-3D task
            logger.info(f"Starting mesh generation for prompt: {prompt}")
            
            headers = {
                "Authorization": f"Bearer {config.meshy_api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare the generation request - Matches official Meshy API v2 format exactly
            generation_data = {
                "mode": "preview",  # Start with preview mode
                "prompt": prompt,
                "art_style": art_style,
                "should_remesh": should_remesh
            }
            
            # Add negative_prompt only if provided (optional parameter)
            if negative_prompt.strip():
                generation_data["negative_prompt"] = negative_prompt
            
            # Create the generation task - Official v2 endpoint
            response = requests.post(
                f"{config.meshy_base_url}/v2/text-to-3d",
                headers=headers,
                json=generation_data,
                timeout=30
            )
            
            # Handle response according to official documentation
            response.raise_for_status()
            
            task_data = response.json()
            task_id = task_data.get("result")
            
            if not task_id:
                return f"Error: No task ID returned from Meshy API. Response: {task_data}"
            
            logger.info(f"Preview task created. Task ID: {task_id}")
            
            # Step 2: Poll for completion - matches official polling pattern
            logger.info("Waiting for mesh generation to complete...")
            
            max_wait_time = config.meshy_timeout
            check_interval = 5  # Check every 5 seconds (matches documentation example)
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                # Check task status - Official v2 endpoint
                status_response = requests.get(
                    f"{config.meshy_base_url}/v2/text-to-3d/{task_id}",
                    headers=headers,
                    timeout=30
                )
                
                status_response.raise_for_status()
                
                status_data = status_response.json()
                status = status_data.get("status")
                progress = status_data.get("progress", 0)
                
                logger.info(f"Preview task status: {status} | Progress: {progress}%")
                
                if status == "SUCCEEDED":
                    logger.info("Preview task finished.")
                    
                    # Generation completed successfully
                    model_urls = status_data.get("model_urls", {})
                    
                    if not model_urls:
                        return "Error: No model URLs in completed task"
                    
                    # Prefer GLB format for Godot (matches documentation example)
                    download_url = model_urls.get("glb") or model_urls.get("fbx") or model_urls.get("obj")
                    
                    if not download_url:
                        return f"Error: No supported model format found. Available formats: {list(model_urls.keys())}"
                    
                    logger.info(f"Preview model completed! Download URL: {download_url}")
                    
                    # Store task_id for potential refinement
                    result_message = f"Preview mesh generated successfully! Task ID: {task_id}\n"
                    result_message += f"Download URL: {download_url}\n"
                    result_message += f"Use refine_generated_mesh('{task_id}') to create a high-quality textured version."
                    
                    # Step 3: Download the mesh file
                    if import_to_godot:
                        download_result = _download_mesh_to_project(download_url, name)
                        if "Error" in download_result:
                            return f"{result_message}\n\n{download_result}"
                        else:
                            return f"{result_message}\n\n{download_result}"
                    else:
                        return result_message
                
                elif status == "FAILED":
                    error_msg = status_data.get("task_error", {}).get("message", "Unknown error")
                    return f"Mesh generation failed: {error_msg}"
                
                elif status in ["PENDING", "IN_PROGRESS"]:
                    # Still processing, wait and check again (matches documentation pattern)
                    logger.info(f"Preview task status: {status} | Progress: {progress} | Retrying in {check_interval} seconds...")
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                else:
                    return f"Unknown task status: {status}"
            
            return f"Mesh generation timeout after {max_wait_time} seconds"
            
        except requests.exceptions.RequestException as e:
            return f"Network error communicating with Meshy API: {str(e)}"
        except Exception as e:
            return f"Error generating mesh: {str(e)}"
    
    @mcp.tool()
    def generate_mesh_from_image(
        ctx: Context,
        image_url: str,
        name: str = None,
        import_to_godot: bool = True,
        position: list = None
    ) -> str:
        """Generate a 3D mesh from an image using Meshy API and optionally import it into Godot.
        
        ⚠️ IMPORTANT: This generates standard quality meshes and may consume API credits.
        ⚠️ Do NOT automatically refine the result unless explicitly requested by the user!
        
        Args:
            ctx: The MCP context
            image_url: URL or path to the image to convert to 3D
            name: Optional name for the generated mesh object in Godot
            import_to_godot: Whether to automatically import the mesh into Godot scene
            position: Optional [x, y, z] position to place the object
            
        Returns:
            str: Success message with details or error information
        """
        try:
            if not config.meshy_api_key:
                return "Error: MESHY_API_KEY environment variable not set. Please set your Meshy API key."
            
            logger.info(f"Starting mesh generation from image: {image_url}")
            
            headers = {
                "Authorization": f"Bearer {config.meshy_api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare the generation request
            generation_data = {
                "image_url": image_url,
                "enable_pbr": True  # Enable PBR materials
            }
            
            # Create the generation task - Updated endpoint
            response = requests.post(
                f"{config.meshy_base_url}/v2/image-to-3d",
                headers=headers,
                json=generation_data,
                timeout=30
            )
            
            if response.status_code not in [200, 202]:
                return f"Error creating image-to-3D task: {response.status_code} - {response.text}"
            
            task_data = response.json()
            task_id = task_data.get("result")
            
            if not task_id:
                return f"Error: No task ID returned from Meshy API. Response: {task_data}"
            
            logger.info(f"Image-to-3D task created with ID: {task_id}")
            
            # Poll for completion (similar to text-to-3D)
            max_wait_time = config.meshy_timeout
            check_interval = 15  # Image-to-3D might take longer
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                status_response = requests.get(
                    f"{config.meshy_base_url}/v2/image-to-3d/{task_id}",
                    headers=headers,
                    timeout=30
                )
                
                if status_response.status_code != 200:
                    return f"Error checking task status: {status_response.status_code} - {status_response.text}"
                
                status_data = status_response.json()
                status = status_data.get("status")
                
                logger.info(f"Task status: {status}")
                
                if status == "SUCCEEDED":
                    model_urls = status_data.get("model_urls", {})
                    
                    if not model_urls:
                        return "Error: No model URLs in completed task"
                    
                    download_url = model_urls.get("glb") or model_urls.get("fbx") or model_urls.get("obj")
                    
                    if not download_url:
                        return f"Error: No supported model format found. Available formats: {list(model_urls.keys())}"
                    
                    logger.info(f"Image-to-3D generation completed! Download URL: {download_url}")
                    
                    result_message = f"Mesh generated successfully from image! Download URL: {download_url}"
                    
                    if import_to_godot:
                        download_result = _download_mesh_to_project(download_url, name)
                        return f"{result_message}\n\n{download_result}"
                    else:
                        return result_message
                
                elif status == "FAILED":
                    error_msg = status_data.get("task_error", {}).get("message", "Unknown error")
                    return f"Image-to-3D generation failed: {error_msg}"
                
                elif status in ["PENDING", "IN_PROGRESS"]:
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                else:
                    return f"Unknown task status: {status}"
            
            return f"Image-to-3D generation timeout after {max_wait_time} seconds"
            
        except Exception as e:
            return f"Error generating mesh from image: {str(e)}"
    
    @mcp.tool()
    def check_mesh_generation_progress(
        ctx: Context,
        task_id: str
    ) -> str:
        """Check the progress of a mesh generation task using its task ID.
        
        Args:
            ctx: The MCP context
            task_id: The task ID from a previous mesh generation request
            
        Returns:
            str: Current status and progress information
        """
        try:
            if not config.meshy_api_key:
                return "Error: MESHY_API_KEY environment variable not set. Please set your Meshy API key."
            
            headers = {
                "Authorization": f"Bearer {config.meshy_api_key}",
                "Content-Type": "application/json"
            }
            
            # Check task status
            status_response = requests.get(
                f"{config.meshy_base_url}/v2/text-to-3d/{task_id}",
                headers=headers,
                timeout=30
            )
            
            if status_response.status_code != 200:
                return f"Error checking task status: {status_response.status_code} - {status_response.text}"
            
            status_data = status_response.json()
            status = status_data.get("status")
            
            if status == "SUCCEEDED":
                model_urls = status_data.get("model_urls", {})
                available_formats = list(model_urls.keys())
                
                return f"✅ Mesh generation completed successfully!\n" \
                       f"Task ID: {task_id}\n" \
                       f"Available formats: {', '.join(available_formats)}\n" \
                       f"Use refine_generated_mesh() if you want higher quality, or the mesh is ready for download."
            
            elif status == "FAILED":
                error_msg = status_data.get("task_error", {}).get("message", "Unknown error")
                return f"❌ Mesh generation failed for task {task_id}\n" \
                       f"Error: {error_msg}"
            
            elif status == "PENDING":
                return f"⏳ Mesh generation is queued for processing\n" \
                       f"Task ID: {task_id}\n" \
                       f"Status: Waiting to start..."
            
            elif status == "IN_PROGRESS":
                # Try to get progress percentage if available
                progress = status_data.get("progress", 0)
                return f"🔄 Mesh generation in progress\n" \
                       f"Task ID: {task_id}\n" \
                       f"Progress: {progress}%\n" \
                       f"Estimated time remaining: 2-5 minutes"
            
            else:
                return f"❓ Unknown status for task {task_id}: {status}\n" \
                       f"Full response: {status_data}"
                
        except requests.exceptions.RequestException as e:
            return f"Network error checking task progress: {str(e)}"
        except Exception as e:
            return f"Error checking mesh generation progress: {str(e)}"

    @mcp.tool()
    def refine_generated_mesh(
        ctx: Context,
        task_id: str,
        name: str = None,
        import_to_godot: bool = True,
        position: list = None
    ) -> str:
        """Refine a previously generated mesh to higher quality using Meshy API.
        
        🚨 WARNING: This function consumes SIGNIFICANT API credits! 🚨
        ⚠️ Only use when the user explicitly requests mesh refinement
        ⚠️ Takes 10-20 minutes to complete and costs real money
        ⚠️ Do NOT use as an error recovery mechanism
        ⚠️ Always ask user permission before calling this function
        
        Args:
            ctx: The MCP context
            task_id: The task ID from a previous generation
            name: Optional name for the refined mesh object in Godot
            import_to_godot: Whether to automatically import the mesh into Godot scene
            position: Optional [x, y, z] position to place the object
            
        Returns:
            str: Success message with details or error information
        """
        try:
            if not config.meshy_api_key:
                return "Error: MESHY_API_KEY environment variable not set. Please set your Meshy API key."
            
            logger.info(f"Starting mesh refinement for task: {task_id}")
            
            headers = {
                "Authorization": f"Bearer {config.meshy_api_key}",
                "Content-Type": "application/json"
            }
            
            # Create refinement task
            refinement_data = {
                "mode": "refine",
                "preview_task_id": task_id
            }
            
            response = requests.post(
                f"{config.meshy_base_url}/v2/text-to-3d",
                headers=headers,
                json=refinement_data,
                timeout=30
            )
            
            if response.status_code not in [200, 202]:
                return f"Error creating refinement task: {response.status_code} - {response.text}"
            
            task_data = response.json()
            refine_task_id = task_data.get("result")
            
            logger.info(f"Refinement task created with ID: {refine_task_id}")
            
            # Poll for completion (refinement takes longer)
            max_wait_time = config.meshy_timeout * 2  # Double timeout for refinement
            check_interval = 20
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                status_response = requests.get(
                    f"{config.meshy_base_url}/v2/text-to-3d/{refine_task_id}",
                    headers=headers,
                    timeout=30
                )
                
                if status_response.status_code != 200:
                    return f"Error checking refinement status: {status_response.status_code} - {status_response.text}"
                
                status_data = status_response.json()
                status = status_data.get("status")
                
                logger.info(f"Refinement status: {status}")
                
                if status == "SUCCEEDED":
                    model_urls = status_data.get("model_urls", {})
                    download_url = model_urls.get("glb") or model_urls.get("fbx") or model_urls.get("obj")
                    
                    if not download_url:
                        return f"No supported format in refined mesh. Available: {list(model_urls.keys())}"
                    
                    logger.info(f"Mesh refinement completed! Download URL: {download_url}")
                    
                    result_message = f"Mesh refined successfully! Download URL: {download_url}"
                    
                    if import_to_godot:
                        download_result = _download_mesh_to_project(download_url, name)
                        return f"{result_message}\n\n{download_result}"
                    else:
                        result = f"Mesh refined successfully! Download URL: {download_url}\n\n"
                        result += f"**Refinement Task ID:** {refine_task_id}\n"
                        result += f"**Note:** The refined mesh was NOT imported to Godot.\n\n"
                        result += f"To import it, use one of these options:\n"
                        result += f"1. Run: `import_asset` with source URL and target path\n"
                        result += f"2. Download manually and import\n"
                        result += f"3. Re-run refinement with `import_to_godot: true`"
                        return result
                
                elif status == "FAILED":
                    error_msg = status_data.get("task_error", {}).get("message", "Unknown error")
                    return f"Mesh refinement failed: {error_msg}"
                
                elif status in ["PENDING", "IN_PROGRESS"]:
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                else:
                    return f"Unknown refinement status: {status}"
            
            return f"Mesh refinement timeout after {max_wait_time} seconds"
            
        except Exception as e:
            return f"Error refining mesh: {str(e)}"

    @mcp.tool()
    def download_and_import_mesh(
        ctx: Context,
        download_url: str,
        name: str,
        position: list = None
    ) -> str:
        """Download a mesh from a URL (e.g., from Meshy API) and import it into Godot.
        
        Use this when you have a mesh URL but haven't imported it to Godot yet.
        
        Args:
            ctx: The MCP context
            download_url: The URL to download the mesh from
            name: Name for the mesh in Godot
            position: Optional [x, y, z] position to place the object
            
        Returns:
            str: Success message or error information
        """
        try:
            logger.info(f"Downloading mesh from URL: {name}")
            # First download the mesh
            download_result = _download_mesh_to_project(download_url, name)
            
            if "Error" in download_result:
                return download_result
            
            # Extract the file path from the download result
            import re
            match = re.search(r'`(res://[^`]+)`', download_result)
            if match:
                file_path = match.group(1)
                # Now import it using import_3d_model
                from .asset_tools import import_3d_model
                import_result = import_3d_model(
                    ctx=ctx,
                    model_path=file_path,
                    name=name,
                    position_x=position[0] if position else 0,
                    position_y=position[1] if position else 0,
                    position_z=position[2] if position else 0
                )
                return f"{download_result}\n\n{import_result}"
            else:
                return f"{download_result}\n\nNote: Could not automatically import. Use import_3d_model manually."
        except Exception as e:
            return f"Error downloading and importing mesh: {str(e)}"

def _download_mesh_to_project(download_url: str, name: str = None) -> str:
    """Helper function to download a mesh file to the Godot project."""
    try:
        # Generate a filename
        if not name:
            name = f"GeneratedMesh_{int(time.time())}"
        
        # Clean the name for filename use
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        
        # Determine file extension from URL
        url_lower = download_url.lower()
        if '.glb' in url_lower:
            extension = '.glb'
        elif '.fbx' in url_lower:
            extension = '.fbx'
        elif '.obj' in url_lower:
            extension = '.obj'
        else:
            extension = '.glb'  # Default
        
        filename = f"{safe_name}{extension}"
        local_path = f"/tmp/{filename}"
        
        logger.info(f"Downloading mesh to: {local_path}")
        
        # Download the file
        urllib.request.urlretrieve(download_url, local_path)
        
        # Import to Godot
        target_path = f"{config.asset_import_path}{filename}"
        
        godot = get_godot_connection()
        
        # First, ensure the target directory exists by creating a dummy file
        # This is necessary because Godot needs the directory to exist before importing
        logger.info(f"Ensuring directory exists: {config.asset_import_path}")
        
        # Check if the asset directory exists, create it if not
        check_dir_result = godot.send_command("GET_ASSET_LIST", {
            "folder": config.asset_import_path
        })
        
        if "error" in check_dir_result and "Unable to access directory" in check_dir_result.get("error", ""):
            # Directory doesn't exist, we need to create it
            # Create a dummy file to force directory creation
            dummy_path = f"{config.asset_import_path}.gdignore"
            dummy_result = godot.send_command("CREATE_SCRIPT", {
                "script_name": ".gdignore",
                "script_folder": config.asset_import_path.rstrip("/"),
                "content": "# This file tells Godot to ignore this directory for scanning",
                "overwrite": True
            })
            logger.info(f"Created directory with .gdignore: {dummy_result}")
        
        # Now import the asset
        import_result = godot.send_command("IMPORT_ASSET", {
            "source_path": local_path,
            "target_path": target_path,
            "overwrite": True
        })
        
        if "error" in import_result:
            return f"Error: Failed to copy file to Godot project: {import_result['error']}"
        
        # Clean up temporary file
        try:
            os.remove(local_path)
        except:
            pass
        
        success_msg = f"✅ **Mesh Downloaded Successfully!**\n\n"
        success_msg += f"**File:** `{target_path}`\n"
        success_msg += f"**Name:** {name}\n\n"
        success_msg += f"The mesh has been downloaded to your project.\n"
        success_msg += f"Use `import_3d_model` to add it to your scene."
        
        return success_msg
        
    except Exception as e:
        return f"Error importing mesh to Godot: {str(e)}" 