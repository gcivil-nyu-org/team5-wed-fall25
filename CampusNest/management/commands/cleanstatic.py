from django.core.management.base import BaseCommand
from django.conf import settings
import shutil
import os


class Command(BaseCommand):
    help = "Delete all collected static files and clean Python cache files for a clean development environment"

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Clean static files, .pyc files, and __pycache__ directories",
        )
        parser.add_argument(
            "--pyc-only",
            action="store_true",
            help="Only clean .pyc files and __pycache__ directories",
        )
        parser.add_argument(
            "--no-confirm",
            action="store_true",
            help="Skip confirmation prompt",
        )

    def handle(self, *args, **options):
        all_clean = options["all"]
        pyc_only = options["pyc_only"]
        no_confirm = options["no_confirm"]

        if pyc_only:
            self._clean_python_cache()
            return

        # Determine what to clean
        clean_static = True
        clean_pyc = all_clean

        # Show what will be cleaned
        self.stdout.write(self.style.WARNING("\n=== Clean Static Files ===\n"))

        if clean_static:
            static_root = settings.STATIC_ROOT
            self.stdout.write(f"Will remove: {static_root}")

        if clean_pyc:
            self.stdout.write("Will remove: All .pyc files and __pycache__ directories")

        # Confirm unless --no-confirm flag is used
        if not no_confirm:
            self.stdout.write(
                self.style.WARNING(
                    "\nThis will delete the files/directories listed above."
                )
            )
            confirm = input("Are you sure you want to continue? [y/N]: ")
            if confirm.lower() != "y":
                self.stdout.write(self.style.ERROR("Aborted."))
                return

        # Clean static files
        if clean_static:
            self._clean_static_files()

        # Clean Python cache if --all flag is used
        if clean_pyc:
            self._clean_python_cache()

        self.stdout.write(self.style.SUCCESS("\n✓ Cleanup completed successfully!\n"))

    def _clean_static_files(self):
        """Remove the staticfiles directory"""
        static_root = settings.STATIC_ROOT

        if os.path.exists(static_root):
            try:
                shutil.rmtree(static_root)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Removed staticfiles directory: {static_root}"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Error removing staticfiles: {e}")
                )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠ Staticfiles directory does not exist: {static_root}"
                )
            )

    def _should_skip_directory(self, root):
        """Check if directory should be skipped during cleanup"""
        return ".venv" in root or "node_modules" in root

    def _remove_pyc_files(self, root, files):
        """Remove .pyc files in the given directory"""
        count = 0
        for file in files:
            if file.endswith(".pyc"):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"✗ Error removing {file_path}: {e}")
                    )
        return count

    def _remove_pycache_dirs(self, root, dirs):
        """Remove __pycache__ directories in the given directory"""
        count = 0
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(pycache_path)
                count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Error removing {pycache_path}: {e}")
                )
        return count

    def _clean_python_cache(self):
        """Remove .pyc files and __pycache__ directories"""
        base_dir = settings.BASE_DIR
        pyc_count = 0
        pycache_count = 0

        # Walk through the project directory
        for root, dirs, files in os.walk(base_dir):
            if self._should_skip_directory(root):
                continue

            pyc_count += self._remove_pyc_files(root, files)
            pycache_count += self._remove_pycache_dirs(root, dirs)

        # Display results
        if pyc_count > 0 or pycache_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Removed {pyc_count} .pyc files and {pycache_count} __pycache__ directories"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING("⚠ No .pyc files or __pycache__ directories found")
            )
