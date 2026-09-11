#!/usr/bin/env python3
"""
install_roommates.py

Automatic installer for the "Find Roommate" Django app into an existing
UrbanTenants project.

WHAT THIS SCRIPT DOES AUTOMATICALLY:
  1. Copies the roommates/ app folder into your project root.
  2. Adds "roommates" to INSTALLED_APPS in settings.py.
  3. Adds `path("roommates/", include("roommates.urls"))` to your main urls.py.
  4. Scans your whole project for a function named `cashfree_create_order`
     (and `cashfree_get_order_status` / similar) and rewrites the import
     lines inside roommates/views.py to point at the real module.
  5. Scans your templates for a navbar-like file (contains "Rooms" or "PGs"
     as visible text) and inserts a "Find Roommate" link automatically.
  6. Runs `makemigrations roommates` and `migrate`.

Every file this script touches is backed up first as `<file>.bak`.
Nothing is deleted. If a step can't be done safely/automatically, the
script prints exactly what you need to do by hand instead of guessing.

USAGE:
    1. Put this script and the `roommates/` folder in the SAME directory.
    2. Run:
           python install_roommates.py /path/to/your/django/project

       (The path should be the folder that directly contains manage.py.)
"""

import os
import re
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_SOURCE = os.path.join(SCRIPT_DIR, "roommates")


def fail(msg):
    print(f"\n❌ {msg}")
    sys.exit(1)


def ok(msg):
    print(f"✅ {msg}")


def warn(msg):
    print(f"⚠️  {msg}")


def backup(path):
    if os.path.exists(path) and not os.path.exists(path + ".bak"):
        shutil.copy2(path, path + ".bak")


def find_manage_py(project_root):
    manage_py = os.path.join(project_root, "manage.py")
    if not os.path.exists(manage_py):
        fail(f"manage.py not found at {manage_py}. Pass the folder that directly contains manage.py.")
    return manage_py


def find_settings_file(project_root):
    """
    Finds settings.py by reading manage.py's DJANGO_SETTINGS_MODULE,
    falling back to a project-wide search.
    """
    manage_py = find_manage_py(project_root)
    with open(manage_py, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r"DJANGO_SETTINGS_MODULE['\"]?\s*,\s*['\"]([\w\.]+)['\"]", content)
    if match:
        dotted = match.group(1)
        rel_path = dotted.replace(".", os.sep) + ".py"
        candidate = os.path.join(project_root, rel_path)
        if os.path.exists(candidate):
            return candidate

    # fallback: search for any settings.py under project_root
    for root, dirs, files in os.walk(project_root):
        if "settings.py" in files:
            return os.path.join(root, "settings.py")

    fail("Could not locate settings.py automatically. Please add \"roommates\" to "
         "INSTALLED_APPS manually.")


def find_root_urls_file(project_root):
    """
    Finds the project-level urls.py (the one whose folder also has settings.py /
    wsgi.py — i.e. the Django project package, not an app's urls.py).
    """
    settings_file = find_settings_file(project_root)
    project_pkg_dir = os.path.dirname(settings_file)
    candidate = os.path.join(project_pkg_dir, "urls.py")
    if os.path.exists(candidate):
        return candidate

    fail(f"Could not find urls.py next to settings.py at {project_pkg_dir}. "
         "Please add the roommates URL include manually.")


def step_copy_app(project_root):
    print("\n--- Step 1: Copying roommates/ app ---")
    if not os.path.isdir(APP_SOURCE):
        fail(f"Could not find source folder at {APP_SOURCE}. "
             "Make sure roommates/ sits next to this script.")

    dest = os.path.join(project_root, "roommates")
    if os.path.exists(dest):
        warn(f"{dest} already exists — skipping copy so nothing gets overwritten. "
             "Delete it first if you want a clean re-copy.")
        return

    shutil.copytree(APP_SOURCE, dest)
    ok(f"Copied roommates/ app to {dest}")


