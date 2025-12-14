# Manually created migration to add new unique constraint

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0006_merge_duplicate_threads"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="thread",
            constraint=models.UniqueConstraint(
                fields=("user_a", "user_b"), name="unique_thread_per_user_pair"
            ),
        ),
    ]
