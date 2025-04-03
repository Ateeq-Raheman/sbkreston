import frappe

def on_trash(doc, method):
    # Only run logic if this is a parent task
    if not doc.is_group:
        frappe.logger().info(f"Skipping dependency cleanup for non-group task: {doc.name}")
        return

    frappe.logger().info(f"🧹 Deleting parent task: {doc.name}")

    # Step 1: Remove this task from other Task's depends_on
    dependencies = frappe.get_all(
        "Task Dependency",
        filters={"task": doc.name},
        fields=["name", "parent"]
    )

    for dep in dependencies:
        parent_task = frappe.get_doc("Task", dep.parent)
        parent_task.depends_on = [
            d for d in parent_task.depends_on if d.task != doc.name
        ]
        parent_task.save(ignore_permissions=True)

    # Step 2: Clear this task's own depends_on
    doc.set("depends_on", [])
    doc.save(ignore_permissions=True)

    # Step 3: Delete all child tasks recursively
    child_tasks = frappe.get_all("Task", filters={"parent_task": doc.name}, pluck="name")

    for child_name in child_tasks:
        try:
            frappe.delete_doc("Task", child_name, force=1)
            frappe.logger().info(f"🗑️ Deleted child task: {child_name}")
        except Exception as e:
            frappe.logger().error(f"❌ Could not delete child task {child_name}: {str(e)}")

    frappe.logger().info(f"✅ Completed deletion of parent task: {doc.name}")