def step_patch_installed_apps(project_root):
    print("\n--- Step 2: Patching INSTALLED_APPS in settings.py ---")
    settings_file = find_settings_file(project_root)

    with open(settings_file, "r", encoding="utf-8") as f:
        content = f.read()

    if re.search(r"""INSTALLED_APPS\s*=.*?["']roommates["']""", content, re.DOTALL):
        ok("\"roommates\" is already in INSTALLED_APPS — nothing to do.")
        return

    match = re.search(r"(INSTALLED_APPS\s*=\s*\[)(.*?)(\n\])", content, re.DOTALL)
    if not match:
        warn(f"Could not automatically locate INSTALLED_APPS in {settings_file}. "
             "Please add \"roommates\" to it manually.")
        return

    backup(settings_file)
    new_content = (
        content[:match.end(2)]
        + '\n    "roommates",'
        + content[match.end(2):]
    )
    with open(settings_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    ok(f"Added \"roommates\" to INSTALLED_APPS in {settings_file} (backup saved as .bak)")


def step_patch_root_urls(project_root):
    print("\n--- Step 3: Patching project urls.py ---")
    urls_file = find_root_urls_file(project_root)

    with open(urls_file, "r", encoding="utf-8") as f:
        content = f.read()

    if 'include("roommates.urls")' in content or "include('roommates.urls')" in content:
        ok("roommates.urls is already included — nothing to do.")
        return

    backup(urls_file)

    # Ensure `include` is imported
    if "from django.urls import" in content and "include" not in content.split("from django.urls import", 1)[1].split("\n")[0]:
        content = re.sub(
            r"from django\.urls import ([^\n]+)",
            lambda m: f"from django.urls import {m.group(1).rstrip()}, include"
            if "include" not in m.group(1) else m.group(0),
            content,
            count=1,
        )
    elif "from django.urls import" not in content:
        content = "from django.urls import include, path\n" + content

    match = re.search(r"(urlpatterns\s*=\s*\[)(.*?)(\n\])", content, re.DOTALL)
    if not match:
        warn(f"Could not automatically locate urlpatterns in {urls_file}. "
             "Please add: path(\"roommates/\", include(\"roommates.urls\")) manually.")
        return

    new_content = (
        content[:match.end(2)]
        + '\n    path("roommates/", include("roommates.urls")),'
        + content[match.end(2):]
    )
    with open(urls_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    ok(f"Added roommates.urls include to {urls_file} (backup saved as .bak)")


def step_patch_cashfree_imports(project_root):
    print("\n--- Step 4: Auto-detecting your Cashfree helper functions ---")

    targets = {
        "cashfree_create_order": None,
        "cashfree_get_order_status": None,
    }

    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in ("migrations", "__pycache__", ".git", "roommates")]
        for filename in files:
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
            except (UnicodeDecodeError, PermissionError):
                continue

            for func_name in targets:
                if targets[func_name] is None and re.search(rf"def\s+{func_name}\s*\(", text):
                    rel = os.path.relpath(filepath, project_root)
                    dotted_module = rel[:-3].replace(os.sep, ".")  # strip .py, dotify
                    targets[func_name] = dotted_module

    views_path = os.path.join(project_root, "roommates", "views.py")
    if not os.path.exists(views_path):
        warn("roommates/views.py not found (did Step 1 run?). Skipping this step.")
        return

    with open(views_path, "r", encoding="utf-8") as f:
        views_content = f.read()

    changed = False

    if targets["cashfree_create_order"]:
        module = targets["cashfree_create_order"]
        views_content = views_content.replace(
            "from rooms.payments import cashfree_create_order  # <-- CHANGE THIS IMPORT",
            f"from {module} import cashfree_create_order",
        )
        ok(f"Found cashfree_create_order() in {module} — import wired automatically.")
        changed = True
    else:
        warn("Could not find a function named cashfree_create_order() anywhere in your "
             "project. You'll need to edit the import in roommates/views.py by hand "
             "(search for 'CHANGE THIS IMPORT').")

    if targets["cashfree_get_order_status"]:
        module = targets["cashfree_get_order_status"]
        views_content = views_content.replace(
            "from rooms.payments import cashfree_get_order_status  # <-- CHANGE THIS IMPORT",
            f"from {module} import cashfree_get_order_status",
        )
        ok(f"Found cashfree_get_order_status() in {module} — import wired automatically.")
        changed = True
    else:
        warn("Could not find a function named cashfree_get_order_status() anywhere in "
             "your project. The chat-unlock payment-verification step will need you to "
             "wire in however your project actually checks Cashfree order status "
             "(search roommates/views.py for 'CHANGE THIS IMPORT').")

    if changed:
        backup(views_path)
        with open(views_path, "w", encoding="utf-8") as f:
            f.write(views_content)


def step_patch_navbar(project_root):
    print("\n--- Step 5: Auto-detecting your navbar to add \"Find Roommate\" ---")

    candidates = []
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in ("migrations", "__pycache__", ".git", "roommates")]
        for filename in files:
            if filename.endswith(".html") and any(
                keyword in filename.lower() for keyword in ("header", "navbar", "nav")
            ):
                candidates.append(os.path.join(root, filename))

    if not candidates:
        warn("Could not find a header/navbar HTML file automatically. "
             "Please add this link to your navbar manually:\n"
             '    <a href="{% url \'roommates:roommate-list\' %}">Find Roommate</a>')
        return

    target_file = None
    for path in candidates:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        if re.search(r">\s*Rooms\s*<", text) or re.search(r">\s*PGs?\s*<", text) or re.search(r">\s*Flats\s*<", text):
            target_file = path
            content = text
            break

    if not target_file:
        warn(f"Found possible navbar files ({', '.join(os.path.relpath(p, project_root) for p in candidates)}) "
             "but couldn't confirm which one has your nav links. Please add manually:\n"
             '    <a href="{% url \'roommates:roommate-list\' %}">Find Roommate</a>')
        return

    if "roommate-list" in content or "Find Roommate" in content:
        ok(f"{os.path.relpath(target_file, project_root)} already has a Find Roommate link — nothing to do.")
        return

    backup(target_file)

    nav_link = '<a href="{% url \'roommates:roommate-list\' %}">Find Roommate</a>\n'

    # Insert right after the last matching nav link (Rooms/PGs/Flats), so it
    # visually sits in the same list.
    match = list(re.finditer(r"<a\b[^>]*>\s*(Rooms|PGs?|Flats)\s*</a>", content))
    if match:
        insert_at = match[-1].end()
        new_content = content[:insert_at] + "\n    " + nav_link.strip() + content[insert_at:]
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        ok(f"Inserted \"Find Roommate\" link into {os.path.relpath(target_file, project_root)} "
           "(backup saved as .bak). Please double check the placement/styling.")
    else:
        warn(f"Found {os.path.relpath(target_file, project_root)} but couldn't safely locate "
             "where to insert the link. Please add manually:\n"
             '    <a href="{% url \'roommates:roommate-list\' %}">Find Roommate</a>')


