import frappe

def on_trash(doc, method):
    """
    This method is triggered automatically before a Task is deleted,
    including when using the standard frappe.client.delete API.

    It only runs if the Task is a parent (is_group == 1):
    - Removes it from other tasks' depends_on field
    - Clears its own depends_on
    - Recursively deletes all child tasks (linked by parent_task)
    """

    if not doc.is_group:
        frappe.logger().info(f"🟡 Skipping child deletion for non-group task: {doc.name}")
        return

    frappe.logger().info(f"🧹 Deleting parent task: {doc.name}")

    # Step 1: Remove this task from other tasks' depends_on fields
    dependencies = frappe.get_all(
        "Task Dependency",
        filters={"task": doc.name},
        fields=["name", "parent"]
    )

    for dep in dependencies:
        try:
            parent_task = frappe.get_doc("Task", dep.parent)
            parent_task.depends_on = [
                d for d in parent_task.depends_on if d.task != doc.name
            ]
            parent_task.save(ignore_permissions=True)
            frappe.logger().info(f"🔗 Removed dependency from {parent_task.name}")
        except Exception as e:
            frappe.logger().error(f"❌ Error updating parent task {dep.parent}: {str(e)}")

    # Step 2: Clear this task's own depends_on
    try:
        doc.set("depends_on", [])
        doc.save(ignore_permissions=True)
        frappe.logger().info(f"✅ Cleared own dependencies for {doc.name}")
    except Exception as e:
        frappe.logger().error(f"❌ Error clearing depends_on for {doc.name}: {str(e)}")

    # Step 3: Delete all child tasks recursively
    child_tasks = frappe.get_all("Task", filters={"parent_task": doc.name}, pluck="name")

    for child_name in child_tasks:
        try:
            frappe.delete_doc("Task", child_name, force=1)
            frappe.logger().info(f"🗑️ Deleted child task: {child_name}")
        except Exception as e:
            frappe.logger().error(f"❌ Could not delete child task {child_name}: {str(e)}")

    frappe.logger().info(f"✅ Completed cleanup for parent task: {doc.name}")
