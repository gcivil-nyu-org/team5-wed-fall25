# Manually created migration to remove old constraints

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0004_thread_unique_thread_per_roommate_pair"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="thread",
            name="unique_thread_per_listing_pair",
        ),
        migrations.RemoveConstraint(
            model_name="thread",
            name="unique_thread_per_item_pair",
        ),
        migrations.RemoveConstraint(
            model_name="thread",
            name="unique_thread_per_roommate_pair",
        ),
    ]