def step_run_migrations(project_root):
    print("\n--- Step 6: Running migrations ---")
    manage_py = find_manage_py(project_root)
    python_exe = sys.executable

    try:
        subprocess.run(
            [python_exe, manage_py, "makemigrations", "roommates"],
            cwd=project_root, check=True,
        )
        subprocess.run(
            [python_exe, manage_py, "migrate"],
            cwd=project_root, check=True,
        )
        ok("Migrations created and applied.")
    except subprocess.CalledProcessError as e:
        warn(f"Migration command failed ({e}). Run these manually once other issues "
             f"above are fixed:\n    python manage.py makemigrations roommates\n"
             f"    python manage.py migrate")
    except FileNotFoundError:
        warn("Could not run migrations automatically (python/manage.py not found in "
             "this environment). Run manually:\n"
             "    python manage.py makemigrations roommates\n"
             "    python manage.py migrate")


def main():
    if len(sys.argv) != 2:
        print("Usage: python install_roommates.py /path/to/your/django/project")
        sys.exit(1)

    project_root = os.path.abspath(sys.argv[1])
    if not os.path.isdir(project_root):
        fail(f"{project_root} is not a valid directory.")

    print(f"Installing Find Roommate into: {project_root}")

    step_copy_app(project_root)
    step_patch_installed_apps(project_root)
    step_patch_root_urls(project_root)
    step_patch_cashfree_imports(project_root)
    step_patch_navbar(project_root)
    step_run_migrations(project_root)

    print("\n============================================================")
    print("DONE. Review any ⚠️  warnings above — those need a manual touch.")
    print("Everything else should now be wired up automatically.")
    print("Backups of every file this script edited were saved as <file>.bak")
    print("============================================================")


if __name__ == "__main__":
    main()
