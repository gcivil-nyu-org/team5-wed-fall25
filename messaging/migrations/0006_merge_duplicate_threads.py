# Manually created migration to merge duplicate threads

from django.db import migrations


def merge_duplicate_threads(apps, schema_editor):
    """
    Merge duplicate threads for the same user pairs.
    Keep the oldest thread and move all messages from duplicates to it.
    """
    Thread = apps.get_model("messaging", "Thread")
    Message = apps.get_model("messaging", "Message")

    # Get all threads ordered by user_a, user_b, created_at
    all_threads = Thread.objects.all().order_by("user_a", "user_b", "created_at")

    # Group threads by user pair
    user_pairs = {}
    for thread in all_threads:
        key = (thread.user_a_id, thread.user_b_id)
        if key not in user_pairs:
            user_pairs[key] = []
        user_pairs[key].append(thread)

    # Merge duplicates
    merged_count = 0
    for key, threads in user_pairs.items():
        if len(threads) > 1:
            # Keep the first (oldest) thread
            primary_thread = threads[0]
            duplicate_threads = threads[1:]

            print(
                f"Merging {len(duplicate_threads)} duplicate thread(s) for user pair {key}"
            )

            # Move all messages from duplicates to primary thread
            for dup_thread in duplicate_threads:
                msg_count = Message.objects.filter(thread=dup_thread).update(
                    thread=primary_thread
                )
                print(
                    f"  Moved {msg_count} messages from thread {dup_thread.id} to {primary_thread.id}"
                )
                # Delete the duplicate thread
                dup_thread.delete()
                merged_count += 1

            # Update the primary thread's updated_at to reflect latest activity
            latest_message = (
                Message.objects.filter(thread=primary_thread)
                .order_by("-created_at")
                .first()
            )
            if latest_message:
                primary_thread.updated_at = latest_message.created_at
                primary_thread.save(update_fields=["updated_at"])

    print(f"Total: Merged {merged_count} duplicate thread(s)")


def reverse_merge(apps, schema_editor):
    """
    Cannot reverse this migration as it involves data loss.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0005_remove_old_constraints"),
    ]

    operations = [
        migrations.RunPython(merge_duplicate_threads, reverse_merge),
    ]
