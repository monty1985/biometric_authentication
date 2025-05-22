import sys
import pkg_resources
import importlib
import os

def check_package(package_name):
    try:
        module = importlib.import_module(package_name)
        version = pkg_resources.get_distribution(package_name).version
        return True, version
    except (ImportError, pkg_resources.DistributionNotFound):
        return False, None

def check_directory(path):
    return os.path.exists(path) and os.path.isdir(path)

required_packages = [
    'fastapi',
    'uvicorn',
    'python-multipart',
    'speechbrain',
    'torch',
    'numpy',
    'python-jose',
    'passlib',
    'pydantic',
    'python-dotenv',
    'faiss',
    'pydub',
    'librosa',
    'soundfile'
]

required_directories = [
    'app',
    'app/api',
    'app/api/v1',
    'app/api/v1/endpoints',
    'app/core',
    'app/models',
    'app/services',
    'tests',
    'data',
    'data/uploads',
    'data/embeddings',
    'pretrained_models'
]

print("Python Version:", sys.version)
print("\nChecking required packages:")
print("-" * 50)

all_packages_ok = True
for package in required_packages:
    installed, version = check_package(package)
    status = "✓" if installed else "✗"
    version_str = f" (v{version})" if version else ""
    print(f"{status} {package}{version_str}")
    if not installed:
        all_packages_ok = False

print("\nChecking required directories:")
print("-" * 50)

all_dirs_ok = True
for directory in required_directories:
    exists = check_directory(directory)
    status = "✓" if exists else "✗"
    print(f"{status} {directory}")
    if not exists:
        all_dirs_ok = False

print("\nSummary:")
print("-" * 50)
print(f"All packages installed: {'✓' if all_packages_ok else '✗'}")
print(f"All directories present: {'✓' if all_dirs_ok else '✗'}")

if not all_packages_ok or not all_dirs_ok:
    print("\nMissing components need to be installed or created.")
    if not all_packages_ok:
        print("\nTo install missing packages, run:")
        print("pip install -r requirements.txt")
    if not all_dirs_ok:
        print("\nTo create missing directories, run:")
        print("mkdir -p " + " ".join(d for d in required_directories if not check_directory(d))) 