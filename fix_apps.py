import os

base_dir = 'apps'
for app_name in os.listdir(base_dir):
    app_path = os.path.join(base_dir, app_name)
    apps_py = os.path.join(app_path, 'apps.py')
    if os.path.exists(apps_py):
        try:
            with open(apps_py, 'r') as f:
                content = f.read()
            
            # Simple replace logic
            old_line = f"name = '{app_name}'"
            new_line = f"name = 'apps.{app_name}'"
            
            if old_line in content:
                new_content = content.replace(old_line, new_line)
                with open(apps_py, 'w') as f:
                    f.write(new_content)
                print(f"Fixed {apps_py}")
            elif f"name = 'apps.{app_name}'" in content:
                print(f"Already fixed {apps_py}")
            else:
                print(f"Skipped {apps_py} (pattern '{old_line}' not found)")
                # printing content for debug
                # print(content) 
        except Exception as e:
            print(f"Error processing {apps_py}: {e}")
