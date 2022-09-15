from typing import List
from app.crud.base import CRUDBase

from app.models.projects import Projects
from app.schemas.designation_tools import DesignationTools as DesignationToolsSchema
from app.models.designation_tools import DesignationTools
from app.schemas.projects import ProjectCreate, ProjectToolsAssignment, ProjectUpdate
from app.schemas.projects import Projects as ProjectSchema
from sqlalchemy.orm import Session

from app.models.tools import Tools


class CRUDTools(CRUDBase[Projects, ProjectCreate, ProjectUpdate]):
    ...
    def get_assigned_tools(self, db: Session, id: int):
        p_obj: ProjectSchema = db.query(Projects).filter(Projects.id == id).first()
        return p_obj

    def assign_tools(self, db: Session, obj_in: ProjectToolsAssignment, project_id: int):
        tools_obj = db.query(Tools).filter(Tools.id == obj_in.tool_id).first()
        project_obj: ProjectSchema = db.query(Projects).filter(Projects.id == project_id).first()
        project_obj.tools.append(tools_obj)
        db.add_all([project_obj])
        db.commit()
        db.refresh(project_obj)
        return project_obj

    def delete_assigned_tools(self, db: Session, obj_in: ProjectToolsAssignment, project_id: int):
        tools_obj = db.query(Tools).filter(Tools.id == obj_in.tool_id).first()
        project_obj: ProjectSchema = db.query(Projects).filter(Projects.id == project_id).first()
        project_obj.tools.remove(tools_obj)
        db.add_all([project_obj])
        db.commit()
        db.refresh(project_obj)
        return project_obj

    def assign_desn_tools(self, db: Session, obj_in: List[DesignationToolsSchema] , project_id: int):
        desgn_tools_obj = []
        desn_id = obj_in[0].designation_id
        db.execute(f"delete from public.designationtools where project_id={project_id} and designation_id={desn_id}")
        db.commit()
        for desgn_tool in obj_in:
            desgn_tool_model = DesignationTools(**desgn_tool.dict())
            desgn_tools_obj.append(desgn_tool_model)
        db.bulk_save_objects(desgn_tools_obj)
        db.commit()
        return desgn_tools_obj
    
    def get_desn_tools(self, db: Session, project_id, designation_id):
        desgn_tools_obj = []
        selcted_desgn_tools_obj = db.execute(f"Select dt.tool_id, tool.display_name tool_name \
                        from public.designationtools dt \
                        inner join public.tools tool on dt.tool_id=tool.id \
                        where dt.project_id={project_id} and dt.designation_id={designation_id} ;").mappings().all()

        all_project_tools = db.execute(f"Select pt.tool_id, tool.display_name tool_name \
                        from public.projects_tools pt  \
                        inner join public.tools tool on pt.tool_id=tool.id \
                        where pt.project_id={project_id}").mappings().all()
        
        not_selcted_desgn_tools = dict(set(all_project_tools) - set(selcted_desgn_tools_obj))
        final_dict = {
            "selcted_desgn_tools_obj": selcted_desgn_tools_obj,
            "all_tools": all_project_tools
        }
        return final_dict

    def get_all_desn_tools(self, db: Session, project_id):
        desgn_tools_obj = []
        desgn_tools_obj = db.execute(f"Select prj.display_name prjname, d.display_name desn_name, tool.display_name tool_name \
                        from public.designationtools dt \
                        inner join public.projects prj on dt.project_id=prj.id \
                        inner join public.designations d on dt.designation_id=d.id \
                        inner join public.tools tool on dt.tool_id=tool.id \
                        where dt.project_id={project_id};").mappings().all()
        return desgn_tools_obj

    def get_not_associated_tools(self, db: Session, id: int):
        tools_obj = db.query(Tools).join(Tools, Projects.tools).filter(Projects.id == id).all()
        tools_obj_not_associated = db.query(Tools).all()
        for tool in tools_obj:
            tools_obj_not_associated.remove(tool)
        return tools_obj_not_associated


projects = CRUDTools(Projects)
