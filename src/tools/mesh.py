"""Mesh tools for COMSOL MCP Server."""

from typing import Optional
from mcp.server.fastmcp import FastMCP

from .session import session_manager


def _java_tags(collection) -> list[str]:
    """Return Java node tags from a COMSOL collection."""
    tags = []
    try:
        for item in collection:
            tags.append(str(item.tag()))
    except Exception:
        pass
    return tags


def _java_node_label(node) -> str:
    """Return a Java node label, falling back to its tag."""
    try:
        return str(node.label())
    except Exception:
        try:
            return str(node.tag())
        except Exception:
            return ""


def _available_mesh_context(jm) -> dict:
    """Summarize available components, geometries, and meshes."""
    components = []
    for comp in jm.component():
        info = {
            "tag": str(comp.tag()),
            "label": _java_node_label(comp),
            "geometries": [],
            "meshes": [],
        }
        try:
            info["geometries"] = [
                {"tag": str(geom.tag()), "label": _java_node_label(geom)}
                for geom in comp.geom()
            ]
        except Exception:
            pass
        try:
            info["meshes"] = [
                {"tag": str(mesh.tag()), "label": _java_node_label(mesh)}
                for mesh in comp.mesh()
            ]
        except Exception:
            pass
        components.append(info)
    return {"components": components}


def register_mesh_tools(mcp: FastMCP) -> None:
    """Register mesh tools with the MCP server."""
    
    @mcp.tool()
    def mesh_list(model_name: Optional[str] = None) -> dict:
        """
        List all mesh sequences in a model.
        
        Args:
            model_name: Model name (default: current model)
        
        Returns:
            List of mesh sequence names
        """
        model = session_manager.get_model(model_name)
        if model is None:
            return {
                "success": False,
                "error": f"Model not found: {model_name or 'no current model'}"
            }
        
        try:
            meshes = model.meshes()
            return {
                "success": True,
                "meshes": meshes,
                "count": len(meshes),
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to list meshes: {str(e)}"}
    
    @mcp.tool()
    def mesh_create(
        mesh_name: str = "mesh1",
        component_name: str = "comp1",
        geometry_name: str = "geom1",
        auto_size: Optional[int] = None,
        model_name: Optional[str] = None
    ) -> dict:
        """
        Run a mesh sequence to generate the mesh.
        
        This executes the meshing operations defined in the mesh sequence.
        
        Args:
            mesh_name: Mesh sequence tag (default: mesh1)
            component_name: Component tag (default: comp1)
            geometry_name: Geometry tag (default: geom1)
            auto_size: Optional COMSOL automatic mesh size level
            model_name: Model name (default: current model)
        
        Returns:
            Mesh generation status
        """
        model = session_manager.get_model(model_name)
        if model is None:
            return {
                "success": False,
                "error": f"Model not found: {model_name or 'no current model'}"
            }
        
        try:
            jm = model.java
            component_tags = _java_tags(jm.component())
            if component_name not in component_tags:
                return {
                    "success": False,
                    "error": f"Component tag not found: {component_name}",
                    "available": _available_mesh_context(jm),
                }

            comp = jm.component(component_name)
            geometry_tags = _java_tags(comp.geom())
            if geometry_name not in geometry_tags:
                return {
                    "success": False,
                    "error": (
                        f"Geometry tag not found in component '{component_name}': "
                        f"{geometry_name}"
                    ),
                    "available": _available_mesh_context(jm),
                }

            mesh_tags = _java_tags(comp.mesh())
            if mesh_name in mesh_tags:
                mesh = comp.mesh(mesh_name)
                created = False
            else:
                mesh = comp.mesh().create(mesh_name, geometry_name)
                created = True

            if auto_size is not None:
                mesh.autoMeshSize(int(auto_size))

            mesh.run()
            return {
                "success": True,
                "model": model.name(),
                "component": str(comp.tag()),
                "geometry": geometry_name,
                "mesh": {
                    "tag": str(mesh.tag()),
                    "label": _java_node_label(mesh),
                    "created": created,
                    "auto_size": auto_size,
                },
                "message": f"Mesh generated: {mesh_name}",
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to create mesh: {str(e)}"}
    
    @mcp.tool()
    def mesh_info(
        mesh_name: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> dict:
        """
        Get information about a mesh.
        
        Args:
            mesh_name: Mesh sequence name (default: first mesh)
            model_name: Model name (default: current model)
        
        Returns:
            Mesh statistics including element counts
        """
        model = session_manager.get_model(model_name)
        if model is None:
            return {
                "success": False,
                "error": f"Model not found: {model_name or 'no current model'}"
            }
        
        try:
            meshes = model.meshes()
            if not meshes:
                return {"success": False, "error": "No meshes defined in model."}
            
            target = mesh_name or meshes[0]
            if target not in meshes:
                return {"success": False, "error": f"Mesh not found: {target}"}
            
            mesh_node = model / "meshes" / target
            
            info = {
                "name": target,
            }
            
            try:
                java_mesh = mesh_node.java
                if hasattr(java_mesh, 'getVertex'):
                    info["num_vertices"] = java_mesh.getVertex().size()
                if hasattr(java_mesh, 'getElement'):
                    info["num_elements"] = java_mesh.getElement().size()
            except Exception:
                pass
            
            try:
                children = [child.name() for child in mesh_node.children()]
                info["features"] = children
            except Exception:
                pass
            
            return {
                "success": True,
                "mesh": info,
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to get mesh info: {str(e)}"}
