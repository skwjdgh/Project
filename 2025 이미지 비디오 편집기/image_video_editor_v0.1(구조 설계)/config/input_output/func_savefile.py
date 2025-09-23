# config/input_output/func_savefile.py
def export_project_as_video(project, output_path: str, format: str = 'mp4'):
    print(f"Rendering project '{project.name}' to video file...")